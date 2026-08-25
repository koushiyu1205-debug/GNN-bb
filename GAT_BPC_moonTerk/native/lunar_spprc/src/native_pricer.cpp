#include "lunar_spprc/native_pricer.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <bit>
#include <bitset>
#include <chrono>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <list>
#include <map>
#include <memory>
#include <mutex>
#include <queue>
#include <numeric>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <variant>

#include "rcspp/rcspp.hpp"

namespace lunar_spprc {
namespace {

// Native v1 accepts at most 100 tasks, so the elementary visited set always
// fits in two machine words.  Keep it inline in every label: State is copied on
// each arc extension, and a heap-backed vector here would turn the hottest
// exact-search operation into an allocation/copy/deallocation cycle.
using VisitedMask = std::array<std::uint64_t, 2>;
constexpr std::size_t kMaxActiveCuts = 16;
constexpr const char* kDssrPolicyVersionV1 =
    "multi_sortie_counterexample_refinement_v1";
constexpr const char* kDssrPolicyVersionV2 =
    "multi_sortie_counterexample_pressure_refinement_v2";
constexpr const char* kNgDssrPolicyVersionV3 =
    "multi_sortie_ng_memory_counterexample_refinement_v3";
constexpr bool kNgDssrV3Compiled =
    LUNAR_SPPRC_ENABLE_NG_DSSR_V3 != 0;
constexpr bool kBidirectionalFeasibilityCompiled =
    LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY != 0;

bool ng_dssr_active(const Model& model) {
    if constexpr (kNgDssrV3Compiled) {
        return model.ng_dssr_memory_enabled;
    }
    return false;
}

bool is_dssr_v2(const SolveParams& params) {
    return params.dssr_enabled &&
           params.dssr_policy_version == kDssrPolicyVersionV2;
}

bool is_ng_dssr_v3(const SolveParams& params) {
    return params.dssr_enabled &&
           params.dssr_policy_version == kNgDssrPolicyVersionV3;
}

bool uses_dssr_batch(const SolveParams& params) {
    return is_dssr_v2(params) || is_ng_dssr_v3(params);
}

struct CutState {
    // Exact overlap values: SRI-3 uses 2 bits (0..3), SRI-5 uses 3 bits
    // (0..5).  Sixteen SRI-5 rows occupy only 48 of the 64 inline bits.
    std::uint64_t packed_overlap = 0;
};

bool same_active_cut_state(const CutState& lhs, const CutState& rhs) {
    return lhs.packed_overlap == rhs.packed_overlap;
}

std::uint64_t cut_state_value_mask(const CutDefinition& cut) {
    return (std::uint64_t{1} << cut.state_bit_width) - 1U;
}

std::uint8_t cut_overlap(const CutState& state, const CutDefinition& cut) {
    return static_cast<std::uint8_t>(
        (state.packed_overlap >> cut.state_bit_offset) &
        cut_state_value_mask(cut));
}

void set_cut_overlap(CutState* state, const CutDefinition& cut,
                     std::uint8_t overlap) {
    const auto value_mask = cut_state_value_mask(cut);
    const auto shifted_mask = value_mask << cut.state_bit_offset;
    state->packed_overlap =
        (state->packed_overlap & ~shifted_mask) |
        ((static_cast<std::uint64_t>(overlap) & value_mask)
         << cut.state_bit_offset);
}

struct Action {
    ActionKind kind = ActionKind::Terminate;
    std::size_t task_index = 0;
    std::size_t model_arc_index = std::numeric_limits<std::size_t>::max();
    std::string path_type;
    double travel_time = 0.0;
    double energy = 0.0;
    double risk = 0.0;
    double distance = 0.0;
    double shadow = 0.0;
};

union AuxiliaryState {
    struct Regular {
        double positive_task_dual_reward = 0.0;
        std::size_t last_model_arc_index =
            std::numeric_limits<std::size_t>::max();
    } regular;
    VisitedMask ng_memory;

    constexpr AuxiliaryState() : regular{} {}
};

static_assert(sizeof(AuxiliaryState) == sizeof(VisitedMask));

struct State {
    bool valid = true;
    bool at_depot = true;
    VisitedMask visited{};
    // Native accepts at most 100 tasks.  These counters therefore have a
    // proven upper bound of 100 (every sortie is nonempty), so size_t wasted
    // 30 bytes per label without representing any reachable state.
    std::uint16_t visited_count = 0;
    std::uint16_t task_visit_count = 0;
    std::uint16_t sortie_task_count = 0;
    std::uint16_t sortie_count = 0;
    std::uint16_t visited_at_sortie_start = 0;
    double global_time = 0.0;
    double sortie_start_time = 0.0;
    double sortie_latest_start_time = std::numeric_limits<double>::infinity();
    double sortie_science_weight = 0.0;
    double sortie_demand = 0.0;
    double sortie_energy = 0.0;
    double sortie_shadow = 0.0;
    double raw_operating_cost = 0.0;
    double raw_risk = 0.0;
    double raw_weighted_completion = 0.0;
    double task_dual_reward = 0.0;
    AuxiliaryState auxiliary;
    double cut_dual_reward = 0.0;
    double guidance_score = 0.0;
    std::size_t last_task_index = std::numeric_limits<std::size_t>::max();
    CutState cut_state;
};

static_assert(
    sizeof(State) == 176,
    "Native label State size changed; compact P0 state requires 176 bytes"
);

const VisitedMask& ng_memory(const State& state) {
    return state.auxiliary.ng_memory;
}

VisitedMask& ng_memory(State* state) {
    return state->auxiliary.ng_memory;
}

class JourneyValue {
  public:
    JourneyValue() : payload_(State{}) {}

    static JourneyValue from_state(State state) {
        return JourneyValue(std::move(state));
    }

    static JourneyValue from_action(Action action) {
        return JourneyValue(std::move(action));
    }

    [[nodiscard]] bool is_action() const {
        return std::holds_alternative<Action>(payload_);
    }

    [[nodiscard]] const State& state() const {
        return std::get<State>(payload_);
    }

    [[nodiscard]] const Action& action() const {
        return std::get<Action>(payload_);
    }

    void reset_state() { payload_.template emplace<State>(); }

  private:
    explicit JourneyValue(State state) : payload_(std::move(state)) {}
    explicit JourneyValue(Action action) : payload_(std::move(action)) {}

    // Labels and arc extenders use disjoint payloads.  The historical struct
    // stored both, forcing every live label to carry an unused Action and
    // std::string.  A tagged union preserves the exact value domains while
    // allocating space only for the active one.
    std::variant<State, Action> payload_;
};

static_assert(
    sizeof(JourneyValue) <= 184,
    "Compact native label payload unexpectedly grew"
);

class JourneyResource {
  public:
    JourneyResource() = default;
    explicit JourneyResource(JourneyValue value) : value_(std::move(value)) {}

    void reset() { value_.reset_state(); }
    [[nodiscard]] const JourneyValue& get_value() const { return value_; }
    void set_value(const JourneyValue& value) { value_ = value; }
    [[nodiscard]] std::string to_string() const {
        if (value_.is_action()) {
            return "action";
        }
        std::ostringstream stream;
        stream << "visited=" << value_.state().visited_count
               << ",time=" << value_.state().global_time;
        return stream.str();
    }

  private:
    JourneyValue value_;
};

double reduced_cost(const Model& model, const State& state) {
    return model.cost_coefficient * state.raw_operating_cost +
           model.risk_coefficient * state.raw_risk +
           model.completion_coefficient * state.raw_weighted_completion -
           state.task_dual_reward - model.fleet_dual - state.cut_dual_reward;
}

double finite_ratio(double numerator, double denominator) {
    const double scale = std::max(1.0e-12, std::abs(denominator));
    return numerator / scale;
}

double signed_log1p(double value) {
    return std::copysign(std::log1p(std::abs(value)), value);
}

std::array<double, kLabelStateFeatureCount> label_state_features(
    const Model& model,
    const State& state,
    double partial_reduced_cost
) {
    const double task_count = std::max(1.0, static_cast<double>(model.tasks.size()));
    const double max_trip = std::max(1.0, static_cast<double>(model.max_tasks_per_trip));
    const double positive_scale = std::max(1.0, model.positive_task_dual_sum);
    const double positive_reward =
        ng_dssr_active(model)
            ? 0.0
            : state.auxiliary.regular.positive_task_dual_reward;
    return {
        static_cast<double>(state.visited_count) / task_count,
        static_cast<double>(state.task_visit_count) / task_count,
        static_cast<double>(state.sortie_task_count) / max_trip,
        static_cast<double>(state.sortie_count) / task_count,
        state.at_depot ? 1.0 : 0.0,
        finite_ratio(state.global_time, model.horizon),
        finite_ratio(
            std::max(0.0, model.horizon - state.global_time),
            model.horizon),
        finite_ratio(state.sortie_demand, model.capacity),
        finite_ratio(state.sortie_energy, model.energy_limit),
        finite_ratio(state.sortie_shadow, model.shadow_limit),
        finite_ratio(state.task_dual_reward, model.absolute_dual_sum),
        finite_ratio(state.cut_dual_reward, model.absolute_dual_sum),
        positive_reward / positive_scale,
        std::max(0.0, model.positive_task_dual_sum - positive_reward) /
            positive_scale,
        signed_log1p(partial_reduced_cost),
    };
}

double qg2_label_state_priority(
    const Model& model,
    const State& state,
    double partial_reduced_cost
) {
    if (!model.guidance_label_state_enabled) {
        return 0.0;
    }
    const auto features = label_state_features(
        model, state, partial_reduced_cost);
    double score = state.guidance_score;
    if (
        !state.at_depot &&
        state.last_task_index < model.tasks.size()
    ) {
        score += model.tasks[state.last_task_index].guidance_priority;
    }
    for (std::size_t index = 0; index < features.size(); ++index) {
        score += model.guidance_label_state_coefficients[index] *
                 features[index];
    }
    return score;
}

double frontier_sigmoid(double value) {
    if (value >= 0.0) {
        const double z = std::exp(-value);
        return 1.0 / (1.0 + z);
    }
    const double z = std::exp(value);
    return z / (1.0 + z);
}

double frontier_calibrated_probability(
    double probability,
    const FrontierProbabilityCalibration& calibration
) {
    if (calibration.constant) {
        return calibration.probability;
    }
    const double bounded = std::clamp(probability, 1.0e-7, 1.0 - 1.0e-7);
    const double logit = std::log(bounded / (1.0 - bounded));
    return frontier_sigmoid(calibration.a * logit + calibration.b);
}

const FrontierDenseTensor& frontier_tensor(
    const FrontierGatSeedModel& model,
    const std::string& name,
    std::initializer_list<std::size_t> shape
) {
    const auto found = model.tensors.find(name);
    if (found == model.tensors.end()) {
        throw std::invalid_argument("frontier GAT tensor missing: " + name);
    }
    const std::vector<std::size_t> expected(shape);
    if (found->second.shape != expected) {
        throw std::invalid_argument("frontier GAT tensor shape mismatch: " + name);
    }
    const auto count = std::accumulate(
        expected.begin(), expected.end(), std::size_t{1},
        std::multiplies<>{});
    if (found->second.values.size() != count ||
        std::ranges::any_of(found->second.values, [](double value) {
            return !std::isfinite(value);
        })) {
        throw std::invalid_argument("frontier GAT tensor values invalid: " + name);
    }
    return found->second;
}

std::vector<double> frontier_dense(
    const std::vector<double>& input,
    const FrontierDenseTensor& weight,
    const FrontierDenseTensor& bias
) {
    const auto output_size = weight.shape.at(0);
    const auto input_size = weight.shape.at(1);
    if (input.size() != input_size || bias.shape != std::vector<std::size_t>{output_size}) {
        throw std::invalid_argument("frontier dense shape mismatch");
    }
    std::vector<double> output(output_size, 0.0);
    for (std::size_t row = 0; row < output_size; ++row) {
        double value = bias.values[row];
        for (std::size_t column = 0; column < input_size; ++column) {
            value += weight.values[row * input_size + column] * input[column];
        }
        output[row] = value;
    }
    return output;
}

void frontier_relu(std::vector<double>* values) {
    for (double& value : *values) {
        value = std::max(0.0, value);
    }
}

void frontier_layer_norm(
    std::vector<double>* values,
    const FrontierDenseTensor& weight,
    const FrontierDenseTensor& bias,
    double epsilon
) {
    if (values->empty() || weight.values.size() != values->size() ||
        bias.values.size() != values->size()) {
        throw std::invalid_argument("frontier LayerNorm shape mismatch");
    }
    const double mean = std::accumulate(values->begin(), values->end(), 0.0) /
                        static_cast<double>(values->size());
    double variance = 0.0;
    for (const double value : *values) {
        variance += (value - mean) * (value - mean);
    }
    variance /= static_cast<double>(values->size());
    const double inverse = 1.0 / std::sqrt(variance + epsilon);
    for (std::size_t index = 0; index < values->size(); ++index) {
        values->at(index) =
            (values->at(index) - mean) * inverse * weight.values[index] +
            bias.values[index];
    }
}

std::vector<std::vector<double>> frontier_gat_layer(
    const std::vector<std::vector<double>>& nodes,
    const std::vector<std::vector<double>>& encoded_edges,
    const std::vector<FrontierGraphEdge>& edges,
    const FrontierGatSeedModel& model,
    std::size_t layer,
    double layer_norm_epsilon
) {
    const std::string prefix = "layers." + std::to_string(layer) + ".";
    const auto& q_weight = frontier_tensor(
        model, prefix + "q.weight", {kFrontierHiddenSize, kFrontierHiddenSize});
    const auto& q_bias = frontier_tensor(
        model, prefix + "q.bias", {kFrontierHiddenSize});
    const auto& k_weight = frontier_tensor(
        model, prefix + "k.weight", {kFrontierHiddenSize, kFrontierHiddenSize});
    const auto& k_bias = frontier_tensor(
        model, prefix + "k.bias", {kFrontierHiddenSize});
    const auto& v_weight = frontier_tensor(
        model, prefix + "v.weight", {kFrontierHiddenSize, kFrontierHiddenSize});
    const auto& v_bias = frontier_tensor(
        model, prefix + "v.bias", {kFrontierHiddenSize});
    const auto& edge_weight = frontier_tensor(
        model, prefix + "edge_attention.weight",
        {kFrontierHeadCount, kFrontierHiddenSize});
    const auto& edge_bias = frontier_tensor(
        model, prefix + "edge_attention.bias", {kFrontierHeadCount});
    const auto& out_weight = frontier_tensor(
        model, prefix + "output.weight",
        {kFrontierHiddenSize, kFrontierHiddenSize});
    const auto& out_bias = frontier_tensor(
        model, prefix + "output.bias", {kFrontierHiddenSize});
    const auto& norm_weight = frontier_tensor(
        model, prefix + "layer_norm.weight", {kFrontierHiddenSize});
    const auto& norm_bias = frontier_tensor(
        model, prefix + "layer_norm.bias", {kFrontierHiddenSize});

    std::vector<std::vector<double>> queries;
    std::vector<std::vector<double>> keys;
    std::vector<std::vector<double>> values;
    queries.reserve(nodes.size());
    keys.reserve(nodes.size());
    values.reserve(nodes.size());
    for (const auto& node : nodes) {
        queries.push_back(frontier_dense(node, q_weight, q_bias));
        keys.push_back(frontier_dense(node, k_weight, k_bias));
        values.push_back(frontier_dense(node, v_weight, v_bias));
    }
    std::vector<std::vector<double>> edge_logits;
    edge_logits.reserve(encoded_edges.size());
    for (const auto& edge : encoded_edges) {
        edge_logits.push_back(frontier_dense(edge, edge_weight, edge_bias));
    }

    constexpr std::size_t head_size =
        kFrontierHiddenSize / kFrontierHeadCount;
    std::vector<std::vector<std::size_t>> incoming(nodes.size());
    for (std::size_t edge_index = 0; edge_index < edges.size(); ++edge_index) {
        if (edges[edge_index].source >= nodes.size() ||
            edges[edge_index].target >= nodes.size()) {
            throw std::invalid_argument("frontier graph endpoint out of range");
        }
        incoming[edges[edge_index].target].push_back(edge_index);
    }
    std::vector<std::vector<double>> output(
        nodes.size(), std::vector<double>(kFrontierHiddenSize, 0.0));
    for (std::size_t target = 0; target < nodes.size(); ++target) {
        for (std::size_t head = 0; head < kFrontierHeadCount; ++head) {
            std::vector<double> logits;
            logits.reserve(incoming[target].size());
            double maximum = -std::numeric_limits<double>::infinity();
            for (const auto edge_index : incoming[target]) {
                const auto source = edges[edge_index].source;
                double score = edge_logits[edge_index][head];
                for (std::size_t offset = 0; offset < head_size; ++offset) {
                    const auto hidden_index = head * head_size + offset;
                    score += queries[target][hidden_index] * keys[source][hidden_index] /
                             std::sqrt(static_cast<double>(head_size));
                }
                score = score >= 0.0 ? score : 0.2 * score;
                logits.push_back(score);
                maximum = std::max(maximum, score);
            }
            double denominator = 0.0;
            for (double& value : logits) {
                value = std::exp(value - maximum);
                denominator += value;
            }
            if (!(denominator > 0.0) || !std::isfinite(denominator)) {
                throw std::invalid_argument("frontier attention softmax invalid");
            }
            for (std::size_t local = 0; local < incoming[target].size(); ++local) {
                const auto edge_index = incoming[target][local];
                const auto source = edges[edge_index].source;
                const double probability = logits[local] / denominator;
                for (std::size_t offset = 0; offset < head_size; ++offset) {
                    const auto hidden_index = head * head_size + offset;
                    output[target][hidden_index] +=
                        probability * values[source][hidden_index];
                }
            }
        }
        output[target] = frontier_dense(output[target], out_weight, out_bias);
        for (std::size_t index = 0; index < kFrontierHiddenSize; ++index) {
            output[target][index] += nodes[target][index];
        }
        frontier_layer_norm(
            &output[target], norm_weight, norm_bias, layer_norm_epsilon);
        frontier_relu(&output[target]);
    }
    return output;
}

std::array<double, 3> frontier_gat_forward(
    const FrontierGatSeedModel& model,
    const FrontierGatBundle& bundle,
    const FrontierProbeTelemetry& graph
) {
    const auto& node_weight = frontier_tensor(
        model, "node_encoder.weight",
        {kFrontierHiddenSize, kFrontierNodeFeatureCount});
    const auto& node_bias = frontier_tensor(
        model, "node_encoder.bias", {kFrontierHiddenSize});
    const auto& edge_weight = frontier_tensor(
        model, "edge_encoder.weight",
        {kFrontierHiddenSize, kFrontierEdgeFeatureCount});
    const auto& edge_bias = frontier_tensor(
        model, "edge_encoder.bias", {kFrontierHiddenSize});
    const auto& context_weight = frontier_tensor(
        model, "context_encoder.weight",
        {kFrontierHiddenSize, kFrontierContextFeatureCount});
    const auto& context_bias = frontier_tensor(
        model, "context_encoder.bias", {kFrontierHiddenSize});
    const auto& pool_weight = frontier_tensor(
        model, "attention_pool.weight", {1U, kFrontierHiddenSize});
    const auto& pool_bias = frontier_tensor(
        model, "attention_pool.bias", {1U});
    const auto& head0_weight = frontier_tensor(
        model, "head.0.weight", {32U, 96U});
    const auto& head0_bias = frontier_tensor(
        model, "head.0.bias", {32U});
    const auto& head2_weight = frontier_tensor(
        model, "head.2.weight", {3U, 32U});
    const auto& head2_bias = frontier_tensor(
        model, "head.2.bias", {3U});

    auto normalize = [](double value, double mean, double scale) {
        if (!std::isfinite(value) || !std::isfinite(mean) ||
            !std::isfinite(scale) || !(scale > 0.0)) {
            throw std::invalid_argument("frontier normalization invalid");
        }
        return (value - mean) / scale;
    };
    if (bundle.node_mean.size() != kFrontierNodeFeatureCount ||
        bundle.node_scale.size() != kFrontierNodeFeatureCount ||
        bundle.edge_mean.size() != kFrontierEdgeFeatureCount ||
        bundle.edge_scale.size() != kFrontierEdgeFeatureCount ||
        bundle.context_mean.size() != kFrontierContextFeatureCount ||
        bundle.context_scale.size() != kFrontierContextFeatureCount) {
        throw std::invalid_argument("frontier normalization shape mismatch");
    }
    std::vector<std::vector<double>> nodes;
    nodes.reserve(graph.node_features.size());
    for (const auto& raw : graph.node_features) {
        std::vector<double> row(kFrontierNodeFeatureCount);
        for (std::size_t index = 0; index < row.size(); ++index) {
            row[index] = normalize(
                raw[index], bundle.node_mean[index], bundle.node_scale[index]);
        }
        nodes.push_back(frontier_dense(row, node_weight, node_bias));
        frontier_relu(&nodes.back());
    }
    std::vector<std::vector<double>> encoded_edges;
    encoded_edges.reserve(graph.edges.size());
    for (const auto& raw : graph.edges) {
        std::vector<double> row(kFrontierEdgeFeatureCount);
        for (std::size_t index = 0; index < row.size(); ++index) {
            row[index] = normalize(
                raw.features[index], bundle.edge_mean[index], bundle.edge_scale[index]);
        }
        encoded_edges.push_back(frontier_dense(row, edge_weight, edge_bias));
        frontier_relu(&encoded_edges.back());
    }
    nodes = frontier_gat_layer(
        nodes, encoded_edges, graph.edges, model, 0U,
        bundle.layer_norm_epsilon);
    nodes = frontier_gat_layer(
        nodes, encoded_edges, graph.edges, model, 1U,
        bundle.layer_norm_epsilon);

    std::vector<double> node_mean(kFrontierHiddenSize, 0.0);
    std::vector<double> node_max(
        kFrontierHiddenSize, -std::numeric_limits<double>::infinity());
    std::vector<double> attention_scores;
    attention_scores.reserve(nodes.size());
    double max_attention = -std::numeric_limits<double>::infinity();
    for (const auto& node : nodes) {
        for (std::size_t index = 0; index < kFrontierHiddenSize; ++index) {
            node_mean[index] += node[index] / static_cast<double>(nodes.size());
            node_max[index] = std::max(node_max[index], node[index]);
        }
        const double score = frontier_dense(node, pool_weight, pool_bias).front();
        attention_scores.push_back(score);
        max_attention = std::max(max_attention, score);
    }
    double attention_denominator = 0.0;
    for (double& score : attention_scores) {
        score = std::exp(score - max_attention);
        attention_denominator += score;
    }
    std::vector<double> attention_pool(kFrontierHiddenSize, 0.0);
    for (std::size_t node_index = 0; node_index < nodes.size(); ++node_index) {
        const double probability =
            attention_scores[node_index] / attention_denominator;
        for (std::size_t hidden = 0; hidden < kFrontierHiddenSize; ++hidden) {
            attention_pool[hidden] += probability * nodes[node_index][hidden];
        }
    }
    std::vector<double> edge_mean(kFrontierHiddenSize, 0.0);
    std::vector<double> edge_max(
        kFrontierHiddenSize, -std::numeric_limits<double>::infinity());
    for (const auto& edge : encoded_edges) {
        for (std::size_t hidden = 0; hidden < kFrontierHiddenSize; ++hidden) {
            edge_mean[hidden] +=
                edge[hidden] / static_cast<double>(encoded_edges.size());
            edge_max[hidden] = std::max(edge_max[hidden], edge[hidden]);
        }
    }
    std::vector<double> raw_context(kFrontierContextFeatureCount);
    for (std::size_t index = 0; index < raw_context.size(); ++index) {
        raw_context[index] = normalize(
            graph.context_features[index], bundle.context_mean[index],
            bundle.context_scale[index]);
    }
    auto context = frontier_dense(raw_context, context_weight, context_bias);
    frontier_relu(&context);
    std::vector<double> pooled;
    pooled.reserve(96U);
    pooled.insert(pooled.end(), node_mean.begin(), node_mean.end());
    pooled.insert(pooled.end(), node_max.begin(), node_max.end());
    pooled.insert(pooled.end(), attention_pool.begin(), attention_pool.end());
    pooled.insert(pooled.end(), edge_mean.begin(), edge_mean.end());
    pooled.insert(pooled.end(), edge_max.begin(), edge_max.end());
    pooled.insert(pooled.end(), context.begin(), context.end());
    auto hidden = frontier_dense(pooled, head0_weight, head0_bias);
    frontier_relu(&hidden);
    const auto logits = frontier_dense(hidden, head2_weight, head2_bias);
    return {
        frontier_sigmoid(logits[0]),
        frontier_sigmoid(logits[1]),
        frontier_sigmoid(logits[2]),
    };
}

bool frontier_bundle_is_valid(const FrontierGatBundle& bundle) {
    return bundle.schema_version ==
               "lunar_ice_bpc.p0v5_frontier_gat_native_bundle.v1" &&
           bundle.graph_schema_version ==
               "lunar_ice_bpc.p0v5_frontier_depth_rc_graph.v1" &&
           bundle.feature_schema_version ==
               "lunar_ice_bpc.p0v5_frontier_probe_features.v1" &&
           bundle.models.size() == 3U &&
           bundle.node_feature_names.size() == kFrontierNodeFeatureCount &&
           bundle.edge_feature_names.size() == kFrontierEdgeFeatureCount &&
           bundle.context_feature_names.size() == kFrontierContextFeatureCount &&
           std::isfinite(bundle.minimum_benefit_probability) &&
           std::isfinite(bundle.maximum_adverse_probability) &&
           std::isfinite(bundle.minimum_expected_gain) &&
           std::isfinite(bundle.adverse_penalty) &&
           std::isfinite(bundle.maximum_disagreement) &&
           bundle.minimum_benefit_probability >= 0.0 &&
           bundle.minimum_benefit_probability <= 1.0 &&
           bundle.maximum_adverse_probability >= 0.0 &&
           bundle.maximum_adverse_probability <= 1.0 &&
           bundle.minimum_expected_gain >= 0.0 &&
           bundle.adverse_penalty >= 0.0 &&
           bundle.maximum_disagreement >= 0.0 &&
           bundle.maximum_disagreement <= 1.0 &&
           std::isfinite(bundle.gain_scale) && bundle.gain_scale >= 0.0 &&
           std::isfinite(bundle.benefit_calibration.probability) &&
           std::isfinite(bundle.benefit_calibration.a) &&
           std::isfinite(bundle.benefit_calibration.b) &&
           std::isfinite(bundle.adverse_calibration.probability) &&
           std::isfinite(bundle.adverse_calibration.a) &&
           std::isfinite(bundle.adverse_calibration.b) &&
           bundle.layer_norm_epsilon > 0.0;
}

struct TemporalEvalEdge {
    std::size_t source = 0U;
    std::size_t target = 0U;
};

bool temporal_group_is_valid(
    const TemporalNormalizationGroup& group,
    std::size_t width
) {
    return group.mean.size() == width && group.scale.size() == width &&
           group.minimum.size() == width && group.maximum.size() == width &&
           std::ranges::all_of(group.scale, [](double value) {
               return std::isfinite(value) && value > 0.0;
           }) &&
           std::ranges::all_of(group.mean, [](double value) {
               return std::isfinite(value);
           }) &&
           std::ranges::all_of(group.minimum, [](double value) {
               return std::isfinite(value);
           }) &&
           std::ranges::all_of(group.maximum, [](double value) {
               return std::isfinite(value);
           }) &&
           std::ranges::equal(
               group.minimum, group.maximum,
               [](double minimum, double maximum) {
                   return minimum <= maximum;
               });
}

bool temporal_bundle_is_valid(const TemporalGatBundle& bundle) {
    return bundle.schema_version ==
               "lunar_ice_bpc.p0v5_temporal_frontier_gat_bundle.v2" &&
           bundle.graph_schema_version ==
               "lunar_ice_bpc.p0v5_temporal_multires_frontier_graph.v2" &&
           bundle.feature_schema_version ==
               "lunar_ice_bpc.p0v5_temporal_multires_features.v2" &&
           (bundle.selected_scale == 30U || bundle.selected_scale == 50U) &&
           (bundle.controller_kind == "temporal_gat" ||
            bundle.controller_kind == "no_message" ||
            bundle.controller_kind == "linear" ||
            bundle.controller_kind == "mlp") &&
           bundle.models.size() == 3U &&
           bundle.cell_node_feature_names.size() == kFrontierNodeFeatureCount &&
           bundle.cell_edge_feature_names.size() == kFrontierEdgeFeatureCount &&
           bundle.node_feature_names.size() == kTemporalGatNodeFeatureCount &&
           bundle.edge_feature_names.size() == kTemporalGatEdgeFeatureCount &&
           bundle.counter_feature_names.size() == kTemporalGatCounterFeatureCount &&
           bundle.context_feature_names.size() == kFrontierContextFeatureCount &&
           temporal_group_is_valid(bundle.cell_node, kFrontierNodeFeatureCount) &&
           temporal_group_is_valid(bundle.cell_edge, kFrontierEdgeFeatureCount) &&
           temporal_group_is_valid(bundle.node, kTemporalGatNodeFeatureCount) &&
           temporal_group_is_valid(bundle.edge, kTemporalGatEdgeFeatureCount) &&
           temporal_group_is_valid(bundle.counter, kTemporalGatCounterFeatureCount) &&
           temporal_group_is_valid(bundle.context, kFrontierContextFeatureCount) &&
           std::isfinite(bundle.minimum_benefit_probability) &&
           bundle.minimum_benefit_probability >= 0.0 &&
           bundle.minimum_benefit_probability <= 1.0 &&
           std::isfinite(bundle.maximum_adverse_probability) &&
           bundle.maximum_adverse_probability >= 0.0 &&
           bundle.maximum_adverse_probability <= 1.0 &&
           std::isfinite(bundle.minimum_expected_gain) &&
           bundle.minimum_expected_gain >= 0.0 &&
           std::isfinite(bundle.adverse_penalty) && bundle.adverse_penalty >= 0.0 &&
           std::isfinite(bundle.maximum_disagreement) &&
           bundle.maximum_disagreement >= 0.0 &&
           bundle.maximum_disagreement <= 1.0 &&
           std::isfinite(bundle.gain_scale) && bundle.gain_scale >= 0.0 &&
           std::isfinite(bundle.benefit_calibration.probability) &&
           std::isfinite(bundle.benefit_calibration.a) &&
           std::isfinite(bundle.benefit_calibration.b) &&
           std::isfinite(bundle.adverse_calibration.probability) &&
           std::isfinite(bundle.adverse_calibration.a) &&
           std::isfinite(bundle.adverse_calibration.b) &&
           bundle.layer_norm_epsilon > 0.0;
}

std::vector<std::vector<double>> temporal_gat_layer(
    const std::vector<std::vector<double>>& nodes,
    const std::vector<std::vector<double>>& encoded_edges,
    const std::vector<TemporalEvalEdge>& edges,
    const FrontierGatSeedModel& model,
    const std::string& prefix,
    double epsilon
) {
    const auto& q_weight = frontier_tensor(
        model, prefix + "q.weight",
        {kTemporalGatHiddenSize, kTemporalGatHiddenSize});
    const auto& q_bias = frontier_tensor(
        model, prefix + "q.bias", {kTemporalGatHiddenSize});
    const auto& k_weight = frontier_tensor(
        model, prefix + "k.weight",
        {kTemporalGatHiddenSize, kTemporalGatHiddenSize});
    const auto& k_bias = frontier_tensor(
        model, prefix + "k.bias", {kTemporalGatHiddenSize});
    const auto& v_weight = frontier_tensor(
        model, prefix + "v.weight",
        {kTemporalGatHiddenSize, kTemporalGatHiddenSize});
    const auto& v_bias = frontier_tensor(
        model, prefix + "v.bias", {kTemporalGatHiddenSize});
    const auto& edge_weight = frontier_tensor(
        model, prefix + "edge_attention.weight",
        {kTemporalGatHeadCount, kTemporalGatHiddenSize});
    const auto& edge_bias = frontier_tensor(
        model, prefix + "edge_attention.bias", {kTemporalGatHeadCount});
    const auto& output_weight = frontier_tensor(
        model, prefix + "output.weight",
        {kTemporalGatHiddenSize, kTemporalGatHiddenSize});
    const auto& output_bias = frontier_tensor(
        model, prefix + "output.bias", {kTemporalGatHiddenSize});
    const auto& norm_weight = frontier_tensor(
        model, prefix + "norm.weight", {kTemporalGatHiddenSize});
    const auto& norm_bias = frontier_tensor(
        model, prefix + "norm.bias", {kTemporalGatHiddenSize});

    std::vector<std::vector<double>> query, key, value, edge_logits;
    query.reserve(nodes.size());
    key.reserve(nodes.size());
    value.reserve(nodes.size());
    for (const auto& node : nodes) {
        query.push_back(frontier_dense(node, q_weight, q_bias));
        key.push_back(frontier_dense(node, k_weight, k_bias));
        value.push_back(frontier_dense(node, v_weight, v_bias));
    }
    edge_logits.reserve(encoded_edges.size());
    for (const auto& edge : encoded_edges) {
        edge_logits.push_back(frontier_dense(edge, edge_weight, edge_bias));
    }
    std::vector<std::vector<std::size_t>> incoming(nodes.size());
    for (std::size_t index = 0; index < edges.size(); ++index) {
        if (edges[index].source >= nodes.size() ||
            edges[index].target >= nodes.size()) {
            throw std::invalid_argument("Temporal-GAT edge endpoint out of range");
        }
        incoming[edges[index].target].push_back(index);
    }
    constexpr std::size_t head_width =
        kTemporalGatHiddenSize / kTemporalGatHeadCount;
    std::vector<std::vector<double>> aggregate(
        nodes.size(), std::vector<double>(kTemporalGatHiddenSize, 0.0));
    for (std::size_t target = 0; target < nodes.size(); ++target) {
        if (incoming[target].empty()) {
            aggregate[target] = query[target];
        } else {
            for (std::size_t head = 0; head < kTemporalGatHeadCount; ++head) {
                std::vector<double> logits;
                double maximum = -std::numeric_limits<double>::infinity();
                for (const auto edge_index : incoming[target]) {
                    const auto source = edges[edge_index].source;
                    double score = edge_logits[edge_index][head];
                    for (std::size_t offset = 0; offset < head_width; ++offset) {
                        const auto hidden = head * head_width + offset;
                        score += query[target][hidden] * key[source][hidden] /
                                 std::sqrt(static_cast<double>(head_width));
                    }
                    score = score >= 0.0 ? score : 0.2 * score;
                    logits.push_back(score);
                    maximum = std::max(maximum, score);
                }
                double denominator = 0.0;
                for (auto& score : logits) {
                    score = std::exp(score - maximum);
                    denominator += score;
                }
                if (!(denominator > 0.0) || !std::isfinite(denominator)) {
                    throw std::invalid_argument("Temporal-GAT attention invalid");
                }
                for (std::size_t local = 0; local < incoming[target].size(); ++local) {
                    const auto source = edges[incoming[target][local]].source;
                    const auto probability = logits[local] / denominator;
                    for (std::size_t offset = 0; offset < head_width; ++offset) {
                        const auto hidden = head * head_width + offset;
                        aggregate[target][hidden] +=
                            probability * value[source][hidden];
                    }
                }
            }
        }
        aggregate[target] = frontier_dense(
            aggregate[target], output_weight, output_bias);
        for (std::size_t hidden = 0; hidden < kTemporalGatHiddenSize; ++hidden) {
            aggregate[target][hidden] += nodes[target][hidden];
        }
        frontier_layer_norm(
            &aggregate[target], norm_weight, norm_bias, epsilon);
        frontier_relu(&aggregate[target]);
    }
    return aggregate;
}

std::vector<double> temporal_encode_graph(
    const std::vector<std::vector<double>>& raw_nodes,
    const std::vector<std::vector<double>>& raw_edge_features,
    const std::vector<TemporalEvalEdge>& edges,
    const TemporalNormalizationGroup& node_group,
    const TemporalNormalizationGroup& edge_group,
    const FrontierGatSeedModel& model,
    const std::string& node_encoder,
    const std::string& edge_encoder,
    const std::string& layer_prefix,
    const std::string& primary_attention_name,
    const std::string& secondary_attention_name,
    double epsilon,
    bool no_message,
    bool type_wise
) {
    if (raw_nodes.empty() || raw_edge_features.empty() ||
        raw_edge_features.size() != edges.size()) {
        throw std::invalid_argument("Temporal-GAT graph is empty or malformed");
    }
    const auto node_width = node_group.mean.size();
    const auto edge_width = edge_group.mean.size();
    const auto& node_weight = frontier_tensor(
        model, node_encoder + ".weight", {kTemporalGatHiddenSize, node_width});
    const auto& node_bias = frontier_tensor(
        model, node_encoder + ".bias", {kTemporalGatHiddenSize});
    const auto& edge_weight = frontier_tensor(
        model, edge_encoder + ".weight", {kTemporalGatHiddenSize, edge_width});
    const auto& edge_bias = frontier_tensor(
        model, edge_encoder + ".bias", {kTemporalGatHiddenSize});
    auto normalize = [](double value, double mean, double scale) {
        if (!std::isfinite(value) || !(scale > 0.0)) {
            throw std::invalid_argument("Temporal-GAT normalization invalid");
        }
        return (value - mean) / scale;
    };
    std::vector<std::vector<double>> nodes;
    for (const auto& raw : raw_nodes) {
        if (raw.size() != node_width) {
            throw std::invalid_argument("Temporal-GAT node width mismatch");
        }
        std::vector<double> row(node_width);
        for (std::size_t index = 0; index < node_width; ++index) {
            row[index] = normalize(
                raw[index], node_group.mean[index], node_group.scale[index]);
        }
        nodes.push_back(frontier_dense(row, node_weight, node_bias));
        frontier_relu(&nodes.back());
    }
    std::vector<std::vector<double>> encoded_edges;
    for (const auto& raw : raw_edge_features) {
        if (raw.size() != edge_width) {
            throw std::invalid_argument("Temporal-GAT edge width mismatch");
        }
        std::vector<double> row(edge_width);
        for (std::size_t index = 0; index < edge_width; ++index) {
            row[index] = normalize(
                raw[index], edge_group.mean[index], edge_group.scale[index]);
        }
        encoded_edges.push_back(frontier_dense(row, edge_weight, edge_bias));
        frontier_relu(&encoded_edges.back());
    }
    if (!no_message) {
        for (std::size_t layer = 0; layer < 2U; ++layer) {
            nodes = temporal_gat_layer(
                nodes, encoded_edges, edges, model,
                layer_prefix + "." + std::to_string(layer) + ".", epsilon);
        }
    }
    const auto pool = [&](const std::vector<std::size_t>& selected,
                          const std::string& attention_name) {
        if (selected.empty()) {
            throw std::invalid_argument(
                "Temporal-GAT type-wise pool is empty");
        }
        const auto& attention_weight = frontier_tensor(
            model, attention_name + ".weight",
            {1U, kTemporalGatHiddenSize});
        const auto& attention_bias = frontier_tensor(
            model, attention_name + ".bias", {1U});
        std::vector<double> mean(kTemporalGatHiddenSize, 0.0);
        std::vector<double> maximum(
            kTemporalGatHiddenSize,
            -std::numeric_limits<double>::infinity());
        std::vector<double> scores;
        scores.reserve(selected.size());
        double maximum_score = -std::numeric_limits<double>::infinity();
        for (const auto node_index : selected) {
            const auto& node = nodes.at(node_index);
            for (std::size_t index = 0; index < kTemporalGatHiddenSize; ++index) {
                mean[index] += node[index] /
                               static_cast<double>(selected.size());
                maximum[index] = std::max(maximum[index], node[index]);
            }
            const auto score = frontier_dense(
                node, attention_weight, attention_bias).front();
            scores.push_back(score);
            maximum_score = std::max(maximum_score, score);
        }
        double denominator = 0.0;
        for (auto& score : scores) {
            score = std::exp(score - maximum_score);
            denominator += score;
        }
        if (!(denominator > 0.0) || !std::isfinite(denominator)) {
            throw std::invalid_argument(
                "Temporal-GAT type-wise attention invalid");
        }
        std::vector<double> attention(kTemporalGatHiddenSize, 0.0);
        for (std::size_t local = 0; local < selected.size(); ++local) {
            const auto probability = scores[local] / denominator;
            const auto& node = nodes[selected[local]];
            for (std::size_t hidden = 0; hidden < kTemporalGatHiddenSize; ++hidden) {
                attention[hidden] += probability * node[hidden];
            }
        }
        std::vector<double> output;
        output.reserve(3U * kTemporalGatHiddenSize);
        output.insert(output.end(), mean.begin(), mean.end());
        output.insert(output.end(), maximum.begin(), maximum.end());
        output.insert(output.end(), attention.begin(), attention.end());
        return output;
    };
    std::vector<std::size_t> primary;
    std::vector<std::size_t> secondary;
    primary.reserve(nodes.size());
    secondary.reserve(nodes.size());
    for (std::size_t index = 0; index < nodes.size(); ++index) {
        if (!type_wise) {
            primary.push_back(index);
            continue;
        }
        if (raw_nodes[index].size() <= 25U) {
            throw std::invalid_argument(
                "Temporal-GAT node type features missing");
        }
        const bool is_label = raw_nodes[index][24] > 0.5;
        const bool is_task = raw_nodes[index][25] > 0.5;
        if (is_label == is_task) {
            throw std::invalid_argument(
                "Temporal-GAT node type is not one-hot");
        }
        (is_label ? primary : secondary).push_back(index);
    }
    auto output = pool(primary, primary_attention_name);
    if (type_wise) {
        const auto secondary_output = pool(
            secondary, secondary_attention_name);
        output.insert(
            output.end(), secondary_output.begin(), secondary_output.end());
    }
    return output;
}

std::array<double, kTemporalGatCounterFeatureCount> temporal_counter_values(
    const FrontierProbeTelemetry& telemetry
) {
    std::array<double, kTemporalGatCounterFeatureCount> values{};
    const auto& left = telemetry.trial_start_snapshot;
    const auto& right = telemetry.trial_end_snapshot;
    const std::array<double, 9> start{
        static_cast<double>(left.processed_labels),
        static_cast<double>(left.extended_labels),
        static_cast<double>(left.dominated_labels),
        static_cast<double>(left.dominance_candidate_checks),
        static_cast<double>(left.subset_dominance_candidate_checks),
        static_cast<double>(left.subset_dominance_rejected_labels),
        static_cast<double>(left.frontier_size),
        static_cast<double>(left.max_visited_bucket_size),
        static_cast<double>(left.negative_label_event_count),
    };
    const std::array<double, 9> end{
        static_cast<double>(right.processed_labels),
        static_cast<double>(right.extended_labels),
        static_cast<double>(right.dominated_labels),
        static_cast<double>(right.dominance_candidate_checks),
        static_cast<double>(right.subset_dominance_candidate_checks),
        static_cast<double>(right.subset_dominance_rejected_labels),
        static_cast<double>(right.frontier_size),
        static_cast<double>(right.max_visited_bucket_size),
        static_cast<double>(right.negative_label_event_count),
    };
    for (std::size_t index = 0; index < start.size(); ++index) {
        values[2U * index] = end[index] - start[index];
        values[2U * index + 1U] = (end[index] + 1.0) / (start[index] + 1.0);
    }
    const double start_rc = std::isfinite(left.best_true_reduced_cost)
                                ? left.best_true_reduced_cost : 0.0;
    const double end_rc = std::isfinite(right.best_true_reduced_cost)
                              ? right.best_true_reduced_cost : 0.0;
    values[18] = end_rc - start_rc;
    values[19] = std::abs(end_rc - start_rc);
    const auto start_count = telemetry.trial_start_label_graph.frontier_size;
    const auto end_count = telemetry.trial_end_label_graph.frontier_size;
    const auto survival = telemetry.temporal_surviving_label_count;
    values[20] = static_cast<double>(survival) /
                 static_cast<double>(std::max<std::size_t>(1U, start_count));
    values[21] = static_cast<double>(
        start_count + end_count - 2U * std::min(
            survival, std::min(start_count, end_count))) /
        static_cast<double>(std::max<std::size_t>(1U, start_count + end_count));
    values[22] = static_cast<double>(telemetry.temporal_new_label_count) /
                 static_cast<double>(std::max<std::size_t>(1U, start_count));
    // Wall time is telemetry, not a model feature: excluding it keeps the
    // response vector and its hash deterministic across identical requests.
    values[23] = 0.0;
    return values;
}

std::array<double, 3> temporal_gat_forward(
    const FrontierGatSeedModel& model,
    const TemporalGatBundle& bundle,
    const FrontierProbeSnapshot& cell_t0,
    const FrontierProbeSnapshot& cell_tk,
    const TemporalPortableGraph& graph_t0,
    const TemporalPortableGraph& graph_tk,
    const std::array<double, kTemporalGatCounterFeatureCount>& counters,
    const std::array<double, kFrontierContextFeatureCount>& context,
    std::size_t scale
) {
    if (bundle.controller_kind == "linear" ||
        bundle.controller_kind == "mlp") {
        std::vector<double> features;
        features.reserve(54U);
        for (std::size_t index = 0; index < counters.size(); ++index) {
            features.push_back((counters[index] - bundle.counter.mean[index]) /
                               bundle.counter.scale[index]);
        }
        for (std::size_t index = 0; index < context.size(); ++index) {
            features.push_back((context[index] - bundle.context.mean[index]) /
                               bundle.context.scale[index]);
        }
        features.push_back(scale == 30U ? 1.0 : 0.0);
        features.push_back(scale == 50U ? 1.0 : 0.0);
        std::vector<double> logits;
        if (bundle.controller_kind == "linear") {
            logits = frontier_dense(
                features, frontier_tensor(model, "weight", {3U, 54U}),
                frontier_tensor(model, "bias", {3U}));
        } else {
            auto hidden = frontier_dense(
                features, frontier_tensor(model, "0.weight", {64U, 54U}),
                frontier_tensor(model, "0.bias", {64U}));
            frontier_relu(&hidden);
            logits = frontier_dense(
                hidden, frontier_tensor(model, "2.weight", {3U, 64U}),
                frontier_tensor(model, "2.bias", {3U}));
        }
        return {frontier_sigmoid(logits[0]), frontier_sigmoid(logits[1]),
                frontier_sigmoid(logits[2])};
    }
    const bool no_message = bundle.controller_kind == "no_message";
    auto cell = [&](const FrontierProbeSnapshot& graph) {
        std::vector<std::vector<double>> nodes;
        std::vector<std::vector<double>> edge_features;
        std::vector<TemporalEvalEdge> edges;
        for (const auto& node : graph.node_features) {
            nodes.emplace_back(node.begin(), node.end());
        }
        for (const auto& edge : graph.edges) {
            edge_features.emplace_back(edge.features.begin(), edge.features.end());
            edges.push_back({edge.source, edge.target});
        }
        return temporal_encode_graph(
            nodes, edge_features, edges, bundle.cell_node, bundle.cell_edge,
            model, "cell_node", "cell_edge", "shared_layers",
            "cell_attention", "", bundle.layer_norm_epsilon, no_message,
            false);
    };
    auto label = [&](const TemporalPortableGraph& graph) {
        std::vector<std::vector<double>> nodes;
        std::vector<std::vector<double>> edge_features;
        std::vector<TemporalEvalEdge> edges;
        for (const auto& node : graph.node_features) {
            nodes.emplace_back(node.begin(), node.end());
        }
        for (const auto& edge : graph.edges) {
            edge_features.emplace_back(edge.features.begin(), edge.features.end());
            edges.push_back({edge.source, edge.target});
        }
        return temporal_encode_graph(
            nodes, edge_features, edges, bundle.node, bundle.edge,
            model, "label_node", "label_edge", "shared_layers",
            "label_attention", "task_attention", bundle.layer_norm_epsilon,
            no_message, true);
    };
    const auto c0 = cell(cell_t0);
    const auto ck = cell(cell_tk);
    const auto l0 = label(graph_t0);
    const auto lk = label(graph_tk);
    std::vector<double> combined;
    combined.reserve(1206U);
    auto append_temporal = [&](const auto& left, const auto& right) {
        combined.insert(combined.end(), left.begin(), left.end());
        combined.insert(combined.end(), right.begin(), right.end());
        for (std::size_t index = 0; index < left.size(); ++index) {
            combined.push_back(right[index] - left[index]);
        }
        for (std::size_t index = 0; index < left.size(); ++index) {
            combined.push_back(std::abs(right[index] - left[index]));
        }
    };
    append_temporal(c0, ck);
    append_temporal(l0, lk);
    for (std::size_t index = 0; index < counters.size(); ++index) {
        combined.push_back(
            (counters[index] - bundle.counter.mean[index]) /
            bundle.counter.scale[index]);
    }
    for (std::size_t index = 0; index < context.size(); ++index) {
        combined.push_back(
            (context[index] - bundle.context.mean[index]) /
            bundle.context.scale[index]);
    }
    combined.push_back(scale == 30U ? 1.0 : 0.0);
    combined.push_back(scale == 50U ? 1.0 : 0.0);
    const auto& trunk0_weight = frontier_tensor(
        model, "trunk.0.weight", {128U, 1206U});
    const auto& trunk0_bias = frontier_tensor(model, "trunk.0.bias", {128U});
    const auto& trunk2_weight = frontier_tensor(
        model, "trunk.2.weight", {64U, 128U});
    const auto& trunk2_bias = frontier_tensor(model, "trunk.2.bias", {64U});
    auto hidden = frontier_dense(combined, trunk0_weight, trunk0_bias);
    frontier_relu(&hidden);
    hidden = frontier_dense(hidden, trunk2_weight, trunk2_bias);
    frontier_relu(&hidden);
    const auto prefix = "scale_heads." + std::to_string(scale);
    const auto& head_weight = frontier_tensor(
        model, prefix + ".weight", {3U, 64U});
    const auto& head_bias = frontier_tensor(model, prefix + ".bias", {3U});
    const auto logits = frontier_dense(hidden, head_weight, head_bias);
    return {
        frontier_sigmoid(logits[0]), frontier_sigmoid(logits[1]),
        frontier_sigmoid(logits[2]),
    };
}

std::int64_t reduced_cost_bucket(double value, double width) {
    const long double bucket = std::floor(
        static_cast<long double>(value) /
        static_cast<long double>(width));
    const auto minimum = static_cast<long double>(
        std::numeric_limits<std::int64_t>::min());
    const auto maximum = static_cast<long double>(
        std::numeric_limits<std::int64_t>::max());
    return static_cast<std::int64_t>(
        std::clamp(bucket, minimum, maximum));
}

bool visited(const State& state, std::size_t task_index) {
    const auto word = task_index / 64U;
    const auto bit = task_index % 64U;
    return word < state.visited.size() && ((state.visited[word] >> bit) & 1U) != 0U;
}

bool mask_contains(const std::vector<std::uint64_t>& mask,
                   std::size_t task_index) {
    const auto word = task_index / 64U;
    const auto bit = task_index % 64U;
    return word < mask.size() && ((mask[word] >> bit) & 1U) != 0U;
}

VisitedMask dominance_visited_key(const Model& model, const State& state) {
    if (!model.dssr_relaxation_enabled) {
        return state.visited;
    }
    if (ng_dssr_active(model)) {
        auto key = ng_memory(state);
        for (std::size_t word = 0; word < key.size(); ++word) {
            const auto branch =
                word < model.dssr_branch_task_mask.size()
                    ? model.dssr_branch_task_mask[word]
                    : std::uint64_t{0};
            key[word] |= state.visited[word] & branch;
        }
        return key;
    }
    VisitedMask key{};
    for (std::size_t word = 0; word < key.size(); ++word) {
        const auto critical =
            word < model.dssr_critical_task_mask.size()
                ? model.dssr_critical_task_mask[word]
                : std::uint64_t{0};
        const auto branch =
            word < model.dssr_branch_task_mask.size()
                ? model.dssr_branch_task_mask[word]
                : std::uint64_t{0};
        key[word] = state.visited[word] & (critical | branch);
    }
    return key;
}

bool visited_subset(const State& lhs, const State& rhs) {
    for (std::size_t index = 0; index < lhs.visited.size(); ++index) {
        if ((lhs.visited[index] & ~rhs.visited[index]) != 0U) {
            return false;
        }
    }
    return true;
}

bool branch_subset_dominance_compatible(const Model& model, const State& lhs,
                                        const State& rhs) {
    for (const auto& decision : model.branch_decisions) {
        if (decision.sense != BranchSense::SameJourney) {
            continue;
        }
        const unsigned lhs_code =
            (decision.task_a_exists && visited(lhs, decision.task_a) ? 1U : 0U) |
            (decision.task_b_exists && visited(lhs, decision.task_b) ? 2U : 0U);
        const unsigned rhs_code =
            (decision.task_a_exists && visited(rhs, decision.task_a) ? 1U : 0U) |
            (decision.task_b_exists && visited(rhs, decision.task_b) ? 2U : 0U);
        const bool safe = lhs_code == rhs_code || (lhs_code == 0U && rhs_code == 3U);
        if (!safe) {
            return false;
        }
    }
    return true;
}

bool branch_terminal_feasible(const Model& model, const State& state) {
    for (const auto& decision : model.branch_decisions) {
        const bool has_a = decision.task_a_exists && visited(state, decision.task_a);
        const bool has_b = decision.task_b_exists && visited(state, decision.task_b);
        if (decision.sense == BranchSense::SameJourney && has_a != has_b) {
            return false;
        }
        if (decision.sense == BranchSense::DifferentJourney && has_a && has_b) {
            return false;
        }
    }
    return true;
}

void mark_visited(State* state, std::size_t task_index) {
    if (visited(*state, task_index)) {
        return;
    }
    const auto word = task_index / 64U;
    const auto bit = task_index % 64U;
    state->visited.at(word) |= (std::uint64_t{1} << bit);
    ++state->visited_count;
}

class JourneyExtension final : public rcspp::ExtensionFunction<JourneyResource> {
  public:
    explicit JourneyExtension(std::shared_ptr<const Model> model) : model_(std::move(model)) {}

    void extend(const JourneyResource& resource, const JourneyResource& extender,
                JourneyResource* output) override {
        const auto& current_value = resource.get_value();
        const auto& action_value = extender.get_value();
        if (current_value.is_action()) {
            State invalid;
            invalid.valid = false;
            output->set_value(JourneyValue::from_state(std::move(invalid)));
            return;
        }
        State next = current_value.state();
        if (!next.valid || !action_value.is_action()) {
            next.valid = false;
            output->set_value(JourneyValue::from_state(std::move(next)));
            return;
        }
        const auto& action = action_value.action();
        if (action.kind == ActionKind::VisitTask) {
            extend_visit(action, &next);
        } else if (action.kind == ActionKind::ReturnDepot) {
            extend_return(action, &next);
        } else {
            next.valid = next.at_depot && next.task_visit_count > 0 &&
                         next.sortie_task_count == 0 &&
                         branch_terminal_feasible(*model_, next);
        }
        output->set_value(JourneyValue::from_state(std::move(next)));
    }

    void extend_back(const JourneyResource&, const JourneyResource&, JourneyResource* output) override {
        State invalid;
        invalid.valid = false;
        output->set_value(JourneyValue::from_state(std::move(invalid)));
    }

    [[nodiscard]] std::unique_ptr<rcspp::ExtensionFunction<JourneyResource>> clone() const override {
        return std::make_unique<JourneyExtension>(*this);
    }

  private:
    void extend_visit(const Action& action, State* state) const {
        const auto epsilon = 1.0e-9;
        if (action.task_index >= model_->tasks.size() ||
            state->sortie_task_count >= model_->max_tasks_per_trip ||
            state->task_visit_count >= model_->tasks.size()) {
            state->valid = false;
            return;
        }
        const bool already_visited = visited(*state, action.task_index);
        const bool forbidden_repeat =
            already_visited &&
            (
                !model_->dssr_relaxation_enabled ||
                (
                    ng_dssr_active(*model_) &&
                    (
                        (
                            ng_memory(*state)[action.task_index / 64U] >>
                            (action.task_index % 64U)
                        ) &
                        1U
                    ) != 0U
                ) ||
                (
                    !ng_dssr_active(*model_) &&
                    mask_contains(
                        model_->dssr_critical_task_mask,
                        action.task_index
                    )
                )
            );
        if (forbidden_repeat) {
            state->valid = false;
            return;
        }
        const auto& task = model_->tasks[action.task_index];
        if (state->sortie_task_count == 0) {
            state->visited_at_sortie_start = state->visited_count;
            state->sortie_start_time = state->global_time;
            state->sortie_latest_start_time = model_->horizon;
            state->sortie_science_weight = 0.0;
        }
        const double arrival = state->global_time + action.travel_time;
        const double arrival_offset = arrival - state->sortie_start_time;
        state->sortie_latest_start_time =
            std::min(state->sortie_latest_start_time,
                     task.due_time - task.service_time - arrival_offset);
        const double required_start =
            std::max(state->sortie_start_time,
                     task.ready_time - arrival_offset);
        if (required_start > state->sortie_latest_start_time + epsilon) {
            state->valid = false;
            return;
        }
        const double departure_shift = required_start - state->sortie_start_time;
        if (departure_shift > epsilon) {
            state->raw_weighted_completion +=
                state->sortie_science_weight * departure_shift;
            state->sortie_start_time = required_start;
        }
        const double service_start = arrival + departure_shift;
        const double completion = service_start + task.service_time;
        if (completion > task.due_time + epsilon || completion > model_->horizon + epsilon) {
            state->valid = false;
            return;
        }
        state->sortie_demand += task.demand;
        state->sortie_energy += action.energy + task.service_energy;
        state->sortie_shadow += action.shadow + task.local_shadow_score * task.service_time;
        if (state->sortie_demand > model_->capacity + epsilon ||
            state->sortie_energy > model_->energy_limit + epsilon ||
            state->sortie_shadow > model_->shadow_limit + epsilon) {
            state->valid = false;
            return;
        }
        state->global_time = completion;
        state->raw_operating_cost += action.distance + action.energy + task.service_energy +
                                     task.service_cost;
        state->raw_risk += action.risk + task.local_thermal_risk * task.service_time * 0.01;
        state->raw_weighted_completion += task.science_weight * completion;
        state->sortie_science_weight += task.science_weight;
        state->task_dual_reward += task.dual;
        if (!ng_dssr_active(*model_)) {
            state->auxiliary.regular.positive_task_dual_reward +=
                std::max(0.0, task.dual);
        }
        if (model_->guidance_task_arc_enabled) {
            if (!model_->guidance_label_state_enabled) {
                state->guidance_score += task.guidance_priority;
            }
            if (action.model_arc_index < model_->arcs.size()) {
                state->guidance_score +=
                    model_->arcs[action.model_arc_index].guidance_priority;
            }
        }
        for (std::size_t cut_index = 0; cut_index < model_->cuts.size(); ++cut_index) {
            const auto& cut = model_->cuts[cut_index];
            if (cut.kind == CutKind::FleetLowerBound) {
                if (state->visited_count == 0) {
                    state->cut_dual_reward += cut.dual;
                }
                continue;
            }
            const auto word = action.task_index / 64U;
            const auto bit = action.task_index % 64U;
            if (word >= cut.task_mask.size() ||
                ((cut.task_mask[word] >> bit) & 1U) == 0U) {
                continue;
            }
            const auto overlap = cut_overlap(state->cut_state, cut);
            const auto old_coefficient = overlap / cut.divisor;
            if (overlap >= cut.max_overlap) {
                state->valid = false;
                return;
            }
            const auto next_overlap = static_cast<std::uint8_t>(overlap + 1U);
            set_cut_overlap(&state->cut_state, cut, next_overlap);
            const auto new_coefficient = next_overlap / cut.divisor;
            if (new_coefficient > old_coefficient) {
                state->cut_dual_reward +=
                    static_cast<double>(new_coefficient - old_coefficient) * cut.dual;
            }
        }
        state->at_depot = false;
        state->last_task_index = action.task_index;
        if (!ng_dssr_active(*model_)) {
            state->auxiliary.regular.last_model_arc_index =
                action.model_arc_index;
        }
        ++state->sortie_task_count;
        ++state->task_visit_count;
        mark_visited(state, action.task_index);
        if (ng_dssr_active(*model_)) {
            if (
                action.task_index >=
                model_->ng_dssr_task_memory_masks.size()
            ) {
                state->valid = false;
                return;
            }
            const auto& target_memory =
                model_->ng_dssr_task_memory_masks[action.task_index];
            auto next_memory = ng_memory(*state);
            for (std::size_t word = 0; word < next_memory.size(); ++word) {
                next_memory[word] &=
                    word < target_memory.size()
                        ? target_memory[word]
                        : std::uint64_t{0};
            }
            next_memory[action.task_index / 64U] |=
                std::uint64_t{1} << (action.task_index % 64U);
            ng_memory(state) = next_memory;
        }
        for (const auto& decision : model_->branch_decisions) {
            if (decision.sense != BranchSense::DifferentJourney) {
                continue;
            }
            const bool has_a = decision.task_a_exists && visited(*state, decision.task_a);
            const bool has_b = decision.task_b_exists && visited(*state, decision.task_b);
            if (has_a && has_b) {
                state->valid = false;
                return;
            }
        }
    }

    void extend_return(const Action& action, State* state) const {
        const double epsilon = 1.0e-9;
        if (state->at_depot || state->sortie_task_count == 0) {
            state->valid = false;
            return;
        }
        state->sortie_energy += action.energy;
        state->sortie_shadow += action.shadow;
        if (state->sortie_energy > model_->energy_limit + epsilon ||
            state->sortie_shadow > model_->shadow_limit + epsilon) {
            state->valid = false;
            return;
        }
        const double return_time = state->global_time + action.travel_time;
        const double recharge = model_->dock_overhead +
                                state->sortie_energy / std::max(epsilon, model_->recharge_power);
        const double end_time = return_time + recharge;
        if (end_time > model_->horizon + epsilon ||
            end_time <= state->sortie_start_time + epsilon ||
            (!model_->dssr_relaxation_enabled &&
             state->visited_count <= state->visited_at_sortie_start)) {
            state->valid = false;
            return;
        }
        state->global_time = end_time;
        state->raw_operating_cost += action.distance + action.energy;
        state->raw_risk += action.risk;
        if (model_->guidance_task_arc_enabled &&
            action.model_arc_index < model_->arcs.size()) {
            state->guidance_score +=
                model_->arcs[action.model_arc_index].guidance_priority;
        }
        state->at_depot = true;
        if (!ng_dssr_active(*model_)) {
            state->auxiliary.regular.last_model_arc_index =
                action.model_arc_index;
        }
        state->sortie_demand = 0.0;
        state->sortie_energy = 0.0;
        state->sortie_shadow = 0.0;
        state->sortie_latest_start_time = std::numeric_limits<double>::infinity();
        state->sortie_science_weight = 0.0;
        state->sortie_task_count = 0;
        ++state->sortie_count;
        assert(model_->dssr_relaxation_enabled ||
               state->visited_count > state->visited_at_sortie_start);
        assert(state->global_time > state->sortie_start_time);
        if (!model_->dssr_relaxation_enabled &&
            state->sortie_count > state->visited_count) {
            state->valid = false;
        }
    }

    std::shared_ptr<const Model> model_;
};

class JourneyFeasibility final : public rcspp::FeasibilityFunction<JourneyResource> {
  public:
    JourneyFeasibility(std::shared_ptr<const Model> model, std::size_t sink_id)
        : model_(std::move(model)), sink_id_(sink_id) {}

    [[nodiscard]] bool is_feasible(const JourneyResource& resource) override {
        const auto& state = resource.get_value().state();
        if (!state.valid) {
            return false;
        }
        if (model_->completion_bound_enabled && node_id_ != sink_id_) {
            ++model_->completion_bound_evaluated_labels;
            const double remaining_positive_dual = std::max(
                0.0,
                model_->positive_task_dual_sum -
                    state.auxiliary.regular.positive_task_dual_reward);
            const double optimistic_reduced_cost =
                reduced_cost(*model_, state) - remaining_positive_dual;
            // A journey is negative only for rc < threshold. Keep a numerical
            // safety margin so floating-point noise can only weaken pruning.
            if (optimistic_reduced_cost >=
                model_->completion_bound_threshold + 1.0e-12) {
                ++model_->completion_bound_pruned_labels;
                return false;
            }
        }
        if (node_id_ == sink_id_) {
            return state.at_depot && state.task_visit_count > 0 &&
                   state.sortie_task_count == 0 &&
                   branch_terminal_feasible(*model_, state);
        }
        return true;
    }

    [[nodiscard]] bool can_be_merged(const JourneyResource&, const JourneyResource&) override {
        return false;
    }

    [[nodiscard]] std::unique_ptr<rcspp::FeasibilityFunction<JourneyResource>> clone() const override {
        return std::make_unique<JourneyFeasibility>(*this);
    }

  protected:
    void preprocess(std::size_t node_id) override { node_id_ = node_id; }

  private:
    std::shared_ptr<const Model> model_;
    std::size_t sink_id_ = 0;
    std::size_t node_id_ = 0;
};

class JourneyCost final : public rcspp::CostFunction<JourneyResource> {
  public:
    explicit JourneyCost(std::shared_ptr<const Model> model) : model_(std::move(model)) {}

    [[nodiscard]] double get_cost(const JourneyResource& resource) const override {
        const auto& state = resource.get_value().state();
        return state.valid ? reduced_cost(*model_, state) : std::numeric_limits<double>::infinity();
    }

    [[nodiscard]] std::unique_ptr<rcspp::CostFunction<JourneyResource>> clone() const override {
        return std::make_unique<JourneyCost>(*this);
    }

  private:
    std::shared_ptr<const Model> model_;
};

class JourneyDominance final : public rcspp::DominanceFunction<JourneyResource> {
  public:
    JourneyDominance(std::shared_ptr<const Model> model, double dominance_epsilon,
                     double resource_epsilon)
        : model_(std::move(model)),
          dominance_epsilon_(dominance_epsilon),
          resource_epsilon_(resource_epsilon) {}

    [[nodiscard]] bool check_dominance(const JourneyResource& lhs,
                                       const JourneyResource& rhs) override {
        return dominates(lhs, rhs, dominance_epsilon_);
    }

    bool fast_check_dominance(const JourneyResource& lhs, const JourneyResource& rhs,
                              double delta) override {
        return dominates(lhs, rhs, std::max(dominance_epsilon_, delta));
    }

    [[nodiscard]] std::unique_ptr<rcspp::DominanceFunction<JourneyResource>> clone() const override {
        return std::make_unique<JourneyDominance>(*this);
    }

  private:
    bool dominates(const JourneyResource& lhs_resource, const JourneyResource& rhs_resource,
                   double cost_epsilon) const {
        const auto& lhs = lhs_resource.get_value().state();
        const auto& rhs = rhs_resource.get_value().state();
        if (!lhs.valid || !rhs.valid || lhs.at_depot != rhs.at_depot) {
            return false;
        }
        if (
            ng_dssr_active(*model_) &&
            !same_active_cut_state(lhs.cut_state, rhs.cut_state)
        ) {
            return false;
        }
        // During a sortie, a later task may require a retroactive depot
        // departure shift.  Existing resource dominance does not carry the
        // complete departure-feasibility interval and shift-cost intercept, so
        // active-sortie dominance would be unsafe under no-task-wait timing.
        if (!lhs.at_depot) {
            return false;
        }
        const auto lhs_key = dominance_visited_key(*model_, lhs);
        const auto rhs_key = dominance_visited_key(*model_, rhs);
        if (lhs_key != rhs_key) {
            if (model_->dssr_relaxation_enabled ||
                !model_->subset_dominance_enabled ||
                lhs.visited_count == 0 || !visited_subset(lhs, rhs) ||
                !same_active_cut_state(lhs.cut_state, rhs.cut_state) ||
                !branch_subset_dominance_compatible(*model_, lhs, rhs)) {
                return false;
            }
        }
        return lhs.global_time <= rhs.global_time + resource_epsilon_ &&
               lhs.task_visit_count <= rhs.task_visit_count &&
               lhs.sortie_demand <= rhs.sortie_demand + resource_epsilon_ &&
               lhs.sortie_energy <= rhs.sortie_energy + resource_epsilon_ &&
               lhs.sortie_shadow <= rhs.sortie_shadow + resource_epsilon_ &&
               lhs.sortie_task_count <= rhs.sortie_task_count &&
               reduced_cost(*model_, lhs) <= reduced_cost(*model_, rhs) + cost_epsilon;
    }

    std::shared_ptr<const Model> model_;
    double dominance_epsilon_;
    double resource_epsilon_;
};

// The auxiliary RealResource carried exactly 0.0 on every arc.  Removing it
// leaves cost, feasibility, dominance and path reconstruction unchanged while
// eliminating one heap-allocated sub-resource from every label.
using Composition = rcspp::ResourceTypeComposition<JourneyResource>;

struct VisitedKeyHash {
    std::size_t operator()(const VisitedMask& value) const noexcept {
        std::size_t seed = value.size();
        for (const auto word : value) {
            seed ^= std::hash<std::uint64_t>{}(word) + 0x9e3779b97f4a7c15ULL +
                    (seed << 6U) + (seed >> 2U);
        }
        return seed;
    }
};

struct ProofQueuePotentialTrace {
    ProofQueuePotentialTrace(
        std::size_t task_count,
        std::size_t arc_count,
        bool label_trace,
        std::size_t label_trace_limit,
        double bucket_width,
        LabelTraceSamplingMode sampling_mode,
        std::uint64_t sampling_seed,
        std::size_t preference_cap,
        std::size_t surface_cap,
        std::size_t surface_label_cap,
        std::size_t witness_cap,
        std::size_t witness_ancestor_cap_value
    )
        : task_rows(task_count),
          arc_rows(arc_count),
          label_trace_enabled(label_trace),
          max_label_trace_rows(label_trace_limit),
          guidance_bucket_width(bucket_width),
          label_trace_sampling_mode(sampling_mode),
          label_trace_seed(sampling_seed),
          preference_cap_per_family(preference_cap),
          surface_reservoir_count(surface_cap),
          surface_labels_per_bucket(surface_label_cap),
          witness_route_cap(witness_cap),
          witness_ancestor_cap(witness_ancestor_cap_value) {
        for (std::size_t index = 0; index < task_rows.size(); ++index) {
            task_rows[index].task_index = index;
        }
        for (std::size_t index = 0; index < arc_rows.size(); ++index) {
            arc_rows[index].task_index = index;
        }
    }

    struct SurfaceClass {
        bool terminal = false;
        std::size_t visited_count = 0;
        std::int64_t reduced_cost_bucket = 0;

        bool operator==(const SurfaceClass&) const = default;
    };

    struct SurfaceClassHash {
        std::size_t operator()(const SurfaceClass& value) const noexcept {
            auto seed = std::hash<std::size_t>{}(value.visited_count);
            seed ^= std::hash<std::int64_t>{}(value.reduced_cost_bucket) +
                    0x9e3779b97f4a7c15ULL + (seed << 6U) + (seed >> 2U);
            seed ^= std::hash<bool>{}(value.terminal) +
                    0x9e3779b97f4a7c15ULL + (seed << 6U) + (seed >> 2U);
            return seed;
        }
    };

    struct RankedLabel {
        std::uint64_t key = 0;
        LabelStateTraceRow row;
    };

    struct RankedSurface {
        std::uint64_t key = 0;
        SurfaceClass surface;
    };

    struct RankedSurfaceLess {
        bool operator()(const RankedSurface& lhs, const RankedSurface& rhs) const {
            return std::tie(
                       lhs.key,
                       lhs.surface.terminal,
                       lhs.surface.visited_count,
                       lhs.surface.reduced_cost_bucket) <
                   std::tie(
                       rhs.key,
                       rhs.surface.terminal,
                       rhs.surface.visited_count,
                       rhs.surface.reduced_cost_bucket);
        }
    };

    struct PreferenceSample {
        std::uint64_t key = 0;
        LabelStateTraceRow winner;
        LabelStateTraceRow loser;
        LabelPreferenceKind kind = LabelPreferenceKind::ExistingDominator;
    };

    struct PreferenceSampleLess {
        bool operator()(const PreferenceSample& lhs, const PreferenceSample& rhs) const {
            return std::tie(
                       lhs.key,
                       lhs.winner.label_id,
                       lhs.loser.label_id,
                       lhs.kind) <
                   std::tie(
                       rhs.key,
                       rhs.winner.label_id,
                       rhs.loser.label_id,
                       rhs.kind);
        }
    };

    static std::uint64_t mix64(std::uint64_t value) {
        value += 0x9e3779b97f4a7c15ULL;
        value = (value ^ (value >> 30U)) * 0xbf58476d1ce4e5b9ULL;
        value = (value ^ (value >> 27U)) * 0x94d049bb133111ebULL;
        return value ^ (value >> 31U);
    }

    std::uint64_t ranked_key(
        std::uint64_t tag,
        std::uint64_t first,
        std::uint64_t second = 0,
        std::uint64_t third = 0
    ) const {
        auto value = mix64(label_trace_seed ^ tag);
        value = mix64(value ^ mix64(first));
        value = mix64(value ^ mix64(second));
        return mix64(value ^ mix64(third));
    }

    LabelStateTraceRow make_label_row(
        const rcspp::Label<Composition>& label,
        const Model& model,
        double priority
    ) const {
        const auto& state = label.get_resource()
                                .template get_component<JourneyResource>(0)
                                .get_value()
                                .get_value()
                                .state();
        const double partial_cost = label.get_cost();
        LabelStateTraceRow row;
        row.label_id = label.id;
        if (label.prev_label != nullptr) {
            row.parent_label_id = label.prev_label->id;
        }
        if (label.get_end_node() != nullptr) {
            row.current_node_id = label.get_end_node()->id;
        }
        row.last_task_index = state.last_task_index;
        row.visited_count = state.visited_count;
        if (!ng_dssr_active(model)) {
            row.last_model_arc_index =
                state.auxiliary.regular.last_model_arc_index;
        }
        row.reduced_cost_bucket = reduced_cost_bucket(
            partial_cost, guidance_bucket_width);
        row.partial_reduced_cost = partial_cost;
        row.label_state_priority = priority;
        row.can_terminate = state.at_depot && state.task_visit_count > 0;
        row.features = label_state_features(model, state, partial_cost);
        return row;
    }

    static bool ranked_label_less(
        const RankedLabel& lhs,
        const RankedLabel& rhs
    ) {
        return std::tie(lhs.key, lhs.row.label_id) <
               std::tie(rhs.key, rhs.row.label_id);
    }

    void record_surface_label(LabelStateTraceRow row) {
        const SurfaceClass surface{
            .terminal = row.can_terminate,
            .visited_count = row.visited_count,
            .reduced_cost_bucket = row.reduced_cost_bucket,
        };
        if (seen_surface_classes.insert(surface).second) {
            ++surface_seen_count;
        }
        auto found = surface_rows.find(surface);
        if (found == surface_rows.end()) {
            const RankedSurface candidate{
                .key = ranked_key(
                    0x53555246414345ULL,
                    surface.terminal ? 1U : 0U,
                    surface.visited_count,
                    static_cast<std::uint64_t>(surface.reduced_cost_bucket)),
                .surface = surface,
            };
            if (surface_rows.size() >= surface_reservoir_count) {
                if (
                    surface_heap.empty() ||
                    !RankedSurfaceLess{}(candidate, surface_heap.top())
                ) {
                    return;
                }
                surface_rows.erase(surface_heap.top().surface);
                surface_heap.pop();
            }
            surface_heap.push(candidate);
            found = surface_rows.emplace(
                surface, std::vector<RankedLabel>{}).first;
        }
        auto& values = found->second;
        if (std::ranges::any_of(values, [&](const RankedLabel& value) {
                return value.row.label_id == row.label_id;
            })) {
            return;
        }
        RankedLabel candidate{
            .key = ranked_key(0x4c4142454cULL, row.label_id),
            .row = std::move(row),
        };
        if (values.size() < surface_labels_per_bucket) {
            values.push_back(std::move(candidate));
            return;
        }
        const auto worst = std::max_element(
            values.begin(), values.end(), ranked_label_less);
        if (ranked_label_less(candidate, *worst)) {
            *worst = std::move(candidate);
        }
    }

    template <typename Queue>
    static void retain_bottom_k(
        Queue& values,
        PreferenceSample sample,
        std::size_t capacity
    ) {
        if (values.size() < capacity) {
            values.push(std::move(sample));
        } else if (PreferenceSampleLess{}(sample, values.top())) {
            values.pop();
            values.push(std::move(sample));
        }
    }

    void record_label(
        const rcspp::Label<Composition>& label,
        const Model& model,
        double priority,
        bool preserve_negative_ancestor = false
    ) {
        if (!label_trace_enabled) {
            return;
        }
        if (
            label_trace_sampling_mode ==
            LabelTraceSamplingMode::QGR1StratifiedReservoirV1
        ) {
            record_surface_label(make_label_row(label, model, priority));
            return;
        }
        const auto found = label_row_by_id.find(label.id);
        if (found != label_row_by_id.end()) {
            auto& row = label_rows[found->second];
            if (label.prev_label != nullptr) {
                row.parent_label_id = label.prev_label->id;
            }
            return;
        }
        if (
            label_rows.size() >= max_label_trace_rows &&
            !preserve_negative_ancestor
        ) {
            label_trace_truncated = true;
            return;
        }
        const auto& state = label.get_resource()
                                .template get_component<JourneyResource>(0)
                                .get_value()
                                .get_value()
                                .state();
        const double partial_cost = label.get_cost();
        LabelStateTraceRow row;
        row.label_id = label.id;
        if (label.prev_label != nullptr) {
            row.parent_label_id = label.prev_label->id;
        }
        if (label.get_end_node() != nullptr) {
            row.current_node_id = label.get_end_node()->id;
        }
        row.last_task_index = state.last_task_index;
        row.visited_count = state.visited_count;
        if (!ng_dssr_active(model)) {
            row.last_model_arc_index =
                state.auxiliary.regular.last_model_arc_index;
        }
        row.reduced_cost_bucket = reduced_cost_bucket(
            partial_cost, guidance_bucket_width);
        row.partial_reduced_cost = partial_cost;
        row.label_state_priority = priority;
        row.can_terminate = state.at_depot && state.task_visit_count > 0;
        row.features = label_state_features(model, state, partial_cost);
        label_row_by_id.emplace(label.id, label_rows.size());
        label_rows.push_back(std::move(row));
    }

    void record_preference(
        const rcspp::Label<Composition>& winner,
        const rcspp::Label<Composition>& loser,
        const Model& model,
        LabelPreferenceKind kind
    ) {
        if (!label_trace_enabled) {
            return;
        }
        if (
            label_trace_sampling_mode ==
            LabelTraceSamplingMode::QGR1StratifiedReservoirV1
        ) {
            auto winner_row = make_label_row(
                winner,
                model,
                qg2_label_state_priority(
                    model,
                    winner.get_resource()
                        .template get_component<JourneyResource>(0)
                        .get_value()
                        .get_value()
                        .state(),
                    winner.get_cost()));
            auto loser_row = make_label_row(
                loser,
                model,
                qg2_label_state_priority(
                    model,
                    loser.get_resource()
                        .template get_component<JourneyResource>(0)
                        .get_value()
                        .get_value()
                        .state(),
                    loser.get_cost()));
            PreferenceSample sample{
                .key = ranked_key(
                    kind == LabelPreferenceKind::ExistingDominator
                        ? 0x4558495354494e47ULL
                        : 0x494e434f4d494e47ULL,
                    winner.id,
                    loser.id),
                .winner = std::move(winner_row),
                .loser = std::move(loser_row),
                .kind = kind,
            };
            if (kind == LabelPreferenceKind::ExistingDominator) {
                ++existing_preference_seen;
                retain_bottom_k(
                    existing_preference_samples,
                    std::move(sample),
                    preference_cap_per_family);
            } else {
                ++incoming_preference_seen;
                retain_bottom_k(
                    incoming_preference_samples,
                    std::move(sample),
                    preference_cap_per_family);
            }
            return;
        }
        record_label(
            winner,
            model,
            qg2_label_state_priority(model,
                                     winner.get_resource()
                                         .template get_component<JourneyResource>(0)
                                         .get_value()
                                         .get_value()
                                         .state(),
                                     winner.get_cost()));
        record_label(
            loser,
            model,
            qg2_label_state_priority(model,
                                     loser.get_resource()
                                         .template get_component<JourneyResource>(0)
                                         .get_value()
                                         .get_value()
                                         .state(),
                                     loser.get_cost()));
        if (preference_rows.size() >= max_label_trace_rows) {
            label_trace_truncated = true;
            return;
        }
        preference_rows.push_back({
            .winner_label_id = winner.id,
            .loser_label_id = loser.id,
            .kind = kind,
        });
    }

    void record_negative_witness(
        const rcspp::Label<Composition>& end_label,
        const Model& model,
        double reduced_cost_value,
        std::size_t solution_index,
        double elapsed_seconds
    ) {
        if (!label_trace_enabled) {
            return;
        }
        if (
            label_trace_sampling_mode ==
            LabelTraceSamplingMode::QGR1StratifiedReservoirV1
        ) {
            ++witness_seen_count;
            if (witness_rows.size() >= witness_route_cap) {
                label_trace_incomplete = true;
                label_trace_truncated = true;
                return;
            }
            std::vector<LabelStateTraceRow> chain;
            const auto* cursor = &end_label;
            while (cursor != nullptr) {
                const auto& state = cursor->get_resource()
                                        .template get_component<JourneyResource>(0)
                                        .get_value()
                                        .get_value()
                                        .state();
                chain.push_back(make_label_row(
                    *cursor,
                    model,
                    qg2_label_state_priority(
                        model, state, cursor->get_cost())));
                cursor = cursor->prev_label;
            }
            std::ranges::reverse(chain);
            std::size_t additions = 0;
            for (const auto& value : chain) {
                additions += !witness_label_rows.contains(value.label_id);
            }
            if (witness_label_rows.size() + additions > witness_ancestor_cap) {
                label_trace_incomplete = true;
                label_trace_truncated = true;
                return;
            }
            NegativeWitnessTraceRow row;
            row.solution_index = solution_index;
            row.reduced_cost = reduced_cost_value;
            row.elapsed_seconds = std::max(0.0, elapsed_seconds);
            for (const auto& value : chain) {
                witness_label_rows.emplace(value.label_id, value);
                row.ancestor_label_ids.push_back(value.label_id);
            }
            witness_rows.push_back(std::move(row));
            return;
        }
        if (witness_rows.size() >= 512U) {
            label_trace_truncated = true;
            return;
        }
        NegativeWitnessTraceRow row;
        row.solution_index = solution_index;
        row.reduced_cost = reduced_cost_value;
        row.elapsed_seconds = std::max(0.0, elapsed_seconds);
        const auto* cursor = &end_label;
        while (cursor != nullptr) {
            const auto& state = cursor->get_resource()
                                    .template get_component<JourneyResource>(0)
                                    .get_value()
                                    .get_value()
                                    .state();
            record_label(
                *cursor,
                model,
                qg2_label_state_priority(
                    model, state, cursor->get_cost()),
                true);
            row.ancestor_label_ids.push_back(cursor->id);
            cursor = cursor->prev_label;
        }
        std::ranges::reverse(row.ancestor_label_ids);
        witness_rows.push_back(std::move(row));
    }

    void finalize_label_trace() {
        if (
            !label_trace_enabled ||
            label_trace_sampling_mode !=
                LabelTraceSamplingMode::QGR1StratifiedReservoirV1
        ) {
            return;
        }
        std::unordered_map<std::uint64_t, LabelStateTraceRow> retained =
            witness_label_rows;
        for (const auto& [surface, values] : surface_rows) {
            static_cast<void>(surface);
            for (const auto& value : values) {
                retained.emplace(value.row.label_id, value.row);
            }
        }
        auto drain_preferences = [&](auto& samples) {
            std::vector<PreferenceSample> ordered;
            ordered.reserve(samples.size());
            while (!samples.empty()) {
                ordered.push_back(samples.top());
                samples.pop();
            }
            std::ranges::sort(ordered, PreferenceSampleLess{});
            for (const auto& sample : ordered) {
                retained.emplace(sample.winner.label_id, sample.winner);
                retained.emplace(sample.loser.label_id, sample.loser);
                preference_rows.push_back({
                    .winner_label_id = sample.winner.label_id,
                    .loser_label_id = sample.loser.label_id,
                    .kind = sample.kind,
                });
            }
        };
        drain_preferences(existing_preference_samples);
        existing_preference_retained = preference_rows.size();
        drain_preferences(incoming_preference_samples);
        incoming_preference_retained =
            preference_rows.size() - existing_preference_retained;
        std::ranges::sort(preference_rows, [](const auto& lhs, const auto& rhs) {
            return std::tie(lhs.kind, lhs.winner_label_id, lhs.loser_label_id) <
                   std::tie(rhs.kind, rhs.winner_label_id, rhs.loser_label_id);
        });
        preference_rows.erase(
            std::unique(
                preference_rows.begin(),
                preference_rows.end(),
                [](const auto& lhs, const auto& rhs) {
                    return lhs.kind == rhs.kind &&
                           lhs.winner_label_id == rhs.winner_label_id &&
                           lhs.loser_label_id == rhs.loser_label_id;
                }),
            preference_rows.end());
        label_rows.clear();
        label_rows.reserve(retained.size());
        for (auto& [label_id, row] : retained) {
            static_cast<void>(label_id);
            label_rows.push_back(std::move(row));
        }
        std::ranges::sort(label_rows, [](const auto& lhs, const auto& rhs) {
            return lhs.label_id < rhs.label_id;
        });
        if (label_rows.size() > max_label_trace_rows) {
            label_trace_incomplete = true;
            label_trace_truncated = true;
            label_rows.resize(max_label_trace_rows);
        }
        surface_retained_count = surface_rows.size();
        surface_label_retained_count = 0;
        for (const auto& [surface, values] : surface_rows) {
            static_cast<void>(surface);
            surface_label_retained_count += values.size();
        }
        witness_retained_count = witness_rows.size();
        witness_ancestor_retained_count = witness_label_rows.size();
        final_label_row_count = label_rows.size();
    }

    std::vector<TaskDominanceTraceRow> task_rows;
    std::vector<TaskDominanceTraceRow> arc_rows;
    bool label_trace_enabled = false;
    bool label_trace_truncated = false;
    bool label_trace_incomplete = false;
    std::size_t max_label_trace_rows = 0;
    double guidance_bucket_width = 0.01;
    LabelTraceSamplingMode label_trace_sampling_mode =
        LabelTraceSamplingMode::PrefixV1;
    std::uint64_t label_trace_seed = 0;
    std::size_t preference_cap_per_family = 0;
    std::size_t surface_reservoir_count = 0;
    std::size_t surface_labels_per_bucket = 0;
    std::size_t witness_route_cap = 0;
    std::size_t witness_ancestor_cap = 0;
    std::size_t existing_preference_seen = 0;
    std::size_t incoming_preference_seen = 0;
    std::size_t existing_preference_retained = 0;
    std::size_t incoming_preference_retained = 0;
    std::size_t surface_seen_count = 0;
    std::size_t surface_retained_count = 0;
    std::size_t surface_label_retained_count = 0;
    std::size_t witness_seen_count = 0;
    std::size_t witness_retained_count = 0;
    std::size_t witness_ancestor_retained_count = 0;
    std::size_t final_label_row_count = 0;
    std::vector<LabelStateTraceRow> label_rows;
    std::vector<LabelPreferenceTraceRow> preference_rows;
    std::vector<NegativeWitnessTraceRow> witness_rows;
    std::unordered_map<std::uint64_t, std::size_t> label_row_by_id;
    std::unordered_map<
        SurfaceClass,
        std::vector<RankedLabel>,
        SurfaceClassHash> surface_rows;
    std::priority_queue<
        RankedSurface,
        std::vector<RankedSurface>,
        RankedSurfaceLess> surface_heap;
    std::unordered_set<SurfaceClass, SurfaceClassHash> seen_surface_classes;
    std::priority_queue<
        PreferenceSample,
        std::vector<PreferenceSample>,
        PreferenceSampleLess> existing_preference_samples;
    std::priority_queue<
        PreferenceSample,
        std::vector<PreferenceSample>,
        PreferenceSampleLess> incoming_preference_samples;
    std::unordered_map<std::uint64_t, LabelStateTraceRow> witness_label_rows;
};

struct DssrPressureMonitor {
    explicit DssrPressureMonitor(
        std::shared_ptr<const Model> source_model,
        std::size_t bucket_limit,
        std::size_t candidate_check_limit
    )
        : model(std::move(source_model)),
          max_bucket_limit(bucket_limit),
          max_candidate_check_limit(candidate_check_limit) {}

    void observe_bucket(
        std::size_t bucket_size,
        const std::vector<std::size_t>& visited_counts
    ) {
        if (bucket_size <= max_bucket_size) {
            return;
        }
        max_bucket_size = bucket_size;
        hottest_bucket_size = bucket_size;
        hottest_bucket_visited_counts = visited_counts;
        select_split_task();
        if (
            max_bucket_limit > 0U &&
            max_bucket_size >= max_bucket_limit
        ) {
            if (!split_task_id.empty()) {
                triggered = true;
                trigger_reason = "max_bucket_size";
            } else {
                refinement_exhausted = true;
            }
        }
    }

    void record_candidate_check() {
        ++dominance_candidate_checks;
        if (
            !triggered &&
            !refinement_exhausted &&
            max_candidate_check_limit > 0U &&
            dominance_candidate_checks >= max_candidate_check_limit
        ) {
            select_split_task();
            if (!split_task_id.empty()) {
                triggered = true;
                trigger_reason = "dominance_candidate_checks";
            } else {
                refinement_exhausted = true;
            }
        }
    }

    void select_split_task() {
        split_task_index = std::numeric_limits<std::size_t>::max();
        split_task_id.clear();
        split_balance = 0U;
        if (
            model == nullptr ||
            hottest_bucket_visited_counts.size() != model->tasks.size()
        ) {
            return;
        }
        bool selected = false;
        for (const auto& task : model->tasks) {
            const auto task_index = task.index;
            if (
                task_index >= hottest_bucket_visited_counts.size() ||
                mask_contains(model->dssr_critical_task_mask, task_index) ||
                mask_contains(model->dssr_branch_task_mask, task_index)
            ) {
                continue;
            }
            const auto visited_count =
                hottest_bucket_visited_counts[task_index];
            const auto balance = std::min(
                visited_count,
                hottest_bucket_size - visited_count
            );
            if (
                !selected ||
                balance > split_balance ||
                (
                    balance == split_balance &&
                    task.id < split_task_id
                )
            ) {
                selected = true;
                split_balance = balance;
                split_task_index = task_index;
                split_task_id = task.id;
            }
        }
    }

    std::shared_ptr<const Model> model;
    std::size_t max_bucket_limit = 0;
    std::size_t max_candidate_check_limit = 0;
    std::size_t dominance_candidate_checks = 0;
    std::size_t max_bucket_size = 0;
    std::size_t hottest_bucket_size = 0;
    std::vector<std::size_t> hottest_bucket_visited_counts;
    bool triggered = false;
    bool refinement_exhausted = false;
    std::string trigger_reason;
    std::size_t split_task_index =
        std::numeric_limits<std::size_t>::max();
    std::string split_task_id;
    std::size_t split_balance = 0;
};

class VisitedLabelList {
  public:
    using Label = rcspp::Label<Composition>;
    using LabelPosition = std::list<Label*>::iterator;
    using VisitedKey = VisitedMask;

    explicit VisitedLabelList(std::shared_ptr<const Model> model = nullptr,
                              std::size_t subset_enumeration_limit = 10,
                              double dominance_epsilon = 1.0e-12,
                              double resource_epsilon = 1.0e-9,
                              std::shared_ptr<ProofQueuePotentialTrace> trace = nullptr,
                              std::shared_ptr<DssrPressureMonitor> dssr_pressure = nullptr)
        : model_(std::move(model)),
          subset_enumeration_limit_(subset_enumeration_limit),
          dominance_epsilon_(dominance_epsilon),
          resource_epsilon_(resource_epsilon),
          trace_(std::move(trace)),
          dssr_pressure_(std::move(dssr_pressure)) {}
    // AlgorithmParams only copies the empty prototype container. Runtime
    // containers are created through copy(), so iterator-bearing state is
    // never copied.
    VisitedLabelList(const VisitedLabelList& other)
        : model_(other.model_),
          subset_enumeration_limit_(other.subset_enumeration_limit_),
          dominance_epsilon_(other.dominance_epsilon_),
          resource_epsilon_(other.resource_epsilon_),
          trace_(other.trace_),
          dssr_pressure_(other.dssr_pressure_) {}
    VisitedLabelList& operator=(const VisitedLabelList&) = delete;

    [[nodiscard]] VisitedLabelList copy() const {
        return VisitedLabelList{model_, subset_enumeration_limit_, dominance_epsilon_,
                                resource_epsilon_, trace_, dssr_pressure_};
    }

    [[nodiscard]] const std::list<Label*>& get_labels() const { return labels_; }

    LabelPosition add_label(Label* label) {
        auto position = labels_.insert(labels_.end(), label);
        auto key = visited_key(*label);
        auto& bucket = buckets_[key];
        if (
            dssr_pressure_ != nullptr &&
            bucket.visited_counts == nullptr &&
            model_ != nullptr
        ) {
            bucket.visited_counts =
                std::make_unique<std::vector<std::size_t>>(
                    model_->tasks.size(),
                    0U
                );
        }
        bucket.labels.push_back(
            BucketEntry{.label = label, .position = position}
        );
        const auto& label_state = state(*label);
        if (bucket.visited_counts != nullptr) {
            for (
                std::size_t task_index = 0;
                task_index < bucket.visited_counts->size();
                ++task_index
            ) {
                if (visited(label_state, task_index)) {
                    ++bucket.visited_counts->at(task_index);
                }
            }
        }
        update_summary(&bucket, key, *label);
        max_bucket_size_ = std::max(max_bucket_size_, bucket.labels.size());
        if (dssr_pressure_ != nullptr) {
            assert(bucket.visited_counts != nullptr);
            dssr_pressure_->observe_bucket(
                bucket.labels.size(),
                *bucket.visited_counts
            );
        }
        return position;
    }

    void erase_label(const LabelPosition& position) {
        Label* label = *position;
        const auto key = visited_key(*label);
        auto bucket_it = buckets_.find(key);
        assert(bucket_it != buckets_.end());
        const auto entry_it = std::ranges::find(
            bucket_it->second.labels,
            label,
            &BucketEntry::label
        );
        assert(entry_it != bucket_it->second.labels.end());
        remove_bucket_entry(
            bucket_it,
            static_cast<std::size_t>(
                std::distance(bucket_it->second.labels.begin(), entry_it)
            ),
            true
        );
    }

    std::size_t remove_dominated_labels(const Label& label) {
        const auto key = visited_key(label);
        auto bucket_it = buckets_.find(key);
        if (bucket_it == buckets_.end()) {
            return 0;
        }
        std::size_t removed = 0;
        std::size_t index = 0;
        while (bucket_it != buckets_.end() && index < bucket_it->second.labels.size()) {
            Label* candidate = bucket_it->second.labels[index].label;
            if (&label == candidate) {
                ++index;
                continue;
            }
            record_dominance_candidate_check();
            if (label <= *candidate) {
                record_removal(label, *candidate);
                candidate->dominated = true;
                remove_bucket_entry(bucket_it, index, true);
                ++removed;
                bucket_it = buckets_.find(key);
            } else {
                ++index;
            }
            if (
                dssr_pressure_ != nullptr &&
                dssr_pressure_->triggered
            ) {
                break;
            }
        }
        return removed;
    }

    [[nodiscard]] bool is_dominated(const Label& label) const {
        record_exposure(label);
        const auto bucket_it = buckets_.find(visited_key(label));
        if (bucket_it != buckets_.end()) {
            for (const auto& entry : bucket_it->second.labels) {
                const auto* candidate = entry.label;
                if (&label == candidate) {
                    continue;
                }
                record_dominance_candidate_check();
                if (*candidate <= label) {
                    record_dominance(candidate, label);
                    return true;
                }
                if (
                    dssr_pressure_ != nullptr &&
                    dssr_pressure_->triggered
                ) {
                    return false;
                }
            }
        }
        if (model_ == nullptr || !model_->subset_dominance_enabled) {
            return false;
        }
        const auto& rhs = state(label);
        if (rhs.visited_count <= 1 ||
            rhs.visited_count > subset_enumeration_limit_) {
            return false;
        }
        std::vector<std::size_t> set_bits;
        set_bits.reserve(rhs.visited_count);
        for (std::size_t word = 0; word < rhs.visited.size(); ++word) {
            std::uint64_t value = rhs.visited[word];
            while (value != 0U) {
                const auto bit = static_cast<std::size_t>(std::countr_zero(value));
                set_bits.push_back(word * 64U + bit);
                value &= value - 1U;
            }
        }
        const std::size_t subset_count = std::size_t{1} << set_bits.size();
        const std::size_t full_mask = subset_count - 1U;
        VisitedKey key{};
        std::size_t previous_gray = 0U;
        for (std::size_t ordinal = 1; ordinal < subset_count; ++ordinal) {
            const std::size_t gray = ordinal ^ (ordinal >> 1U);
            const std::size_t changed = gray ^ previous_gray;
            const auto changed_index = static_cast<std::size_t>(std::countr_zero(changed));
            const auto task_index = set_bits[changed_index];
            const auto word = task_index / 64U;
            const auto bit = task_index % 64U;
            key[word] ^= std::uint64_t{1} << bit;
            previous_gray = gray;
            if (gray == full_mask) {
                continue;
            }
            ++subset_dominance_key_lookups_;
            const auto subset_bucket = buckets_.find(key);
            if (subset_bucket == buckets_.end()) {
                continue;
            }
            ++subset_dominance_nonempty_buckets_;
            const auto& bucket = subset_bucket->second;
            if (!summary_can_contain_dominator(bucket, rhs)) {
                ++subset_dominance_summary_skipped_buckets_;
                continue;
            }
            // The bucket key already proves the proper-subset relation.  Same-journey
            // compatibility depends only on the two visited masks, so audit it once per
            // bucket instead of once per candidate label.
            if (!branch_subset_dominance_compatible(
                    *model_,
                    state(*bucket.labels.front().label),
                    rhs
                )) {
                continue;
            }
            for (const auto& entry : bucket.labels) {
                const auto* candidate = entry.label;
                record_dominance_candidate_check();
                ++subset_dominance_candidate_checks_;
                if (known_subset_candidate_dominates(*candidate, label)) {
                    record_dominance(candidate, label);
                    ++subset_dominance_rejected_labels_;
                    return true;
                }
                if (
                    dssr_pressure_ != nullptr &&
                    dssr_pressure_->triggered
                ) {
                    return false;
                }
            }
        }
        return false;
    }

    void print_labels() const {
        if (!LOG_TRACE_ACTIVE()) {
            return;
        }
        for (const auto* label : labels_) {
            LOG_TRACE("  ", label, ": ", label->get_resource().to_string(), "\n");
        }
    }

    [[nodiscard]] std::size_t dominance_candidate_checks() const {
        return dominance_candidate_checks_;
    }
    [[nodiscard]] std::size_t max_bucket_size() const { return max_bucket_size_; }
    [[nodiscard]] std::size_t subset_dominance_candidate_checks() const {
        return subset_dominance_candidate_checks_;
    }
    [[nodiscard]] std::size_t subset_dominance_key_lookups() const {
        return subset_dominance_key_lookups_;
    }
    [[nodiscard]] std::size_t subset_dominance_nonempty_buckets() const {
        return subset_dominance_nonempty_buckets_;
    }
    [[nodiscard]] std::size_t subset_dominance_summary_skipped_buckets() const {
        return subset_dominance_summary_skipped_buckets_;
    }
    [[nodiscard]] std::size_t subset_dominance_rejected_labels() const {
        return subset_dominance_rejected_labels_;
    }

  private:
    void record_exposure(const Label& label) const {
        if (trace_ == nullptr) {
            return;
        }
        const auto& value = state(label);
        if (value.last_task_index < trace_->task_rows.size()) {
            ++trace_->task_rows[value.last_task_index].incoming_evaluated;
        }
        if (
            !ng_dssr_active(*model_) &&
            value.auxiliary.regular.last_model_arc_index <
                trace_->arc_rows.size()
        ) {
            ++trace_
                  ->arc_rows[
                      value.auxiliary.regular.last_model_arc_index
                  ]
                  .incoming_evaluated;
        }
    }

    void record_removal(
        const Label& winner,
        const Label& removed
    ) const {
        if (trace_ == nullptr) {
            return;
        }
        trace_->record_preference(
            winner,
            removed,
            *model_,
            LabelPreferenceKind::IncomingDominator);
        const auto& winner_state = state(winner);
        const auto& removed_state = state(removed);
        if (winner_state.last_task_index < trace_->task_rows.size()) {
            ++trace_->task_rows[winner_state.last_task_index]
                  .accepted_removed_existing;
        }
        if (removed_state.last_task_index < trace_->task_rows.size()) {
            ++trace_->task_rows[removed_state.last_task_index]
                  .removed_as_existing;
        }
        if (
            !ng_dssr_active(*model_) &&
            winner_state.auxiliary.regular.last_model_arc_index <
                trace_->arc_rows.size()
        ) {
            ++trace_
                  ->arc_rows[
                      winner_state.auxiliary.regular.last_model_arc_index
                  ]
                  .accepted_removed_existing;
        }
        if (
            !ng_dssr_active(*model_) &&
            removed_state.auxiliary.regular.last_model_arc_index <
                trace_->arc_rows.size()
        ) {
            ++trace_
                  ->arc_rows[
                      removed_state.auxiliary.regular.last_model_arc_index
                  ]
                  .removed_as_existing;
        }
    }

    void record_dominance(
        const Label* winner,
        const Label& rejected
    ) const {
        if (trace_ == nullptr) {
            return;
        }
        trace_->record_preference(
            *winner,
            rejected,
            *model_,
            LabelPreferenceKind::ExistingDominator);
        const auto& winner_state = state(*winner);
        const auto& rejected_state = state(rejected);
        if (winner_state.last_task_index < trace_->task_rows.size()) {
            ++trace_->task_rows[winner_state.last_task_index]
                  .existing_dominator_wins;
        }
        if (rejected_state.last_task_index < trace_->task_rows.size()) {
            ++trace_->task_rows[rejected_state.last_task_index]
                  .incoming_rejected;
        }
        if (
            !ng_dssr_active(*model_) &&
            winner_state.auxiliary.regular.last_model_arc_index <
                trace_->arc_rows.size()
        ) {
            ++trace_
                  ->arc_rows[
                      winner_state.auxiliary.regular.last_model_arc_index
                  ]
                  .existing_dominator_wins;
        }
        if (
            !ng_dssr_active(*model_) &&
            rejected_state.auxiliary.regular.last_model_arc_index <
                trace_->arc_rows.size()
        ) {
            ++trace_
                  ->arc_rows[
                      rejected_state.auxiliary.regular.last_model_arc_index
                  ]
                  .incoming_rejected;
        }
    }

    struct BucketEntry {
        Label* label = nullptr;
        LabelPosition position;
    };

    struct BucketSummary {
        double min_global_time = std::numeric_limits<double>::infinity();
        double min_sortie_demand = std::numeric_limits<double>::infinity();
        double min_sortie_energy = std::numeric_limits<double>::infinity();
        double min_sortie_shadow = std::numeric_limits<double>::infinity();
        std::size_t min_sortie_task_count = std::numeric_limits<std::size_t>::max();
        double min_reduced_cost = std::numeric_limits<double>::infinity();
    };

    struct Bucket {
        std::vector<BucketEntry> labels;
        // Only DSSR pressure refinement needs per-task visit counts.  Keeping
        // an empty vector object in every elementary P0 bucket cost 24 bytes
        // per visited-set key even though the data was never read.
        std::unique_ptr<std::vector<std::size_t>> visited_counts;
        // Subset dominance only enumerates keys up to the configured small
        // visited-set limit.  Allocate its optimistic summary only for those
        // keys instead of charging six scalars to every large exact bucket.
        std::unique_ptr<BucketSummary> summary;
    };

    static const State& state(const Label& label) {
        return label.get_resource()
            .template get_component<JourneyResource>(0)
            .get_value()
            .get_value()
            .state();
    }

    void record_dominance_candidate_check() const {
        ++dominance_candidate_checks_;
        if (dssr_pressure_ != nullptr) {
            dssr_pressure_->record_candidate_check();
        }
    }

    [[nodiscard]] VisitedKey visited_key(const Label& label) const {
        return dominance_visited_key(*model_, state(label));
    }

    void update_summary(
        Bucket* bucket,
        const VisitedKey& key,
        const Label& label
    ) const {
        if (
            model_ == nullptr ||
            !model_->subset_dominance_enabled
        ) {
            return;
        }
        std::size_t key_size = 0;
        for (const auto word : key) {
            key_size += std::popcount(word);
        }
        if (key_size > subset_enumeration_limit_) {
            return;
        }
        if (bucket->summary == nullptr) {
            bucket->summary = std::make_unique<BucketSummary>();
        }
        const auto& value = state(label);
        auto& summary = *bucket->summary;
        summary.min_global_time =
            std::min(summary.min_global_time, value.global_time);
        summary.min_sortie_demand =
            std::min(summary.min_sortie_demand, value.sortie_demand);
        summary.min_sortie_energy =
            std::min(summary.min_sortie_energy, value.sortie_energy);
        summary.min_sortie_shadow =
            std::min(summary.min_sortie_shadow, value.sortie_shadow);
        summary.min_sortie_task_count =
            std::min(
                summary.min_sortie_task_count,
                static_cast<std::size_t>(value.sortie_task_count)
            );
        summary.min_reduced_cost =
            std::min(summary.min_reduced_cost, reduced_cost(*model_, value));
    }

    [[nodiscard]] bool summary_can_contain_dominator(const Bucket& bucket,
                                                     const State& rhs) const {
        if (bucket.summary == nullptr) {
            return true;
        }
        const auto& summary = *bucket.summary;
        // These are independent optimistic minima.  A stale minimum after a label
        // deletion can only admit an unnecessary bucket scan; it can never suppress
        // a real dominator, so no exactness or certificate assumption is introduced.
        return summary.min_global_time <= rhs.global_time + resource_epsilon_ &&
               summary.min_sortie_demand <= rhs.sortie_demand + resource_epsilon_ &&
               summary.min_sortie_energy <= rhs.sortie_energy + resource_epsilon_ &&
               summary.min_sortie_shadow <= rhs.sortie_shadow + resource_epsilon_ &&
               summary.min_sortie_task_count <= rhs.sortie_task_count &&
               summary.min_reduced_cost <=
                   reduced_cost(*model_, rhs) + dominance_epsilon_;
    }

    [[nodiscard]] bool known_subset_candidate_dominates(const Label& lhs_label,
                                                         const Label& rhs_label) const {
        const auto& lhs = state(lhs_label);
        const auto& rhs = state(rhs_label);
        if (!lhs.valid || !rhs.valid || lhs.at_depot != rhs.at_depot ||
            !same_active_cut_state(lhs.cut_state, rhs.cut_state)) {
            return false;
        }
        if (!lhs.at_depot) {
            return false;
        }
        if (lhs.global_time > rhs.global_time + resource_epsilon_ ||
            lhs.task_visit_count > rhs.task_visit_count ||
            lhs.sortie_demand > rhs.sortie_demand + resource_epsilon_ ||
            lhs.sortie_energy > rhs.sortie_energy + resource_epsilon_ ||
            lhs.sortie_shadow > rhs.sortie_shadow + resource_epsilon_ ||
            lhs.sortie_task_count > rhs.sortie_task_count ||
            reduced_cost(*model_, lhs) >
                reduced_cost(*model_, rhs) + dominance_epsilon_) {
            return false;
        }
        // JourneyResource is now the only component, and the checks above are
        // exactly its component-wise dominance predicate.
        return true;
    }

    using BucketMap =
        std::unordered_map<VisitedKey, Bucket, VisitedKeyHash>;

    void remove_bucket_entry(
        const BucketMap::iterator& bucket_it,
        std::size_t index,
        bool erase_from_master
    ) {
        auto& bucket = bucket_it->second;
        assert(index < bucket.labels.size());
        const auto removed = bucket.labels[index];
        assert(removed.label != nullptr);
        const auto& label_state = state(*removed.label);
        if (bucket.visited_counts != nullptr) {
            for (
                std::size_t task_index = 0;
                task_index < bucket.visited_counts->size();
                ++task_index
            ) {
                if (visited(label_state, task_index)) {
                    assert(bucket.visited_counts->at(task_index) > 0U);
                    --bucket.visited_counts->at(task_index);
                }
            }
        }
        bucket.labels[index] = bucket.labels.back();
        bucket.labels.pop_back();
        if (bucket.labels.empty()) {
            buckets_.erase(bucket_it);
        }
        if (erase_from_master) {
            labels_.erase(removed.position);
        }
    }

    std::list<Label*> labels_;
    BucketMap buckets_;
    mutable std::size_t dominance_candidate_checks_ = 0;
    mutable std::size_t subset_dominance_key_lookups_ = 0;
    mutable std::size_t subset_dominance_nonempty_buckets_ = 0;
    mutable std::size_t subset_dominance_summary_skipped_buckets_ = 0;
    mutable std::size_t subset_dominance_candidate_checks_ = 0;
    mutable std::size_t subset_dominance_rejected_labels_ = 0;
    std::size_t max_bucket_size_ = 0;
    std::shared_ptr<const Model> model_;
    std::size_t subset_enumeration_limit_ = 10;
    double dominance_epsilon_ = 1.0e-12;
    double resource_epsilon_ = 1.0e-9;
    std::shared_ptr<ProofQueuePotentialTrace> trace_;
    std::shared_ptr<DssrPressureMonitor> dssr_pressure_;
};

using LabelList = VisitedLabelList;

class AuditedBestFirstDominance final
    : public rcspp::DominanceAlgorithm<Composition, LabelList> {
  public:
    using Base = rcspp::DominanceAlgorithm<Composition, LabelList>;
    using Label = rcspp::Label<Composition>;
    using Pair = rcspp::LabelIteratorPair<Composition>;
    using Clock = std::chrono::steady_clock;

    AuditedBestFirstDominance(rcspp::ResourceFactory<Composition>* factory,
                              rcspp::AlgorithmParams<LabelList> params,
                              std::shared_ptr<const Model> model,
                              ProofQueuePolicy proof_queue_policy,
                              double proof_queue_guidance_bucket_width,
                              double negative_epsilon,
                              std::shared_ptr<ProofQueuePotentialTrace> trace,
                              FrontierProbeConfig frontier_probe,
                              CounterfactualPrefixConfig counterfactual_prefix)
        : Base(factory, std::move(params)),
          model_(std::move(model)),
          proof_queue_policy_(proof_queue_policy),
          proof_queue_guidance_bucket_width_(
              proof_queue_guidance_bucket_width),
          negative_epsilon_(std::abs(negative_epsilon)),
          trace_(std::move(trace)),
          frontier_probe_config_(std::move(frontier_probe)),
          counterfactual_prefix_config_(std::move(counterfactual_prefix)),
          guidance_stats_(std::make_shared<GuidanceStats>()),
          unprocessed_experimental_(
              GreaterCachedKey{guidance_stats_}) {
        const auto& observation_boundaries =
            frontier_probe_config_.observation_boundaries;
        if (!observation_boundaries.empty()) {
            if (frontier_probe_config_.mode == FrontierProbeMode::Disabled ||
                observation_boundaries.front() == 0U ||
                !std::ranges::is_sorted(observation_boundaries) ||
                std::ranges::adjacent_find(observation_boundaries) !=
                    observation_boundaries.end() ||
                observation_boundaries.back() >
                    frontier_probe_config_.processed_label_boundary) {
                throw std::invalid_argument(
                    "frontier observation boundaries require an enabled "
                    "probe and must be strictly increasing, positive, and "
                    "not exceed the decision boundary");
            }
        }
        frontier_probe_telemetry_.enabled =
            frontier_probe_config_.mode != FrontierProbeMode::Disabled;
        frontier_probe_telemetry_.boundary =
            frontier_probe_config_.processed_label_boundary;
        frontier_probe_telemetry_.trial_pop_budget =
            frontier_probe_config_.trial_pop_budget;
        frontier_probe_telemetry_.observation_boundaries =
            frontier_probe_config_.observation_boundaries;
        frontier_probe_telemetry_.context_features =
            frontier_probe_config_.context_features;
        switch (frontier_probe_config_.mode) {
            case FrontierProbeMode::Disabled:
                frontier_probe_telemetry_.mode = "disabled";
                break;
            case FrontierProbeMode::CollectForceQ0:
                frontier_probe_telemetry_.mode = "collect_force_q0";
                break;
            case FrontierProbeMode::ForceQD1:
                frontier_probe_telemetry_.mode = "force_qd1";
                break;
            case FrontierProbeMode::Learned:
                frontier_probe_telemetry_.mode = "learned";
                break;
            case FrontierProbeMode::CollectTrial:
                frontier_probe_telemetry_.mode = "collect_trial";
                break;
            case FrontierProbeMode::ForceTrialContinue:
                frontier_probe_telemetry_.mode = "force_trial_continue";
                break;
            case FrontierProbeMode::ForceTrialRevert:
                frontier_probe_telemetry_.mode = "force_trial_revert";
                break;
            case FrontierProbeMode::LearnedAfterTrial:
                frontier_probe_telemetry_.mode = "learned_after_trial";
                break;
        }
        if (temporal_trial_mode()) {
            if (frontier_probe_config_.trial_pop_budget == 0U) {
                throw std::invalid_argument(
                    "temporal frontier trial requires a positive pop budget");
            }
            if (frontier_probe_config_.problem_scale != 30U &&
                frontier_probe_config_.problem_scale != 50U) {
                throw std::invalid_argument(
                    "temporal frontier trial is authorized only for scale30/50");
            }
            if (!frontier_probe_config_.require_root_cg ||
                !frontier_probe_config_.fail_closed_on_ood) {
                throw std::invalid_argument(
                    "temporal frontier trial requires root-only and "
                    "fail-closed OOD policies");
            }
            if (frontier_probe_config_.require_root_cg &&
                frontier_probe_config_.pricing_lifecycle != "root_cg") {
                throw std::invalid_argument(
                    "temporal frontier trial is authorized only for root_cg");
            }
            if (frontier_probe_config_.mode ==
                FrontierProbeMode::LearnedAfterTrial) {
                const auto is_sha256 = [](const std::string& value) {
                    return value.size() == 64U && std::ranges::all_of(
                        value, [](const unsigned char item) {
                            return std::isxdigit(item) != 0;
                        });
                };
                if (!is_sha256(frontier_probe_config_.manifest_sha256) ||
                    !is_sha256(frontier_probe_config_.bundle_file_sha256) ||
                    !is_sha256(
                        frontier_probe_config_.temporal_bundle.bundle_sha256)) {
                    throw std::invalid_argument(
                        "learned temporal trial requires immutable manifest, "
                        "bundle-file, and canonical bundle bindings");
                }
            }
        }
        auto& counterfactual = counterfactual_prefix_telemetry_;
        counterfactual.enabled =
            counterfactual_prefix_config_.mode !=
            CounterfactualPrefixMode::Disabled;
        counterfactual.processed_label_boundary =
            counterfactual_prefix_config_.processed_label_boundary;
        counterfactual.rollout_checkpoints =
            counterfactual_prefix_config_.rollout_checkpoints;
        counterfactual.maximum_rollout_budget =
            counterfactual_prefix_config_.maximum_rollout_budget;
        counterfactual.public_routes_forbidden =
            counterfactual_prefix_config_.public_routes_forbidden;
        counterfactual.certificate_forbidden =
            counterfactual_prefix_config_.certificate_forbidden;
        switch (counterfactual_prefix_config_.mode) {
            case CounterfactualPrefixMode::Disabled:
                counterfactual.mode = "disabled";
                break;
            case CounterfactualPrefixMode::Q0Prefix:
                counterfactual.mode = "counterfactual_q0_prefix";
                break;
            case CounterfactualPrefixMode::QD1Prefix:
                counterfactual.mode = "counterfactual_qd1_prefix";
                break;
        }
    }

    [[nodiscard]] std::size_t extended_labels() const { return this->num_extended_labels_; }
    [[nodiscard]] std::size_t processed_labels() const { return processed_labels_; }
    [[nodiscard]] std::size_t dominated_labels() const { return this->nb_dominated_labels_; }
    [[nodiscard]] bool memory_pressure_triggered() const {
        return this->memory_pressure_triggered_;
    }
    [[nodiscard]] std::size_t dominance_candidate_checks() const {
        std::size_t total = 0;
        for (const auto& labels : this->non_dominated_labels_by_node_pos_) {
            total += labels.dominance_candidate_checks();
        }
        return total;
    }
    [[nodiscard]] std::size_t max_visited_bucket_size() const {
        std::size_t value = 0;
        for (const auto& labels : this->non_dominated_labels_by_node_pos_) {
            value = std::max(value, labels.max_bucket_size());
        }
        return value;
    }
    [[nodiscard]] std::size_t subset_dominance_candidate_checks() const {
        std::size_t total = 0;
        for (const auto& labels : this->non_dominated_labels_by_node_pos_) {
            total += labels.subset_dominance_candidate_checks();
        }
        return total;
    }
    [[nodiscard]] std::size_t subset_dominance_key_lookups() const {
        std::size_t total = 0;
        for (const auto& labels : this->non_dominated_labels_by_node_pos_) {
            total += labels.subset_dominance_key_lookups();
        }
        return total;
    }
    [[nodiscard]] std::size_t subset_dominance_nonempty_buckets() const {
        std::size_t total = 0;
        for (const auto& labels : this->non_dominated_labels_by_node_pos_) {
            total += labels.subset_dominance_nonempty_buckets();
        }
        return total;
    }
    [[nodiscard]] std::size_t subset_dominance_summary_skipped_buckets() const {
        std::size_t total = 0;
        for (const auto& labels : this->non_dominated_labels_by_node_pos_) {
            total += labels.subset_dominance_summary_skipped_buckets();
        }
        return total;
    }
    [[nodiscard]] std::size_t subset_dominance_rejected_labels() const {
        std::size_t total = 0;
        for (const auto& labels : this->non_dominated_labels_by_node_pos_) {
            total += labels.subset_dominance_rejected_labels();
        }
        return total;
    }
    [[nodiscard]] double extension_wall_time_seconds() const {
        return this->total_full_extend_time_.elapsed_seconds();
    }
    [[nodiscard]] double dominance_wall_time_seconds() const {
        return this->total_update_non_dom_time_.elapsed_seconds();
    }
    void begin_best_reduced_cost_trace(Clock::time_point started, bool enabled) {
        trace_started_ = started;
        counterfactual_request_started_ = started;
        counterfactual_timing_started_ = true;
        trace_enabled_ = enabled;
        best_reduced_cost_ = std::numeric_limits<double>::infinity();
        best_reduced_cost_event_count_total_ = 0;
        best_reduced_cost_events_.clear();
    }
    [[nodiscard]] const std::vector<BestReducedCostEvent>& best_reduced_cost_events() const {
        return best_reduced_cost_events_;
    }
    [[nodiscard]] std::size_t best_reduced_cost_event_count_total() const {
        return best_reduced_cost_event_count_total_;
    }
    [[nodiscard]] bool best_reduced_cost_events_truncated() const {
        return best_reduced_cost_event_count_total_ > best_reduced_cost_events_.size();
    }
    [[nodiscard]] std::size_t label_state_scored_count() const {
        return guidance_stats_->label_state_scored_count;
    }
    [[nodiscard]] std::size_t guidance_nonzero_score_count() const {
        return guidance_stats_->nonzero_score_count;
    }
    [[nodiscard]] std::size_t guidance_ordering_decision_count() const {
        return guidance_stats_->ordering_decision_count;
    }
    [[nodiscard]] std::size_t guidance_reordered_label_hash_count() const {
        return guidance_stats_->reordered_label_hashes.count();
    }
    [[nodiscard]] std::size_t guidance_bucket_hash_count() const {
        return guidance_stats_->bucket_hashes.count();
    }
    [[nodiscard]] double label_state_scoring_estimated_wall_seconds() const {
        if (guidance_stats_->scoring_sample_count == 0U) {
            return 0.0;
        }
        return guidance_stats_->scoring_sample_wall_seconds *
               static_cast<double>(guidance_stats_->label_state_scored_count) /
               static_cast<double>(guidance_stats_->scoring_sample_count);
    }
    [[nodiscard]] double first_true_negative_wall_time_seconds() const {
        return first_true_negative_wall_time_seconds_;
    }
    [[nodiscard]] std::size_t labels_processed_before_first_true_negative() const {
        return labels_processed_before_first_true_negative_;
    }
    [[nodiscard]] const FrontierProbeTelemetry& frontier_probe_telemetry() const {
        return frontier_probe_telemetry_;
    }
    [[nodiscard]] const CounterfactualPrefixTelemetry&
    counterfactual_prefix_telemetry() const {
        return counterfactual_prefix_telemetry_;
    }
    void release_request_memory() { release_label_memory(); }

  private:
    [[nodiscard]] bool temporal_trial_mode() const {
        return frontier_probe_config_.mode == FrontierProbeMode::CollectTrial ||
               frontier_probe_config_.mode ==
                   FrontierProbeMode::ForceTrialContinue ||
               frontier_probe_config_.mode ==
                   FrontierProbeMode::ForceTrialRevert ||
               frontier_probe_config_.mode ==
                   FrontierProbeMode::LearnedAfterTrial;
    }
    void extract_solution(const Label& end_label) override {
        const auto size_before = this->solutions_.size();
        Base::extract_solution(end_label);
        if (this->solutions_.size() == size_before) {
            return;
        }
        const double reduced_cost = end_label.get_cost();
        const auto elapsed =
            std::chrono::duration<double>(Clock::now() - trace_started_).count();
        const bool true_negative =
            reduced_cost < -negative_epsilon_;
        if (
            true_negative &&
            !std::isfinite(first_true_negative_wall_time_seconds_)
        ) {
            first_true_negative_wall_time_seconds_ = std::max(0.0, elapsed);
            labels_processed_before_first_true_negative_ = processed_labels_;
        }
        if (trace_ != nullptr && true_negative) {
            trace_->record_negative_witness(
                end_label,
                *model_,
                reduced_cost,
                this->solutions_.size() - 1U,
                elapsed);
        }
        if (!trace_enabled_) {
            return;
        }
        constexpr double improvement_epsilon = 1.0e-12;
        if (!(reduced_cost < best_reduced_cost_ - improvement_epsilon)) {
            return;
        }
        best_reduced_cost_ = reduced_cost;
        ++best_reduced_cost_event_count_total_;
        if (best_reduced_cost_events_.size() >= max_best_reduced_cost_events_) {
            return;
        }
        best_reduced_cost_events_.push_back(BestReducedCostEvent{
            .elapsed_seconds = std::max(0.0, elapsed),
            .extended_labels = this->num_extended_labels_,
            .solution_count = this->solutions_.size(),
            .discovered_reduced_cost = reduced_cost,
            .best_reduced_cost = best_reduced_cost_,
        });
    }

    struct GreaterCost {
        bool operator()(const Pair& lhs, const Pair& rhs) const {
            const auto& lhs_state = lhs.first->get_resource()
                                        .template get_component<JourneyResource>(0)
                                        .get_value()
                                        .get_value()
                                        .state();
            const auto& rhs_state = rhs.first->get_resource()
                                        .template get_component<JourneyResource>(0)
                                        .get_value()
                                        .get_value()
                                        .state();
            const bool lhs_can_terminate =
                lhs_state.at_depot && lhs_state.task_visit_count > 0;
            const bool rhs_can_terminate =
                rhs_state.at_depot && rhs_state.task_visit_count > 0;
            if (lhs_can_terminate != rhs_can_terminate) {
                return !lhs_can_terminate;
            }
            constexpr double guidance_epsilon = 1.0e-12;
            if (std::abs(lhs_state.guidance_score - rhs_state.guidance_score) >
                guidance_epsilon) {
                // Larger guidance score is expanded first.  With guidance off
                // all scores remain exactly zero and the historical P0
                // comparator is unchanged.
                return lhs_state.guidance_score < rhs_state.guidance_score;
            }
            return lhs.first->get_cost() > rhs.first->get_cost();
        }
    };

    struct CachedQueueEntry {
        Pair value;
        bool can_terminate = false;
        double primary_key = 0.0;
        double secondary_key = 0.0;
        std::int64_t reduced_cost_bucket = 0;
        double guidance_score = 0.0;
        double partial_cost = 0.0;
        std::uint64_t creation_sequence_id = 0;
    };

    struct GuidanceStats {
        std::size_t label_state_scored_count = 0;
        std::size_t nonzero_score_count = 0;
        std::size_t ordering_decision_count = 0;
        std::size_t scoring_sample_count = 0;
        double scoring_sample_wall_seconds = 0.0;
        std::bitset<4096> bucket_hashes;
        std::bitset<65536> reordered_label_hashes;
    };

    struct GreaterCachedKey {
        std::shared_ptr<GuidanceStats> stats;

        bool operator()(
            const CachedQueueEntry& lhs,
            const CachedQueueEntry& rhs
        ) const {
            if (lhs.can_terminate != rhs.can_terminate) {
                return !lhs.can_terminate;
            }
            constexpr double key_epsilon = 1.0e-12;
            if (
                std::abs(lhs.primary_key - rhs.primary_key) >
                key_epsilon
            ) {
                return lhs.primary_key > rhs.primary_key;
            }
            if (
                std::abs(lhs.secondary_key - rhs.secondary_key) >
                key_epsilon
            ) {
                return lhs.secondary_key > rhs.secondary_key;
            }
            if (lhs.reduced_cost_bucket != rhs.reduced_cost_bucket) {
                return lhs.reduced_cost_bucket > rhs.reduced_cost_bucket;
            }
            if (
                std::abs(lhs.guidance_score - rhs.guidance_score) >
                key_epsilon
            ) {
                const bool guided_lhs_after =
                    lhs.guidance_score < rhs.guidance_score;
                const bool q0_lhs_after =
                    std::abs(lhs.partial_cost - rhs.partial_cost) >
                            key_epsilon
                        ? lhs.partial_cost > rhs.partial_cost
                        : lhs.creation_sequence_id >
                              rhs.creation_sequence_id;
                if (stats != nullptr && guided_lhs_after != q0_lhs_after) {
                    ++stats->ordering_decision_count;
                    stats->reordered_label_hashes.set(
                        lhs.creation_sequence_id %
                        stats->reordered_label_hashes.size());
                    stats->reordered_label_hashes.set(
                        rhs.creation_sequence_id %
                        stats->reordered_label_hashes.size());
                }
                return guided_lhs_after;
            }
            if (
                std::abs(lhs.partial_cost - rhs.partial_cost) >
                key_epsilon
            ) {
                return lhs.partial_cost > rhs.partial_cost;
            }
            return (
                lhs.creation_sequence_id >
                rhs.creation_sequence_id
            );
        }
    };

    struct FrontierLabelRecord {
        Pair value;
        std::uint64_t creation_sequence_id = 0;
        double partial_cost = 0.0;
        std::size_t depth_bin = 0;
        std::size_t rc_bin = 0;
        std::size_t cell = 0;
        bool terminal = false;
        std::size_t visited_count = 0;
        std::size_t last_task_index = std::numeric_limits<std::size_t>::max();
        std::size_t q0_rank = 0;
        std::size_t qd1_rank = 0;
        std::uint64_t dominance_surface_hash = 0;
    };

    static std::uint64_t frontier_mix(std::uint64_t value) {
        value += 0x9e3779b97f4a7c15ULL;
        value = (value ^ (value >> 30U)) * 0xbf58476d1ce4e5b9ULL;
        value = (value ^ (value >> 27U)) * 0x94d049bb133111ebULL;
        return value ^ (value >> 31U);
    }

    static std::size_t frontier_depth_bin(
        std::size_t visited_count,
        std::size_t scale
    ) {
        const double value = static_cast<double>(visited_count) /
                             static_cast<double>(std::max<std::size_t>(1U, scale));
        constexpr std::array<double, 7> limits{
            0.05, 0.10, 0.20, 0.30, 0.40, 0.55, 0.75};
        return static_cast<std::size_t>(
            std::lower_bound(limits.begin(), limits.end(), value) - limits.begin());
    }

    static double frontier_mean(const std::vector<double>& values) {
        return values.empty()
                   ? 0.0
                   : std::accumulate(values.begin(), values.end(), 0.0) /
                         static_cast<double>(values.size());
    }

    static double frontier_std(
        const std::vector<double>& values,
        double mean
    ) {
        if (values.empty()) {
            return 0.0;
        }
        double value = 0.0;
        for (const double item : values) {
            value += (item - mean) * (item - mean);
        }
        return std::sqrt(value / static_cast<double>(values.size()));
    }

    std::vector<FrontierLabelRecord> frontier_records() const {
        std::vector<FrontierLabelRecord> records;
        auto append_record = [&](const Pair& value, std::uint64_t creation_id) {
            const auto& state = value.first->get_resource()
                                    .template get_component<JourneyResource>(0)
                                    .get_value()
                                    .get_value()
                                    .state();
            std::uint64_t surface_hash = frontier_mix(
                state.cut_state.packed_overlap ^
                (state.at_depot ? 0xd3f04a5aULL : 0x19b87c61ULL));
            for (const auto word : dominance_visited_key(*model_, state)) {
                surface_hash ^= frontier_mix(word + surface_hash);
            }
            surface_hash ^= frontier_mix(
                static_cast<std::uint64_t>(state.last_task_index));
            records.push_back(FrontierLabelRecord{
                .value = value,
                .creation_sequence_id = creation_id,
                .partial_cost = value.first->get_cost(),
                .terminal = state.at_depot && state.task_visit_count > 0,
                .visited_count = state.visited_count,
                .last_task_index = state.last_task_index,
                .dominance_surface_hash = surface_hash,
            });
        };
        if (proof_queue_policy_ == ProofQueuePolicy::Q0PartialCost) {
            auto queue = unprocessed_q0_;
            records.reserve(queue.size());
            while (!queue.empty()) {
                const auto value = queue.top();
                queue.pop();
                const auto found = creation_sequence_ids_.find(value.first);
                if (found == creation_sequence_ids_.end()) {
                    throw std::runtime_error(
                        "frontier creation sequence binding missing");
                }
                append_record(value, found->second);
            }
        } else {
            auto queue = unprocessed_experimental_;
            records.reserve(queue.size());
            while (!queue.empty()) {
                const auto entry = queue.top();
                queue.pop();
                append_record(entry.value, entry.creation_sequence_id);
            }
        }
        std::vector<std::size_t> order(records.size());
        std::iota(order.begin(), order.end(), 0U);
        std::ranges::sort(order, [&records](std::size_t lhs, std::size_t rhs) {
            return std::tie(
                       records[lhs].partial_cost,
                       records[lhs].creation_sequence_id) <
                   std::tie(
                       records[rhs].partial_cost,
                       records[rhs].creation_sequence_id);
        });
        for (std::size_t rank = 0; rank < order.size(); ++rank) {
            auto& record = records[order[rank]];
            record.q0_rank = rank;
            record.rc_bin = std::min<std::size_t>(
                7U, (8U * rank) / std::max<std::size_t>(1U, order.size()));
            record.depth_bin = frontier_depth_bin(
                record.visited_count, model_->tasks.size());
            record.cell = record.depth_bin * 8U + record.rc_bin;
        }
        std::ranges::sort(order, [&records](std::size_t lhs, std::size_t rhs) {
            return std::tuple{
                       !records[lhs].terminal,
                       std::numeric_limits<std::size_t>::max() -
                           records[lhs].visited_count,
                       records[lhs].partial_cost,
                       records[lhs].creation_sequence_id} <
                   std::tuple{
                       !records[rhs].terminal,
                       std::numeric_limits<std::size_t>::max() -
                           records[rhs].visited_count,
                       records[rhs].partial_cost,
                       records[rhs].creation_sequence_id};
        });
        for (std::size_t rank = 0; rank < order.size(); ++rank) {
            records[order[rank]].qd1_rank = rank;
        }
        return records;
    }

    CounterfactualFrontierGraph build_counterfactual_label_graph() const {
        const auto started = Clock::now();
        auto records = frontier_records();
        CounterfactualFrontierGraph graph;
        graph.frontier_size = records.size();
        if (records.empty()) {
            graph.build_wall_seconds =
                std::chrono::duration<double>(Clock::now() - started).count();
            return graph;
        }

        const auto cap = std::min(
            counterfactual_prefix_config_.label_sample_cap,
            kCounterfactualLabelSampleCap);
        std::unordered_set<std::size_t> selected;
        selected.reserve(cap);
        auto add_family = [&](std::vector<std::size_t> candidates,
                              std::size_t family_cap,
                              std::size_t* family_count,
                              bool hash_order) {
            if (hash_order) {
                std::ranges::sort(candidates, [&](std::size_t lhs, std::size_t rhs) {
                    return std::tuple{
                               frontier_mix(
                                   records[lhs].creation_sequence_id ^
                                   counterfactual_prefix_config_.sampling_seed),
                               records[lhs].creation_sequence_id} <
                           std::tuple{
                               frontier_mix(
                                   records[rhs].creation_sequence_id ^
                                   counterfactual_prefix_config_.sampling_seed),
                               records[rhs].creation_sequence_id};
                });
            }
            std::size_t accepted = 0;
            for (const auto index : candidates) {
                if (selected.size() >= cap || accepted >= family_cap) {
                    break;
                }
                if (selected.insert(index).second) {
                    ++accepted;
                }
            }
            *family_count += accepted;
        };

        std::vector<std::size_t> terminal;
        std::vector<std::size_t> q0(records.size());
        std::vector<std::size_t> qd1(records.size());
        std::vector<std::size_t> deepest(records.size());
        std::iota(q0.begin(), q0.end(), 0U);
        qd1 = q0;
        deepest = q0;
        for (std::size_t index = 0; index < records.size(); ++index) {
            if (records[index].terminal) {
                terminal.push_back(index);
            }
        }
        std::ranges::sort(q0, [&](std::size_t lhs, std::size_t rhs) {
            return std::tuple{
                       !records[lhs].terminal,
                       records[lhs].partial_cost,
                       records[lhs].creation_sequence_id} <
                   std::tuple{
                       !records[rhs].terminal,
                       records[rhs].partial_cost,
                       records[rhs].creation_sequence_id};
        });
        for (std::size_t rank = 0; rank < q0.size(); ++rank) {
            records[q0[rank]].q0_rank = rank;
        }
        std::ranges::sort(qd1, [&](std::size_t lhs, std::size_t rhs) {
            return std::tuple{
                       !records[lhs].terminal,
                       std::numeric_limits<std::size_t>::max() -
                           records[lhs].visited_count,
                       records[lhs].partial_cost,
                       records[lhs].creation_sequence_id} <
                   std::tuple{
                       !records[rhs].terminal,
                       std::numeric_limits<std::size_t>::max() -
                           records[rhs].visited_count,
                       records[rhs].partial_cost,
                       records[rhs].creation_sequence_id};
        });
        for (std::size_t rank = 0; rank < qd1.size(); ++rank) {
            records[qd1[rank]].qd1_rank = rank;
        }
        std::ranges::sort(deepest, [&](std::size_t lhs, std::size_t rhs) {
            return std::tuple{
                       std::numeric_limits<std::size_t>::max() -
                           records[lhs].visited_count,
                       records[lhs].partial_cost,
                       records[lhs].creation_sequence_id} <
                   std::tuple{
                       std::numeric_limits<std::size_t>::max() -
                           records[rhs].visited_count,
                       records[rhs].partial_cost,
                       records[rhs].creation_sequence_id};
        });
        add_family(
            std::move(terminal), 32U, &graph.terminal_family_count, true);
        add_family(q0, 32U, &graph.q0_family_count, false);
        add_family(qd1, 32U, &graph.qd1_family_count, false);
        add_family(deepest, 32U, &graph.deepest_family_count, false);

        std::array<std::vector<std::size_t>, kFrontierNodeCount> cells;
        for (std::size_t index = 0; index < records.size(); ++index) {
            cells[records[index].cell].push_back(index);
        }
        for (auto& cell : cells) {
            if (cell.empty()) {
                continue;
            }
            add_family(
                std::move(cell), 2U, &graph.depth_rc_family_count, true);
        }
        std::vector<std::size_t> remainder(records.size());
        std::iota(remainder.begin(), remainder.end(), 0U);
        add_family(
            std::move(remainder), cap, &graph.bottom_k_family_count, true);

        std::vector<std::size_t> sample(selected.begin(), selected.end());
        std::ranges::sort(sample, [&](std::size_t lhs, std::size_t rhs) {
            return records[lhs].creation_sequence_id <
                   records[rhs].creation_sequence_id;
        });
        graph.sampled_label_count = sample.size();
        graph.label_nodes.reserve(sample.size());
        std::unordered_map<const Label*, std::uint64_t> active_ids;
        active_ids.reserve(records.size());
        for (const auto& record : records) {
            active_ids.emplace(record.value.first, record.creation_sequence_id);
        }
        std::unordered_map<std::uint64_t, std::size_t> sample_index;
        sample_index.reserve(sample.size());
        const double count_scale = static_cast<double>(records.size());
        const double creation_scale = static_cast<double>(
            std::max<std::uint64_t>(1U, next_creation_sequence_id_));
        for (const auto record_index : sample) {
            const auto& record = records[record_index];
            const auto& state = record.value.first->get_resource()
                                    .template get_component<JourneyResource>(0)
                                    .get_value()
                                    .get_value()
                                    .state();
            auto features = std::array<double,
                kCounterfactualLabelNodeFeatureCount>{};
            const auto label_features = label_state_features(
                *model_, state, record.partial_cost);
            std::copy(
                label_features.begin(), label_features.end(), features.begin());
            features[15] = record.terminal ? 1.0 : 0.0;
            features[16] = static_cast<double>(
                next_creation_sequence_id_ - 1U -
                std::min(
                    next_creation_sequence_id_ - 1U,
                    record.creation_sequence_id)) / creation_scale;
            features[17] = static_cast<double>(record.q0_rank) /
                           std::max(1.0, count_scale - 1.0);
            features[18] = static_cast<double>(record.qd1_rank) /
                           std::max(1.0, count_scale - 1.0);
            features[19] = features[18] - features[17];
            features[20] = record.last_task_index < model_->tasks.size()
                               ? static_cast<double>(record.last_task_index + 1U) /
                                     static_cast<double>(model_->tasks.size())
                               : 0.0;
            features[21] = record.last_task_index < model_->tasks.size()
                               ? 1.0
                               : 0.0;
            std::uint64_t parent_id =
                std::numeric_limits<std::uint64_t>::max();
            const auto parent = active_ids.find(record.value.first->prev_label);
            if (parent != active_ids.end()) {
                parent_id = parent->second;
            }
            features[23] = branch_terminal_feasible(*model_, state) ? 1.0 : 0.0;
            sample_index.emplace(
                record.creation_sequence_id, graph.label_nodes.size());
            graph.label_nodes.push_back(CounterfactualLabelNode{
                .creation_sequence_id = record.creation_sequence_id,
                .parent_creation_sequence_id = parent_id,
                .last_task_index = record.last_task_index,
                .depth_rc_cell = record.cell,
                .dominance_surface_hash = record.dominance_surface_hash,
                .features = features,
            });
        }
        for (auto& node : graph.label_nodes) {
            node.features[22] = sample_index.contains(
                                    node.parent_creation_sequence_id)
                                    ? 1.0
                                    : 0.0;
        }

        struct EdgeKey {
            std::size_t source = 0;
            std::size_t target = 0;
            std::size_t type = 0;
            auto operator<=>(const EdgeKey&) const = default;
        };
        std::map<EdgeKey, std::size_t> edges;
        for (std::size_t index = 0; index < graph.label_nodes.size(); ++index) {
            edges[{index, index, 0U}] = 1U;
        }
        for (std::size_t child = 0; child < graph.label_nodes.size(); ++child) {
            const auto found = sample_index.find(
                graph.label_nodes[child].parent_creation_sequence_id);
            if (found == sample_index.end()) {
                continue;
            }
            edges[{found->second, child, 1U}] = 1U;
            edges[{child, found->second, 2U}] = 1U;
        }
        std::map<std::uint64_t, std::vector<std::size_t>> surfaces;
        for (std::size_t index = 0; index < graph.label_nodes.size(); ++index) {
            surfaces[graph.label_nodes[index].dominance_surface_hash]
                .push_back(index);
        }
        for (auto& [surface, members] : surfaces) {
            static_cast<void>(surface);
            std::ranges::sort(members, [&](std::size_t lhs, std::size_t rhs) {
                return std::tie(
                           graph.label_nodes[lhs].features[14],
                           graph.label_nodes[lhs].creation_sequence_id) <
                       std::tie(
                           graph.label_nodes[rhs].features[14],
                           graph.label_nodes[rhs].creation_sequence_id);
            });
            for (std::size_t index = 1; index < members.size(); ++index) {
                edges[{members[index - 1U], members[index], 3U}] = 1U;
                edges[{members[index], members[index - 1U], 3U}] = 1U;
            }
        }
        graph.label_edges.reserve(edges.size());
        for (const auto& [key, count] : edges) {
            CounterfactualLabelEdge edge;
            edge.source = key.source;
            edge.target = key.target;
            edge.features[key.type] = 1.0;
            edge.features[4] = std::log1p(static_cast<double>(count));
            edge.features[5] = graph.label_nodes[key.target].features[0] -
                               graph.label_nodes[key.source].features[0];
            edge.features[6] = graph.label_nodes[key.target].features[14] -
                               graph.label_nodes[key.source].features[14];
            edge.features[7] =
                graph.label_nodes[key.source].features[15] ==
                        graph.label_nodes[key.target].features[15]
                    ? 1.0
                    : 0.0;
            graph.label_edges.push_back(edge);
        }

        std::vector<double> rc;
        std::vector<double> depth;
        std::size_t terminal_count = 0;
        rc.reserve(records.size());
        depth.reserve(records.size());
        for (const auto& record : records) {
            rc.push_back(record.partial_cost / model_->absolute_dual_sum);
            depth.push_back(
                static_cast<double>(record.visited_count) /
                static_cast<double>(
                    std::max<std::size_t>(1U, model_->tasks.size())));
            terminal_count += record.terminal ? 1U : 0U;
        }
        graph.context_features = counterfactual_prefix_config_.context_features;
        auto& context = graph.context_features;
        const auto rc_mean = frontier_mean(rc);
        const auto depth_mean = frontier_mean(depth);
        context[0] = std::log1p(static_cast<double>(model_->tasks.size()));
        context[1] = std::log1p(static_cast<double>(records.size()));
        context[2] = static_cast<double>(terminal_count) / count_scale;
        context[3] = rc_mean;
        context[4] = *std::ranges::min_element(rc);
        context[5] = frontier_std(rc, rc_mean);
        context[6] = depth_mean;
        context[7] = frontier_std(depth, depth_mean);
        context[8] = std::log1p(
            static_cast<double>(dominance_candidate_checks()) /
            static_cast<double>(std::max<std::size_t>(1U, processed_labels_)));
        context[9] = std::log1p(
            static_cast<double>(extended_labels()) /
            static_cast<double>(std::max<std::size_t>(1U, processed_labels_)));
        context[10] = std::log1p(
            static_cast<double>(dominated_labels()) /
            static_cast<double>(std::max<std::size_t>(1U, processed_labels_)));
        context[11] = std::log1p(static_cast<double>(max_visited_bucket_size()));
        context[12] = static_cast<double>(max_visited_bucket_size()) / count_scale;
        context[13] = static_cast<double>(subset_dominance_candidate_checks()) /
                      static_cast<double>(std::max<std::size_t>(1U, processed_labels_));
        context[14] = static_cast<double>(subset_dominance_rejected_labels()) /
                      static_cast<double>(std::max<std::size_t>(
                          1U, subset_dominance_candidate_checks()));
        context[21] = static_cast<double>(model_->branch_decisions.size());
        context[22] = static_cast<double>(model_->cuts.size());
        context[23] = std::log1p(std::accumulate(
            model_->cuts.begin(), model_->cuts.end(), 0.0,
            [](double total, const auto& cut) {
                return total + std::abs(cut.dual);
            }));
        context[26] = model_->positive_task_dual_sum / model_->absolute_dual_sum;
        context[27] = model_->fleet_dual / model_->absolute_dual_sum;

        std::array<std::uint64_t, 4> digest{
            0xcbf29ce484222325ULL,
            0x84222325cbf29ce4ULL,
            0x9e3779b97f4a7c15ULL,
            0x6a09e667f3bcc909ULL,
        };
        auto digest_value = [&digest](std::uint64_t value) {
            for (std::size_t index = 0; index < digest.size(); ++index) {
                digest[index] ^= frontier_mix(
                    value + index * 0x100000001b3ULL);
                digest[index] *= 0x100000001b3ULL;
            }
        };
        digest_value(graph.frontier_size);
        for (const auto& node : graph.label_nodes) {
            digest_value(node.creation_sequence_id);
            digest_value(node.parent_creation_sequence_id);
            digest_value(node.last_task_index);
            digest_value(node.depth_rc_cell);
            digest_value(node.dominance_surface_hash);
            for (const auto value : node.features) {
                digest_value(std::bit_cast<std::uint64_t>(value));
            }
        }
        for (const auto& edge : graph.label_edges) {
            digest_value(edge.source);
            digest_value(edge.target);
            for (const auto value : edge.features) {
                digest_value(std::bit_cast<std::uint64_t>(value));
            }
        }
        for (const auto value : context) {
            digest_value(std::bit_cast<std::uint64_t>(value));
        }
        std::ostringstream stream;
        stream << std::hex << std::setfill('0');
        for (const auto value : digest) {
            stream << std::setw(16) << value;
        }
        graph.graph_hash = stream.str();
        graph.build_wall_seconds =
            std::chrono::duration<double>(Clock::now() - started).count();
        return graph;
    }

    TemporalPortableGraph build_temporal_label_task_graph(
        const CounterfactualFrontierGraph& native_graph
    ) const {
        TemporalPortableGraph graph;
        graph.context_features = native_graph.context_features;
        const auto label_count = native_graph.label_nodes.size();
        graph.node_features.reserve(label_count + model_->tasks.size());
        graph.creation_sequence_ids.reserve(label_count + model_->tasks.size());

        std::vector<std::size_t> canonical_tasks(model_->tasks.size());
        std::iota(canonical_tasks.begin(), canonical_tasks.end(), 0U);
        std::ranges::sort(canonical_tasks, [&](std::size_t lhs, std::size_t rhs) {
            return model_->tasks[lhs].id < model_->tasks[rhs].id;
        });
        std::unordered_map<std::size_t, std::size_t> canonical_by_original;
        canonical_by_original.reserve(canonical_tasks.size());
        for (std::size_t canonical = 0; canonical < canonical_tasks.size(); ++canonical) {
            canonical_by_original.emplace(
                model_->tasks[canonical_tasks[canonical]].index, canonical);
        }

        std::vector<std::size_t> last_task_by_label;
        last_task_by_label.reserve(label_count);
        for (const auto& node : native_graph.label_nodes) {
            std::array<double, kTemporalGatNodeFeatureCount> features{};
            std::copy(node.features.begin(), node.features.end(), features.begin());
            features[24] = 1.0;
            const auto found = canonical_by_original.find(node.last_task_index);
            const auto canonical = found == canonical_by_original.end()
                                       ? std::numeric_limits<std::size_t>::max()
                                       : found->second;
            if (canonical < canonical_tasks.size()) {
                features[20] = static_cast<double>(canonical + 1U) /
                               static_cast<double>(canonical_tasks.size());
            } else {
                features[20] = 0.0;
            }
            graph.node_features.push_back(features);
            graph.creation_sequence_ids.push_back(node.creation_sequence_id);
            last_task_by_label.push_back(canonical);
        }

        double horizon = 1.0;
        double demand_scale = 1.0;
        double energy_scale = 1.0;
        double cost_scale = 1.0;
        double dual_scale = 0.0;
        for (const auto& task : model_->tasks) {
            horizon = std::max(horizon, task.due_time);
            demand_scale = std::max(demand_scale, task.demand);
            energy_scale = std::max(energy_scale, task.service_energy);
            cost_scale = std::max(cost_scale, std::abs(task.service_cost));
            dual_scale += std::abs(task.dual);
        }
        dual_scale = std::max(1.0, dual_scale);
        std::vector<std::size_t> branch_degree(model_->tasks.size(), 0U);
        for (const auto& decision : model_->branch_decisions) {
            const auto left = canonical_by_original.find(decision.task_a);
            const auto right = canonical_by_original.find(decision.task_b);
            if (decision.task_a_exists && left != canonical_by_original.end()) {
                ++branch_degree[left->second];
            }
            if (decision.task_b_exists && right != canonical_by_original.end()) {
                ++branch_degree[right->second];
            }
        }
        std::vector<std::size_t> cut_degree(model_->tasks.size(), 0U);
        for (const auto& cut : model_->cuts) {
            for (std::size_t canonical = 0; canonical < canonical_tasks.size(); ++canonical) {
                const auto original = model_->tasks[canonical_tasks[canonical]].index;
                const auto word = original / 64U;
                const auto bit = original % 64U;
                if (word < cut.task_mask.size() &&
                    ((cut.task_mask[word] >> bit) & 1U) != 0U) {
                    ++cut_degree[canonical];
                }
            }
        }
        for (std::size_t canonical = 0; canonical < canonical_tasks.size(); ++canonical) {
            const auto& task = model_->tasks[canonical_tasks[canonical]];
            std::array<double, kTemporalGatNodeFeatureCount> features{};
            features[25] = 1.0;
            features[26] = task.demand / demand_scale;
            features[27] = task.service_time / horizon;
            features[28] = task.service_energy / energy_scale;
            features[29] = task.service_cost / cost_scale;
            features[30] = task.ready_time / horizon;
            features[31] = task.due_time / horizon;
            features[32] = task.local_shadow_score / horizon;
            features[33] = task.local_thermal_risk;
            features[34] = task.dual / dual_scale;
            features[35] = static_cast<double>(branch_degree[canonical]) /
                           std::max(1.0, static_cast<double>(
                               model_->branch_decisions.size()));
            features[36] = static_cast<double>(cut_degree[canonical]) /
                           std::max(1.0, static_cast<double>(model_->cuts.size()));
            features[37] = static_cast<double>(canonical + 1U) /
                           static_cast<double>(canonical_tasks.size());
            features[38] = 1.0;
            features[39] = 1.0;
            graph.node_features.push_back(features);
            graph.creation_sequence_ids.push_back(
                std::numeric_limits<std::uint64_t>::max());
        }

        using EdgeKey = std::tuple<std::size_t, std::size_t, std::size_t>;
        std::map<EdgeKey, std::array<double, kTemporalGatEdgeFeatureCount>> edges;
        for (const auto& edge : native_graph.label_edges) {
            std::array<double, kTemporalGatEdgeFeatureCount> features{};
            std::copy(edge.features.begin(), edge.features.end(), features.begin());
            edges[{edge.source, edge.target, 0U}] = features;
        }
        for (std::size_t label = 0; label < last_task_by_label.size(); ++label) {
            if (last_task_by_label[label] >= canonical_tasks.size()) {
                continue;
            }
            std::array<double, kTemporalGatEdgeFeatureCount> features{};
            features[8] = 1.0;
            const auto task = label_count + last_task_by_label[label];
            edges[{label, task, 1U}] = features;
            edges[{task, label, 1U}] = features;
        }
        // Explicit fine-to-coarse membership relation: sampled labels in the
        // same deterministic depth x partial-RC cell are joined in creation-
        // ID order.  The complete 64-cell graph remains a separate resolution
        // with shared message weights; this relation exposes membership to the
        // label/task resolution without duplicating cell nodes.
        std::map<std::size_t, std::vector<std::size_t>> labels_by_cell;
        for (std::size_t label = 0; label < native_graph.label_nodes.size(); ++label) {
            labels_by_cell[native_graph.label_nodes[label].depth_rc_cell]
                .push_back(label);
        }
        for (auto& [cell, members] : labels_by_cell) {
            static_cast<void>(cell);
            std::ranges::sort(members, [&](std::size_t left, std::size_t right) {
                return native_graph.label_nodes[left].creation_sequence_id <
                       native_graph.label_nodes[right].creation_sequence_id;
            });
            for (std::size_t index = 1U; index < members.size(); ++index) {
                std::array<double, kTemporalGatEdgeFeatureCount> features{};
                features[10] = 1.0;
                edges[{members[index - 1U], members[index], 3U}] = features;
                edges[{members[index], members[index - 1U], 3U}] = features;
            }
        }

        std::map<std::pair<std::size_t, std::size_t>, double> travel;
        std::unordered_map<std::string, std::size_t> canonical_by_id;
        for (std::size_t canonical = 0; canonical < canonical_tasks.size(); ++canonical) {
            canonical_by_id.emplace(
                model_->tasks[canonical_tasks[canonical]].id, canonical);
        }
        for (const auto& arc : model_->arcs) {
            const auto source = canonical_by_id.find(arc.source);
            const auto target = canonical_by_id.find(arc.target);
            if (source == canonical_by_id.end() || target == canonical_by_id.end() ||
                source->second == target->second) {
                continue;
            }
            const auto key = std::pair{source->second, target->second};
            const auto found = travel.find(key);
            if (found == travel.end() || arc.travel_time < found->second) {
                travel[key] = arc.travel_time;
            }
        }
        auto add_task_interaction = [&](std::size_t left, std::size_t right,
                                        std::size_t type) {
            std::array<double, kTemporalGatEdgeFeatureCount> features{};
            features[9] = 1.0;
            edges[{label_count + left, label_count + right, type}] = features;
        };
        for (std::size_t source = 0; source < canonical_tasks.size(); ++source) {
            std::vector<std::pair<double, std::size_t>> candidates;
            for (std::size_t target = 0; target < canonical_tasks.size(); ++target) {
                const auto found = travel.find({source, target});
                if (source != target && found != travel.end()) {
                    candidates.emplace_back(found->second, target);
                }
            }
            std::ranges::sort(candidates, [&](const auto& lhs, const auto& rhs) {
                return std::tie(lhs.first,
                                model_->tasks[canonical_tasks[lhs.second]].id) <
                       std::tie(rhs.first,
                                model_->tasks[canonical_tasks[rhs.second]].id);
            });
            candidates.resize(std::min<std::size_t>(4U, candidates.size()));
            for (const auto& [time, target] : candidates) {
                static_cast<void>(time);
                add_task_interaction(source, target, 2U);
                add_task_interaction(target, source, 2U);
            }
        }
        for (const auto& decision : model_->branch_decisions) {
            const auto left = canonical_by_original.find(decision.task_a);
            const auto right = canonical_by_original.find(decision.task_b);
            if (decision.task_a_exists && decision.task_b_exists &&
                left != canonical_by_original.end() &&
                right != canonical_by_original.end()) {
                add_task_interaction(left->second, right->second, 2U);
                add_task_interaction(right->second, left->second, 2U);
            }
        }
        for (const auto& cut : model_->cuts) {
            std::vector<std::size_t> members;
            for (std::size_t canonical = 0; canonical < canonical_tasks.size(); ++canonical) {
                const auto original = model_->tasks[canonical_tasks[canonical]].index;
                const auto word = original / 64U;
                const auto bit = original % 64U;
                if (word < cut.task_mask.size() &&
                    ((cut.task_mask[word] >> bit) & 1U) != 0U) {
                    members.push_back(canonical);
                }
            }
            for (std::size_t left = 0; left < members.size(); ++left) {
                for (std::size_t right = left + 1U; right < members.size(); ++right) {
                    add_task_interaction(members[left], members[right], 2U);
                    add_task_interaction(members[right], members[left], 2U);
                }
            }
        }
        for (std::size_t node = 0; node < graph.node_features.size(); ++node) {
            std::array<double, kTemporalGatEdgeFeatureCount> features{};
            features[0] = 1.0;
            edges.try_emplace(EdgeKey{node, node, 5U}, features);
        }
        graph.edges.reserve(edges.size());
        for (const auto& [key, features] : edges) {
            graph.edges.push_back(TemporalGraphEdge{
                .source = std::get<0>(key),
                .target = std::get<1>(key),
                .features = features,
            });
        }

        std::array<std::uint64_t, 4> digest{
            0xcbf29ce484222325ULL, 0x84222325cbf29ce4ULL,
            0x9e3779b97f4a7c15ULL, 0x6a09e667f3bcc909ULL,
        };
        auto digest_value = [&digest](std::uint64_t value) {
            for (std::size_t index = 0; index < digest.size(); ++index) {
                digest[index] ^= frontier_mix(value + index * 0x100000001b3ULL);
                digest[index] *= 0x100000001b3ULL;
            }
        };
        for (std::size_t node = 0; node < graph.node_features.size(); ++node) {
            digest_value(graph.creation_sequence_ids[node]);
            for (const auto value : graph.node_features[node]) {
                digest_value(std::bit_cast<std::uint64_t>(value));
            }
        }
        for (const auto& edge : graph.edges) {
            digest_value(edge.source);
            digest_value(edge.target);
            for (const auto value : edge.features) {
                digest_value(std::bit_cast<std::uint64_t>(value));
            }
        }
        std::ostringstream stream;
        stream << std::hex << std::setfill('0');
        for (const auto value : digest) {
            stream << std::setw(16) << value;
        }
        graph.graph_hash = stream.str();
        return graph;
    }

    void capture_counterfactual_endpoint(std::size_t rollout_budget) {
        const auto records = frontier_records();
        auto graph = build_counterfactual_label_graph();
        std::unordered_set<std::uint64_t> current;
        current.reserve(records.size());
        std::size_t survival = 0;
        for (const auto& record : records) {
            current.insert(record.creation_sequence_id);
            survival += counterfactual_base_label_ids_.contains(
                            record.creation_sequence_id)
                            ? 1U
                            : 0U;
        }
        const auto base_count = counterfactual_base_label_ids_.size();
        const auto new_count = graph.frontier_size > survival
                                   ? graph.frontier_size - survival
                                   : 0U;
        counterfactual_prefix_telemetry_.endpoints.push_back(
            CounterfactualPrefixEndpoint{
                .rollout_budget = rollout_budget,
                .processed_labels = processed_labels_,
                .extended_labels = extended_labels(),
                .dominated_labels = dominated_labels(),
                .dominance_candidate_checks = dominance_candidate_checks(),
                .subset_dominance_candidate_checks =
                    subset_dominance_candidate_checks(),
                .subset_dominance_rejected_labels =
                    subset_dominance_rejected_labels(),
                .frontier_size = graph.frontier_size,
                .max_visited_bucket_size = max_visited_bucket_size(),
                .negative_label_event_count =
                    best_reduced_cost_event_count_total_,
                .best_true_reduced_cost = best_reduced_cost_,
                .base_label_survival_count = survival,
                .new_label_count = new_count,
                .frontier_churn = static_cast<double>(
                    base_count + graph.frontier_size - 2U * survival) /
                    static_cast<double>(std::max<std::size_t>(
                        1U, base_count + graph.frontier_size)),
                .request_elapsed_wall_seconds =
                    counterfactual_timing_started_
                        ? std::chrono::duration<double>(
                              Clock::now() - counterfactual_request_started_)
                              .count()
                        : 0.0,
                .rollout_elapsed_wall_seconds =
                    counterfactual_boundary_timing_started_
                        ? std::chrono::duration<double>(
                              Clock::now() - counterfactual_boundary_started_)
                              .count()
                        : 0.0,
                .graph_build_wall_seconds = graph.build_wall_seconds,
                .graph = std::move(graph),
            });
    }

    bool maybe_run_counterfactual_prefix() {
        auto& config = counterfactual_prefix_config_;
        auto& telemetry = counterfactual_prefix_telemetry_;
        if (config.mode == CounterfactualPrefixMode::Disabled) {
            return false;
        }
        if (!telemetry.reached_boundary &&
            processed_labels_ == config.processed_label_boundary) {
            telemetry.reached_boundary = true;
            if (number_of_labels() == 0U) {
                telemetry.stop_reason = "base_frontier_empty";
                return false;
            }
            telemetry.base_graph = build_counterfactual_label_graph();
            telemetry.base_graph_hash = telemetry.base_graph.graph_hash;
            telemetry.base_graph_build_wall_seconds =
                telemetry.base_graph.build_wall_seconds;
            telemetry.base_request_elapsed_wall_seconds =
                counterfactual_timing_started_
                    ? std::chrono::duration<double>(
                          Clock::now() - counterfactual_request_started_)
                          .count()
                    : 0.0;
            counterfactual_boundary_started_ = Clock::now();
            counterfactual_boundary_timing_started_ = true;
            telemetry.base_processed_labels = processed_labels_;
            telemetry.base_extended_labels = extended_labels();
            telemetry.base_dominated_labels = dominated_labels();
            telemetry.base_dominance_candidate_checks =
                dominance_candidate_checks();
            telemetry.base_subset_dominance_candidate_checks =
                subset_dominance_candidate_checks();
            telemetry.base_subset_dominance_rejected_labels =
                subset_dominance_rejected_labels();
            telemetry.base_max_visited_bucket_size =
                max_visited_bucket_size();
            telemetry.base_negative_label_event_count =
                best_reduced_cost_event_count_total_;
            telemetry.base_best_true_reduced_cost = best_reduced_cost_;
            counterfactual_base_label_ids_.clear();
            for (const auto& record : frontier_records()) {
                counterfactual_base_label_ids_.insert(
                    record.creation_sequence_id);
            }
            if (config.mode == CounterfactualPrefixMode::QD1Prefix) {
                const auto migration_started = Clock::now();
                migrate_counterfactual_frontier_to_qd1();
                telemetry.migration_wall_seconds =
                    std::chrono::duration<double>(
                        Clock::now() - migration_started).count();
                telemetry.switched_to_qd1 = true;
            }
        }
        if (!telemetry.reached_boundary) {
            return false;
        }
        while (counterfactual_checkpoint_index_ <
               config.rollout_checkpoints.size()) {
            const auto budget = config.rollout_checkpoints[
                counterfactual_checkpoint_index_];
            const auto target = config.processed_label_boundary + budget;
            if (processed_labels_ < target) {
                break;
            }
            capture_counterfactual_endpoint(budget);
            ++counterfactual_checkpoint_index_;
            if (budget == config.maximum_rollout_budget) {
                telemetry.complete = true;
                telemetry.truncated_diagnostic = true;
                telemetry.request_elapsed_wall_seconds =
                    counterfactual_timing_started_
                        ? std::chrono::duration<double>(
                              Clock::now() - counterfactual_request_started_)
                              .count()
                        : 0.0;
                telemetry.stop_reason = "selected_rollout_checkpoint_reached";
                return true;
            }
        }
        return false;
    }

    void build_frontier_graph() {
        const auto started = Clock::now();
        frontier_probe_telemetry_.graph_built = false;
        frontier_probe_telemetry_.graph_hash.clear();
        frontier_probe_telemetry_.frontier_size = 0;
        frontier_probe_telemetry_.nonempty_node_count = 0;
        frontier_probe_telemetry_.edge_count = 0;
        frontier_probe_telemetry_.graph_build_wall_seconds = 0.0;
        frontier_probe_telemetry_.node_features.clear();
        frontier_probe_telemetry_.edges.clear();
        auto records = frontier_records();
        if (records.empty()) {
            frontier_probe_telemetry_.decision_reason = "frontier_empty";
            return;
        }
        frontier_probe_telemetry_.frontier_size = records.size();
        frontier_probe_telemetry_.node_features.assign(
            kFrontierNodeCount,
            std::array<double, kFrontierNodeFeatureCount>{});
        struct CellValues {
            std::vector<double> rc;
            std::vector<double> depth;
            std::vector<double> age;
            std::unordered_map<std::size_t, std::size_t> last_tasks;
            std::size_t terminal_count = 0;
        };
        std::array<CellValues, kFrontierNodeCount> cells;
        const double rc_scale = std::max(1.0, model_->absolute_dual_sum);
        const double creation_scale = static_cast<double>(
            std::max<std::uint64_t>(1U, next_creation_sequence_id_));
        for (const auto& record : records) {
            auto& cell = cells[record.cell];
            cell.rc.push_back(record.partial_cost / rc_scale);
            cell.depth.push_back(
                static_cast<double>(record.visited_count) /
                static_cast<double>(std::max<std::size_t>(1U, model_->tasks.size())));
            cell.age.push_back(
                static_cast<double>(
                    next_creation_sequence_id_ - 1U -
                    std::min(next_creation_sequence_id_ - 1U,
                             record.creation_sequence_id)) /
                creation_scale);
            if (record.last_task_index != std::numeric_limits<std::size_t>::max()) {
                ++cell.last_tasks[record.last_task_index];
            }
            cell.terminal_count += record.terminal ? 1U : 0U;
        }
        constexpr std::array<double, 8> depth_lower{
            0.0, 0.05, 0.10, 0.20, 0.30, 0.40, 0.55, 0.75};
        for (std::size_t cell_index = 0; cell_index < cells.size(); ++cell_index) {
            const auto& cell = cells[cell_index];
            auto& output = frontier_probe_telemetry_.node_features[cell_index];
            if (cell.rc.empty()) {
                output[14] = depth_lower[cell_index / 8U];
                output[15] = (static_cast<double>(cell_index % 8U) + 0.5) / 8.0;
                continue;
            }
            ++frontier_probe_telemetry_.nonempty_node_count;
            const double count = static_cast<double>(cell.rc.size());
            const double rc_mean = frontier_mean(cell.rc);
            const double depth_mean = frontier_mean(cell.depth);
            const double age_mean = frontier_mean(cell.age);
            double entropy = 0.0;
            for (const auto& [task, occurrences] : cell.last_tasks) {
                static_cast<void>(task);
                const double probability = static_cast<double>(occurrences) / count;
                entropy -= probability * std::log(std::max(1.0e-12, probability));
            }
            output = {
                1.0,
                std::log1p(count),
                count / static_cast<double>(records.size()),
                static_cast<double>(cell.terminal_count) / count,
                rc_mean,
                *std::ranges::min_element(cell.rc),
                *std::ranges::max_element(cell.rc),
                frontier_std(cell.rc, rc_mean),
                depth_mean,
                frontier_std(cell.depth, depth_mean),
                age_mean,
                frontier_std(cell.age, age_mean),
                static_cast<double>(cell.last_tasks.size()) /
                    static_cast<double>(std::max<std::size_t>(1U, model_->tasks.size())),
                entropy / std::log1p(
                    static_cast<double>(std::max<std::size_t>(1U, model_->tasks.size()))),
                depth_lower[cell_index / 8U],
                (static_cast<double>(cell_index % 8U) + 0.5) / 8.0,
            };
        }

        struct EdgeKey {
            std::size_t source = 0;
            std::size_t target = 0;
            std::size_t type = 0;
            auto operator<=>(const EdgeKey&) const = default;
        };
        std::map<EdgeKey, std::pair<std::size_t, std::size_t>> edge_counts;
        for (std::size_t cell = 0; cell < kFrontierNodeCount; ++cell) {
            edge_counts[{cell, cell, 0U}];
            const auto depth = cell / 8U;
            const auto rc = cell % 8U;
            if (depth + 1U < 8U) {
                edge_counts[{cell, cell + 8U, 1U}];
                edge_counts[{cell + 8U, cell, 1U}];
            }
            if (rc + 1U < 8U) {
                edge_counts[{cell, cell + 1U, 2U}];
                edge_counts[{cell + 1U, cell, 2U}];
            }
        }
        std::unordered_map<const Label*, const FrontierLabelRecord*> record_by_label;
        record_by_label.reserve(records.size());
        for (const auto& record : records) {
            record_by_label.emplace(record.value.first, &record);
        }
        std::size_t transition_count = 0;
        for (const auto& child : records) {
            const auto* parent = child.value.first->prev_label;
            const auto found = record_by_label.find(parent);
            if (found == record_by_label.end()) {
                continue;
            }
            const auto& parent_record = *found->second;
            auto& forward = edge_counts[{parent_record.cell, child.cell, 3U}];
            ++forward.first;
            forward.second += parent_record.terminal == child.terminal ? 1U : 0U;
            auto& reverse = edge_counts[{child.cell, parent_record.cell, 4U}];
            ++reverse.first;
            reverse.second += parent_record.terminal == child.terminal ? 1U : 0U;
            ++transition_count;
        }
        frontier_probe_telemetry_.edges.clear();
        frontier_probe_telemetry_.edges.reserve(edge_counts.size());
        for (const auto& [key, counts] : edge_counts) {
            FrontierGraphEdge edge;
            edge.source = key.source;
            edge.target = key.target;
            edge.features[key.type] = 1.0;
            if (key.type == 3U || key.type == 4U) {
                edge.features[5] = std::log1p(static_cast<double>(counts.first));
                edge.features[6] = static_cast<double>(counts.first) /
                                   static_cast<double>(std::max<std::size_t>(1U, transition_count));
                edge.features[9] = static_cast<double>(counts.second) /
                                   static_cast<double>(std::max<std::size_t>(1U, counts.first));
            }
            edge.features[7] = static_cast<double>(key.target / 8U) -
                               static_cast<double>(key.source / 8U);
            edge.features[8] = static_cast<double>(key.target % 8U) -
                               static_cast<double>(key.source % 8U);
            frontier_probe_telemetry_.edges.push_back(edge);
        }
        frontier_probe_telemetry_.edge_count =
            frontier_probe_telemetry_.edges.size();

        std::vector<double> all_rc;
        std::vector<double> all_depth;
        all_rc.reserve(records.size());
        all_depth.reserve(records.size());
        std::size_t terminal_count = 0;
        for (const auto& record : records) {
            all_rc.push_back(record.partial_cost / rc_scale);
            all_depth.push_back(
                static_cast<double>(record.visited_count) /
                static_cast<double>(std::max<std::size_t>(1U, model_->tasks.size())));
            terminal_count += record.terminal ? 1U : 0U;
        }
        auto& context = frontier_probe_telemetry_.context_features;
        const double rc_mean = frontier_mean(all_rc);
        const double depth_mean = frontier_mean(all_depth);
        context[0] = std::log1p(static_cast<double>(model_->tasks.size()));
        context[1] = std::log1p(static_cast<double>(records.size()));
        context[2] = static_cast<double>(terminal_count) /
                     static_cast<double>(records.size());
        context[3] = rc_mean;
        context[4] = *std::ranges::min_element(all_rc);
        context[5] = frontier_std(all_rc, rc_mean);
        context[6] = depth_mean;
        context[7] = frontier_std(all_depth, depth_mean);
        context[8] = std::log1p(
            static_cast<double>(dominance_candidate_checks()) /
            static_cast<double>(std::max<std::size_t>(1U, processed_labels_)));
        context[9] = std::log1p(
            static_cast<double>(extended_labels()) /
            static_cast<double>(std::max<std::size_t>(1U, processed_labels_)));
        context[10] = std::log1p(
            static_cast<double>(dominated_labels()) /
            static_cast<double>(std::max<std::size_t>(1U, processed_labels_)));
        context[11] = std::log1p(static_cast<double>(max_visited_bucket_size()));
        context[12] = static_cast<double>(max_visited_bucket_size()) /
                      static_cast<double>(records.size());
        context[13] = static_cast<double>(subset_dominance_candidate_checks()) /
                      static_cast<double>(std::max<std::size_t>(1U, processed_labels_));
        context[14] = static_cast<double>(subset_dominance_rejected_labels()) /
                      static_cast<double>(std::max<std::size_t>(
                          1U, subset_dominance_candidate_checks()));
        context[21] = static_cast<double>(model_->branch_decisions.size());
        context[22] = static_cast<double>(model_->cuts.size());
        double cut_dual_abs = 0.0;
        for (const auto& cut : model_->cuts) {
            cut_dual_abs += std::abs(cut.dual);
        }
        context[23] = std::log1p(cut_dual_abs);
        context[26] = model_->positive_task_dual_sum / rc_scale;
        context[27] = model_->fleet_dual / rc_scale;

        std::array<std::uint64_t, 4> digest{
            0xcbf29ce484222325ULL,
            0x84222325cbf29ce4ULL,
            0x9e3779b97f4a7c15ULL,
            0x6a09e667f3bcc909ULL,
        };
        auto digest_value = [&digest](std::uint64_t value) {
            for (std::size_t index = 0; index < digest.size(); ++index) {
                digest[index] ^= frontier_mix(value + index * 0x100000001b3ULL);
                digest[index] *= 0x100000001b3ULL;
            }
        };
        for (const auto& node : frontier_probe_telemetry_.node_features) {
            for (const double value : node) {
                digest_value(std::bit_cast<std::uint64_t>(value));
            }
        }
        for (const auto& edge : frontier_probe_telemetry_.edges) {
            digest_value(edge.source);
            digest_value(edge.target);
            for (const double value : edge.features) {
                digest_value(std::bit_cast<std::uint64_t>(value));
            }
        }
        for (const double value : context) {
            digest_value(std::bit_cast<std::uint64_t>(value));
        }
        std::ostringstream stream;
        stream << std::hex << std::setfill('0');
        for (const auto value : digest) {
            stream << std::setw(16) << value;
        }
        frontier_probe_telemetry_.graph_hash = stream.str();
        frontier_probe_telemetry_.graph_built = true;
        frontier_probe_telemetry_.graph_build_wall_seconds =
            std::chrono::duration<double>(Clock::now() - started).count();
    }

    bool frontier_graph_is_ood(const FrontierGatBundle& bundle) const {
        auto outside = [](double value, const std::vector<double>& minimum,
                          const std::vector<double>& maximum,
                          std::size_t index) {
            return index >= minimum.size() || index >= maximum.size() ||
                   !std::isfinite(value) || value < minimum[index] ||
                   value > maximum[index];
        };
        for (const auto& node : frontier_probe_telemetry_.node_features) {
            for (std::size_t index = 0; index < node.size(); ++index) {
                if (outside(node[index], bundle.node_min, bundle.node_max, index)) {
                    return true;
                }
            }
        }
        for (const auto& edge : frontier_probe_telemetry_.edges) {
            for (std::size_t index = 0; index < edge.features.size(); ++index) {
                if (outside(edge.features[index], bundle.edge_min, bundle.edge_max, index)) {
                    return true;
                }
            }
        }
        for (std::size_t index = 0;
             index < frontier_probe_telemetry_.context_features.size(); ++index) {
            if (outside(
                    frontier_probe_telemetry_.context_features[index],
                    bundle.context_min, bundle.context_max, index)) {
                return true;
            }
        }
        return false;
    }

    bool learned_frontier_action() {
        const auto started = Clock::now();
        const auto& bundle = frontier_probe_config_.bundle;
        if (!frontier_bundle_is_valid(bundle)) {
            frontier_probe_telemetry_.fail_closed = true;
            frontier_probe_telemetry_.decision_reason = "invalid_bundle";
            return false;
        }
        if (frontier_graph_is_ood(bundle)) {
            frontier_probe_telemetry_.fail_closed = true;
            frontier_probe_telemetry_.inference_ood = true;
            frontier_probe_telemetry_.ood_reason = "feature_outside_frozen_range";
            frontier_probe_telemetry_.decision_reason = "frontier_ood";
            return false;
        }
        try {
            frontier_probe_telemetry_.seed_outputs.clear();
            for (const auto& model : bundle.models) {
                frontier_probe_telemetry_.seed_outputs.push_back(
                    frontier_gat_forward(
                        model, bundle, frontier_probe_telemetry_));
            }
            frontier_probe_telemetry_.model_called = true;
            double benefit_sum = 0.0;
            double benefit_min = 1.0;
            double benefit_max = 0.0;
            double gain_min = 1.0;
            double gain_max = 0.0;
            double adverse_min = 1.0;
            double adverse_max = 0.0;
            for (const auto& output : frontier_probe_telemetry_.seed_outputs) {
                if (std::ranges::any_of(output, [](double value) {
                        return !std::isfinite(value);
                    })) {
                    throw std::invalid_argument("nonfinite frontier GAT output");
                }
                benefit_sum += output[0];
                benefit_min = std::min(benefit_min, output[0]);
                benefit_max = std::max(benefit_max, output[0]);
                gain_min = std::min(gain_min, output[1]);
                gain_max = std::max(gain_max, output[1]);
                adverse_min = std::min(adverse_min, output[2]);
                adverse_max = std::max(adverse_max, output[2]);
            }
            auto& telemetry = frontier_probe_telemetry_;
            telemetry.p_benefit = benefit_sum /
                                  static_cast<double>(telemetry.seed_outputs.size());
            telemetry.positive_gain = gain_min;
            telemetry.p_adverse = adverse_max;
            telemetry.disagreement = std::max({
                benefit_max - benefit_min,
                gain_max - gain_min,
                adverse_max - adverse_min,
            });
            telemetry.p_benefit = frontier_calibrated_probability(
                telemetry.p_benefit, bundle.benefit_calibration);
            telemetry.p_adverse = frontier_calibrated_probability(
                telemetry.p_adverse, bundle.adverse_calibration);
            telemetry.positive_gain = std::clamp(
                telemetry.positive_gain * bundle.gain_scale, 0.0, 1.0);
            telemetry.expected_gain = telemetry.p_benefit * telemetry.positive_gain;
            telemetry.risk_score = telemetry.expected_gain -
                                   bundle.adverse_penalty * telemetry.p_adverse;
            const bool selected =
                telemetry.p_benefit >= bundle.minimum_benefit_probability &&
                telemetry.p_adverse <= bundle.maximum_adverse_probability &&
                telemetry.expected_gain >= bundle.minimum_expected_gain &&
                telemetry.risk_score > 0.0 &&
                telemetry.disagreement <= bundle.maximum_disagreement;
            telemetry.decision_reason = selected
                                            ? "learned_threshold_accept"
                                            : "learned_threshold_reject";
            telemetry.inference_wall_seconds =
                std::chrono::duration<double>(Clock::now() - started).count();
            return selected;
        } catch (const std::exception& exception) {
            frontier_probe_telemetry_.fail_closed = true;
            frontier_probe_telemetry_.decision_reason =
                std::string("model_fail_closed:") + exception.what();
            frontier_probe_telemetry_.inference_wall_seconds =
                std::chrono::duration<double>(Clock::now() - started).count();
            return false;
        }
    }

    bool temporal_graph_is_ood(
        const TemporalGatBundle& bundle,
        const std::array<double, kTemporalGatCounterFeatureCount>& counters,
        const std::array<double, kFrontierContextFeatureCount>& context
    ) const {
        auto outside = [](double value,
                          const TemporalNormalizationGroup& group,
                          std::size_t index) {
            return index >= group.minimum.size() ||
                   !std::isfinite(value) ||
                   value < group.minimum[index] ||
                   value > group.maximum[index];
        };
        const auto cell_ood = [&](const FrontierProbeSnapshot& graph) {
            for (const auto& node : graph.node_features) {
                for (std::size_t index = 0; index < node.size(); ++index) {
                    if (outside(node[index], bundle.cell_node, index)) {
                        return true;
                    }
                }
            }
            for (const auto& edge : graph.edges) {
                for (std::size_t index = 0; index < edge.features.size(); ++index) {
                    if (outside(edge.features[index], bundle.cell_edge, index)) {
                        return true;
                    }
                }
            }
            return false;
        };
        const auto label_ood = [&](const TemporalPortableGraph& graph) {
            for (const auto& node : graph.node_features) {
                for (std::size_t index = 0; index < node.size(); ++index) {
                    if (outside(node[index], bundle.node, index)) {
                        return true;
                    }
                }
            }
            for (const auto& edge : graph.edges) {
                for (std::size_t index = 0; index < edge.features.size(); ++index) {
                    if (outside(edge.features[index], bundle.edge, index)) {
                        return true;
                    }
                }
            }
            return false;
        };
        const auto& telemetry = frontier_probe_telemetry_;
        if (cell_ood(telemetry.trial_start_snapshot) ||
            cell_ood(telemetry.trial_end_snapshot) ||
            label_ood(telemetry.trial_start_temporal_graph) ||
            label_ood(telemetry.trial_end_temporal_graph)) {
            return true;
        }
        for (std::size_t index = 0; index < counters.size(); ++index) {
            if (outside(counters[index], bundle.counter, index)) {
                return true;
            }
        }
        for (std::size_t index = 0; index < context.size(); ++index) {
            if (outside(context[index], bundle.context, index)) {
                return true;
            }
        }
        return false;
    }

    bool learned_temporal_action() {
        const auto started = Clock::now();
        const auto& bundle = frontier_probe_config_.temporal_bundle;
        auto& telemetry = frontier_probe_telemetry_;
        if (!temporal_bundle_is_valid(bundle) ||
            bundle.selected_scale != frontier_probe_config_.problem_scale) {
            telemetry.fail_closed = true;
            telemetry.decision_reason = "invalid_temporal_bundle";
            return false;
        }
        const auto counters = temporal_counter_values(telemetry);
        const auto context = telemetry.trial_end_snapshot.context_features;
        if (temporal_graph_is_ood(bundle, counters, context)) {
            telemetry.fail_closed = true;
            telemetry.inference_ood = true;
            telemetry.ood_reason = "temporal_feature_outside_frozen_range";
            telemetry.decision_reason = "temporal_frontier_ood";
            return false;
        }
        try {
            telemetry.seed_outputs.clear();
            for (const auto& model : bundle.models) {
                telemetry.seed_outputs.push_back(temporal_gat_forward(
                    model, bundle, telemetry.trial_start_snapshot,
                    telemetry.trial_end_snapshot,
                    telemetry.trial_start_temporal_graph,
                    telemetry.trial_end_temporal_graph,
                    counters, context, bundle.selected_scale));
            }
            telemetry.model_called = true;
            const auto decision = decide_temporal_gat_outputs(
                bundle, telemetry.seed_outputs);
            telemetry.p_benefit = decision.p_benefit;
            telemetry.positive_gain = decision.positive_gain;
            telemetry.p_adverse = decision.p_adverse;
            telemetry.disagreement = decision.disagreement;
            telemetry.expected_gain = decision.expected_gain;
            telemetry.risk_score = decision.risk_score;
            const bool evaluation_control =
                bundle.controller_kind != "temporal_gat";
            const bool selected = decision.continue_qd1;
            telemetry.decision_reason = selected
                ? (evaluation_control ? "temporal_control_accept"
                                      : "temporal_learned_threshold_accept")
                : (evaluation_control ? "temporal_control_reject"
                                      : "temporal_learned_threshold_reject");
            telemetry.inference_wall_seconds =
                std::chrono::duration<double>(Clock::now() - started).count();
            return selected;
        } catch (const std::exception& exception) {
            telemetry.fail_closed = true;
            telemetry.decision_reason =
                std::string("temporal_model_fail_closed:") + exception.what();
            telemetry.inference_wall_seconds =
                std::chrono::duration<double>(Clock::now() - started).count();
            return false;
        }
    }

    CachedQueueEntry qd1_entry(
        const Pair& value,
        std::uint64_t creation_sequence_id
    ) const {
        const auto& state = value.first->get_resource()
                                .template get_component<JourneyResource>(0)
                                .get_value()
                                .get_value()
                                .state();
        return CachedQueueEntry{
            .value = value,
            .can_terminate = state.at_depot && state.task_visit_count > 0,
            .primary_key = -static_cast<double>(state.visited_count),
            .secondary_key = 0.0,
            .reduced_cost_bucket = 0,
            .guidance_score = 0.0,
            .partial_cost = value.first->get_cost(),
            .creation_sequence_id = creation_sequence_id,
        };
    }

    void migrate_frontier_to_qd1() {
        const auto started = Clock::now();
        auto& telemetry = frontier_probe_telemetry_;
        telemetry.frontier_before_migration = unprocessed_q0_.size();
        std::unordered_set<std::uint64_t> identifiers;
        identifiers.reserve(unprocessed_q0_.size());
        while (!unprocessed_q0_.empty()) {
            const auto value = unprocessed_q0_.top();
            unprocessed_q0_.pop();
            ++telemetry.drained_count;
            const auto found = creation_sequence_ids_.find(value.first);
            if (found == creation_sequence_ids_.end()) {
                throw std::runtime_error(
                    "frontier migration creation sequence missing");
            }
            const auto creation_id = found->second;
            telemetry.creation_hash_before ^= frontier_mix(creation_id);
            if (!identifiers.insert(creation_id).second) {
                ++telemetry.duplicate_count;
            }
            unprocessed_experimental_.push(qd1_entry(value, creation_id));
            telemetry.creation_hash_after ^= frontier_mix(creation_id);
            ++telemetry.migrated_count;
        }
        if (telemetry.frontier_before_migration != telemetry.drained_count ||
            telemetry.drained_count != telemetry.migrated_count ||
            telemetry.migrated_count != unprocessed_experimental_.size() ||
            telemetry.creation_hash_before != telemetry.creation_hash_after ||
            telemetry.duplicate_count != 0U) {
            throw std::runtime_error("frontier migration correctness redline");
        }
        proof_queue_policy_ = ProofQueuePolicy::QD1DeeperFirst;
        telemetry.switched_to_qd1 = true;
        telemetry.action = "SWITCH_QD1";
        telemetry.migration_wall_seconds =
            std::chrono::duration<double>(Clock::now() - started).count();
    }

    void migrate_frontier_back_to_q0() {
        const auto started = Clock::now();
        auto& telemetry = frontier_probe_telemetry_;
        telemetry.reverse_frontier_before_migration =
            unprocessed_experimental_.size();

        // Build a complete staging queue from a copy. The shared staging
        // primitive is also exercised by empty/single/large/duplicate/fault
        // native tests. The live QD1 queue is untouched until every
        // conservation and binding check has passed.
        auto staged = detail::stage_atomic_frontier_migration(
            unprocessed_experimental_,
            decltype(unprocessed_q0_){},
            [](const CachedQueueEntry& entry) {
                return entry.creation_sequence_id;
            },
            [](const CachedQueueEntry& entry) {
                return entry.value.first;
            },
            [](const CachedQueueEntry& entry) {
                return entry.value;
            },
            [](std::uint64_t creation_id) {
                return frontier_mix(creation_id);
            });
        telemetry.reverse_staged_count = staged.staged_count;
        telemetry.reverse_migrated_count = staged.target.size();
        telemetry.reverse_duplicate_count =
            staged.duplicate_creation_id_count;
        telemetry.reverse_creation_hash_before =
            staged.creation_hash_before;
        telemetry.reverse_creation_hash_after =
            staged.creation_hash_after;

        std::unordered_map<const Label*, std::uint64_t> staged_bindings;
        staged_bindings.reserve(staged.bindings.size());
        for (const auto& [label, creation_id] : staged.bindings) {
            if (!staged_bindings.emplace(label, creation_id).second) {
                ++telemetry.reverse_duplicate_count;
            }
        }
        if (telemetry.reverse_frontier_before_migration !=
                telemetry.reverse_staged_count ||
            telemetry.reverse_staged_count !=
                telemetry.reverse_migrated_count ||
            telemetry.reverse_migrated_count != staged.target.size() ||
            telemetry.reverse_creation_hash_before !=
                telemetry.reverse_creation_hash_after ||
            telemetry.reverse_duplicate_count != 0U ||
            staged_bindings.size() != staged.target.size()) {
            throw std::runtime_error(
                "reverse frontier migration correctness redline");
        }

        unprocessed_q0_.swap(staged.target);
        unprocessed_experimental_ = decltype(unprocessed_experimental_)(
            GreaterCachedKey{guidance_stats_});
        creation_sequence_ids_ = std::move(staged_bindings);
        proof_queue_policy_ = ProofQueuePolicy::Q0PartialCost;
        telemetry.migrated_back_to_q0 = true;
        telemetry.action = "MIGRATE_BACK_TO_Q0";
        telemetry.reverse_migration_wall_seconds =
            std::chrono::duration<double>(Clock::now() - started).count();
    }

    void start_temporal_trial() {
        auto& telemetry = frontier_probe_telemetry_;
        telemetry.trial_started = true;
        telemetry.trial_start_snapshot = current_frontier_snapshot(
            frontier_probe_config_.processed_label_boundary);
        telemetry.temporal_graph_build_wall_seconds =
            telemetry.trial_start_snapshot.graph_build_wall_seconds;
        const auto temporal_graph_started = Clock::now();
        telemetry.trial_start_label_graph = build_counterfactual_label_graph();
        telemetry.trial_start_temporal_graph = build_temporal_label_task_graph(
            telemetry.trial_start_label_graph);
        telemetry.temporal_graph_build_wall_seconds +=
            std::chrono::duration<double>(
                Clock::now() - temporal_graph_started).count();
        temporal_trial_started_ = Clock::now();
        migrate_frontier_to_qd1();
        telemetry.action = "TRIAL_QD1";
        telemetry.decision_reason = "temporal_trial_running";
    }

    void maybe_finish_temporal_trial() {
        auto& telemetry = frontier_probe_telemetry_;
        if (!temporal_trial_mode() || !telemetry.trial_started ||
            telemetry.trial_completed ||
            proof_queue_policy_ != ProofQueuePolicy::QD1DeeperFirst) {
            return;
        }
        const auto target = frontier_probe_config_.processed_label_boundary +
                            frontier_probe_config_.trial_pop_budget;
        telemetry.trial_pops = processed_labels_ -
                               frontier_probe_config_.processed_label_boundary;
        if (processed_labels_ < target) {
            return;
        }
        build_frontier_graph();
        if (!frontier_probe_telemetry_.graph_built) {
            telemetry.decision_reason = "trial_frontier_empty";
            return;
        }
        telemetry.trial_end_snapshot = current_frontier_snapshot(target);
        telemetry.temporal_graph_build_wall_seconds +=
            telemetry.trial_end_snapshot.graph_build_wall_seconds;
        const auto temporal_graph_started = Clock::now();
        telemetry.trial_end_label_graph = build_counterfactual_label_graph();
        telemetry.trial_end_temporal_graph = build_temporal_label_task_graph(
            telemetry.trial_end_label_graph);
        telemetry.temporal_graph_build_wall_seconds +=
            std::chrono::duration<double>(
                Clock::now() - temporal_graph_started).count();
        std::unordered_set<std::uint64_t> start_ids;
        for (std::uint64_t cell = 0; cell < kFrontierNodeCount; ++cell) {
            telemetry.temporal_edges.push_back({0U, cell, cell});
        }
        for (const auto id :
             telemetry.trial_start_temporal_graph.creation_sequence_ids) {
            if (id != std::numeric_limits<std::uint64_t>::max()) {
                start_ids.insert(id);
            }
        }
        for (const auto id :
             telemetry.trial_end_temporal_graph.creation_sequence_ids) {
            if (id == std::numeric_limits<std::uint64_t>::max()) {
                continue;
            }
            if (start_ids.contains(id)) {
                ++telemetry.temporal_surviving_label_count;
                telemetry.temporal_edges.push_back({1U, id, id});
            } else {
                ++telemetry.temporal_new_label_count;
            }
        }
        const auto start_frontier =
            telemetry.trial_start_label_graph.frontier_size;
        const auto end_frontier =
            telemetry.trial_end_label_graph.frontier_size;
        telemetry.temporal_extended_label_delta =
            telemetry.trial_end_snapshot.extended_labels -
            telemetry.trial_start_snapshot.extended_labels;
        telemetry.temporal_dominated_label_delta =
            telemetry.trial_end_snapshot.dominated_labels -
            telemetry.trial_start_snapshot.dominated_labels;
        telemetry.temporal_survival_fraction =
            static_cast<double>(telemetry.temporal_surviving_label_count) /
            static_cast<double>(std::max<std::size_t>(1U, start_frontier));
        telemetry.temporal_frontier_churn = static_cast<double>(
            start_frontier + end_frontier - 2U * std::min(
                telemetry.temporal_surviving_label_count,
                std::min(start_frontier, end_frontier))) /
            static_cast<double>(std::max<std::size_t>(
                1U, start_frontier + end_frontier));
        telemetry.temporal_cell_edge_count = kFrontierNodeCount;
        telemetry.temporal_label_edge_count =
            telemetry.temporal_surviving_label_count;
        std::array<std::uint64_t, 4> temporal_digest{
            0xcbf29ce484222325ULL, 0x84222325cbf29ce4ULL,
            0x9e3779b97f4a7c15ULL, 0x6a09e667f3bcc909ULL,
        };
        for (const auto& edge : telemetry.temporal_edges) {
            for (const auto value : edge) {
                for (std::size_t index = 0; index < temporal_digest.size(); ++index) {
                    temporal_digest[index] ^=
                        frontier_mix(value + index * 0x100000001b3ULL);
                    temporal_digest[index] *= 0x100000001b3ULL;
                }
            }
        }
        std::ostringstream temporal_stream;
        temporal_stream << std::hex << std::setfill('0');
        for (const auto value : temporal_digest) {
            temporal_stream << std::setw(16) << value;
        }
        telemetry.temporal_edge_hash = temporal_stream.str();
        telemetry.trial_completed = true;
        telemetry.trial_wall_seconds = std::chrono::duration<double>(
            Clock::now() - temporal_trial_started_).count();
        telemetry.temporal_counter_features = temporal_counter_values(telemetry);
        std::uint64_t counter_digest = 0xcbf29ce484222325ULL;
        for (const auto value : telemetry.temporal_counter_features) {
            counter_digest ^= frontier_mix(std::bit_cast<std::uint64_t>(value));
            counter_digest *= 0x100000001b3ULL;
        }
        std::ostringstream counter_stream;
        counter_stream << std::hex << std::setfill('0')
                       << std::setw(16) << counter_digest;
        telemetry.temporal_counter_hash = counter_stream.str();

        bool continue_qd1 = false;
        switch (frontier_probe_config_.mode) {
            case FrontierProbeMode::ForceTrialContinue:
                continue_qd1 = true;
                telemetry.decision_reason = "forced_trial_continue";
                break;
            case FrontierProbeMode::LearnedAfterTrial:
                continue_qd1 = learned_temporal_action();
                break;
            case FrontierProbeMode::CollectTrial:
                telemetry.decision_reason = "collected_trial_revert";
                break;
            case FrontierProbeMode::ForceTrialRevert:
                telemetry.decision_reason = "forced_trial_revert";
                break;
            default:
                throw std::logic_error("non-trial mode reached trial decision");
        }
        if (continue_qd1) {
            telemetry.action = "CONTINUE_QD1";
        } else {
            migrate_frontier_back_to_q0();
        }
    }

    void migrate_counterfactual_frontier_to_qd1() {
        const auto frontier_before = unprocessed_q0_.size();
        std::size_t drained = 0;
        std::size_t migrated = 0;
        std::size_t duplicate = 0;
        std::uint64_t hash_before = 0;
        std::uint64_t hash_after = 0;
        std::unordered_set<std::uint64_t> identifiers;
        identifiers.reserve(frontier_before);
        while (!unprocessed_q0_.empty()) {
            const auto value = unprocessed_q0_.top();
            unprocessed_q0_.pop();
            ++drained;
            const auto found = creation_sequence_ids_.find(value.first);
            if (found == creation_sequence_ids_.end()) {
                throw std::runtime_error(
                    "counterfactual migration creation sequence missing");
            }
            const auto creation_id = found->second;
            hash_before ^= frontier_mix(creation_id);
            duplicate += identifiers.insert(creation_id).second ? 0U : 1U;
            unprocessed_experimental_.push(qd1_entry(value, creation_id));
            hash_after ^= frontier_mix(creation_id);
            ++migrated;
        }
        if (frontier_before != drained || drained != migrated ||
            migrated != unprocessed_experimental_.size() ||
            hash_before != hash_after || duplicate != 0U) {
            throw std::runtime_error(
                "counterfactual frontier migration correctness redline");
        }
        proof_queue_policy_ = ProofQueuePolicy::QD1DeeperFirst;
    }

    [[nodiscard]] FrontierProbeSnapshot current_frontier_snapshot(
        std::size_t boundary
    ) const {
        FrontierProbeSnapshot snapshot;
        snapshot.reached = true;
        snapshot.graph_built = frontier_probe_telemetry_.graph_built;
        snapshot.boundary = boundary;
        snapshot.processed_labels = processed_labels_;
        snapshot.extended_labels = extended_labels();
        snapshot.dominated_labels = dominated_labels();
        snapshot.dominance_candidate_checks = dominance_candidate_checks();
        snapshot.subset_dominance_candidate_checks =
            subset_dominance_candidate_checks();
        snapshot.subset_dominance_rejected_labels =
            subset_dominance_rejected_labels();
        snapshot.max_visited_bucket_size = max_visited_bucket_size();
        snapshot.negative_label_event_count =
            best_reduced_cost_event_count_total_;
        snapshot.best_true_reduced_cost = best_reduced_cost_;
        snapshot.graph_hash = frontier_probe_telemetry_.graph_hash;
        snapshot.frontier_size = frontier_probe_telemetry_.frontier_size;
        snapshot.nonempty_node_count =
            frontier_probe_telemetry_.nonempty_node_count;
        snapshot.edge_count = frontier_probe_telemetry_.edge_count;
        snapshot.graph_build_wall_seconds =
            frontier_probe_telemetry_.graph_build_wall_seconds;
        snapshot.node_features = frontier_probe_telemetry_.node_features;
        snapshot.edges = frontier_probe_telemetry_.edges;
        snapshot.context_features = frontier_probe_telemetry_.context_features;
        return snapshot;
    }

    void record_frontier_snapshot(std::size_t boundary) {
        frontier_probe_telemetry_.snapshots.push_back(
            current_frontier_snapshot(boundary));
    }

    void maybe_run_frontier_probe() {
        if (frontier_probe_config_.mode == FrontierProbeMode::Disabled ||
            proof_queue_policy_ != ProofQueuePolicy::Q0PartialCost) {
            return;
        }
        const bool observation_due =
            frontier_observation_index_ <
                frontier_probe_config_.observation_boundaries.size() &&
            processed_labels_ == frontier_probe_config_.observation_boundaries[
                                     frontier_observation_index_];
        const bool decision_due =
            !frontier_probe_decided_ &&
            processed_labels_ == frontier_probe_config_.processed_label_boundary;
        if (!observation_due && !decision_due) {
            return;
        }
        if (decision_due) {
            frontier_probe_decided_ = true;
            frontier_probe_telemetry_.reached = true;
        }
        if (unprocessed_q0_.empty()) {
            frontier_probe_telemetry_.decision_reason = "frontier_empty";
            if (observation_due) {
                record_frontier_snapshot(
                    frontier_probe_config_.observation_boundaries[
                        frontier_observation_index_]);
                ++frontier_observation_index_;
            }
            return;
        }
        build_frontier_graph();
        if (observation_due) {
            record_frontier_snapshot(
                frontier_probe_config_.observation_boundaries[
                    frontier_observation_index_]);
            ++frontier_observation_index_;
        }
        if (!decision_due) {
            return;
        }
        if (!frontier_probe_telemetry_.graph_built) {
            return;
        }
        if (temporal_trial_mode()) {
            start_temporal_trial();
            return;
        }
        bool switch_to_qd1 = false;
        if (frontier_probe_config_.mode == FrontierProbeMode::CollectForceQ0) {
            frontier_probe_telemetry_.decision_reason = "forced_continue_q0";
        } else if (frontier_probe_config_.mode == FrontierProbeMode::ForceQD1) {
            frontier_probe_telemetry_.decision_reason = "forced_switch_qd1";
            switch_to_qd1 = true;
        } else if (frontier_probe_config_.mode == FrontierProbeMode::Learned) {
            switch_to_qd1 = learned_frontier_action();
        }
        if (switch_to_qd1) {
            migrate_frontier_to_qd1();
        } else {
            frontier_probe_telemetry_.action = "CONTINUE_Q0";
            creation_sequence_ids_.clear();
        }
    }

    Pair next_label_iterator() override {
        if (maybe_run_counterfactual_prefix()) {
            return Pair{};
        }
        maybe_run_frontier_probe();
        maybe_finish_temporal_trial();
        if (
            proof_queue_policy_ ==
            ProofQueuePolicy::Q0PartialCost
        ) {
            if (unprocessed_q0_.empty()) {
                return Pair{};
            }
            auto value = unprocessed_q0_.top();
            unprocessed_q0_.pop();
            ++processed_labels_;
            if (frontier_probe_decided_) {
                ++frontier_probe_telemetry_.q0_post_probe_pops;
                if (temporal_trial_mode()) {
                    creation_sequence_ids_.erase(value.first);
                }
            } else if (
                frontier_probe_config_.mode != FrontierProbeMode::Disabled &&
                counterfactual_prefix_config_.mode ==
                    CounterfactualPrefixMode::Disabled
            ) {
                creation_sequence_ids_.erase(value.first);
            }
            return value;
        }
        if (unprocessed_experimental_.empty()) {
            if (temporal_trial_mode() &&
                frontier_probe_telemetry_.trial_started &&
                !frontier_probe_telemetry_.trial_completed) {
                frontier_probe_telemetry_.trial_pops = processed_labels_ -
                    frontier_probe_config_.processed_label_boundary;
                frontier_probe_telemetry_.trial_wall_seconds =
                    std::chrono::duration<double>(
                        Clock::now() - temporal_trial_started_).count();
                frontier_probe_telemetry_.action =
                    "TRIAL_EXHAUSTED_BEFORE_DECISION";
                frontier_probe_telemetry_.decision_reason =
                    "frontier_exhausted_before_trial_budget";
            }
            return Pair{};
        }
        auto entry = unprocessed_experimental_.top();
        unprocessed_experimental_.pop();
        ++processed_labels_;
        if (frontier_probe_decided_ && frontier_probe_telemetry_.switched_to_qd1) {
            ++frontier_probe_telemetry_.qd1_post_probe_pops;
            if (frontier_probe_telemetry_.trial_started &&
                !frontier_probe_telemetry_.trial_completed) {
                frontier_probe_telemetry_.trial_pops = processed_labels_ -
                    frontier_probe_config_.processed_label_boundary;
            }
        }
        if (trace_ != nullptr) {
            trace_->record_label(
                *entry.value.first,
                *model_,
                entry.guidance_score);
        }
        return entry.value;
    }

    [[nodiscard]] std::size_t number_of_labels() const override {
        return (
            proof_queue_policy_ ==
                ProofQueuePolicy::Q0PartialCost
            ? unprocessed_q0_.size()
            : unprocessed_experimental_.size()
        );
    }

    void add_new_unprocessed_label(const Pair& value) override {
        if (
            proof_queue_policy_ ==
            ProofQueuePolicy::Q0PartialCost
        ) {
            // Keep the production Q0 container and comparator byte-for-byte
            // equivalent to the historical path.
            if (trace_ != nullptr) {
                trace_->record_label(*value.first, *model_, 0.0);
            }
            if ((frontier_probe_config_.mode != FrontierProbeMode::Disabled &&
                 (!frontier_probe_decided_ || temporal_trial_mode())) ||
                counterfactual_prefix_config_.mode !=
                    CounterfactualPrefixMode::Disabled) {
                creation_sequence_ids_[value.first] =
                    next_creation_sequence_id_++;
            }
            unprocessed_q0_.push(value);
            return;
        }
        const auto& state = value.first->get_resource()
                                .template get_component<JourneyResource>(0)
                                .get_value()
                                .get_value()
                                .state();
        const double partial_cost = value.first->get_cost();
        double primary_key = 0.0;
        double secondary_key = 0.0;
        std::int64_t rc_bucket = 0;
        double guidance_score = state.guidance_score;
        if (
            proof_queue_policy_ ==
            ProofQueuePolicy::QD1DeeperFirst
        ) {
            primary_key = -static_cast<double>(state.visited_count);
        } else if (
            proof_queue_policy_ ==
            ProofQueuePolicy::QB1OptimisticCompletion
        ) {
            const double remaining_positive_dual = std::max(
                0.0,
                model_->positive_task_dual_sum -
                    state.auxiliary.regular.positive_task_dual_reward);
            primary_key = partial_cost - remaining_positive_dual;
        } else if (
            proof_queue_policy_ ==
            ProofQueuePolicy::QG1GuidancePotential
        ) {
            // Keep QD1's proven deeper-first skeleton. Guidance is allowed to
            // reorder only labels at the same depth and in the same
            // deterministic coarse partial-RC bucket. Exact partial RC and
            // creation id remain deterministic fallbacks. With all-zero
            // guidance this is exactly the QD1 total order.
            primary_key = -static_cast<double>(state.visited_count);
            secondary_key = std::floor(
                partial_cost / proof_queue_guidance_bucket_width_);
        } else if (
            proof_queue_policy_ ==
                ProofQueuePolicy::QG2LabelStatePotential ||
            proof_queue_policy_ ==
                ProofQueuePolicy::QGR1DepthResidualGAT
        ) {
            const bool sample =
                guidance_stats_->label_state_scored_count % 1024U == 0U;
            const auto sample_started = sample ? Clock::now() : Clock::time_point{};
            guidance_score = qg2_label_state_priority(
                *model_, state, partial_cost);
            if (sample) {
                guidance_stats_->scoring_sample_wall_seconds +=
                    std::chrono::duration<double>(
                        Clock::now() - sample_started).count();
                ++guidance_stats_->scoring_sample_count;
            }
            ++guidance_stats_->label_state_scored_count;
            if (std::abs(guidance_score) > 1.0e-12) {
                ++guidance_stats_->nonzero_score_count;
            }
            rc_bucket = reduced_cost_bucket(
                partial_cost, proof_queue_guidance_bucket_width_);
            if (
                proof_queue_policy_ ==
                ProofQueuePolicy::QGR1DepthResidualGAT
            ) {
                // QGR1 is a strict residual of QD1: learned scores may act
                // only after terminal class, depth, and the narrow reduced-
                // cost bucket have tied.  With zero scores this is the same
                // deterministic total order as QD1 up to the deliberately
                // cached creation-id tie break used by experimental queues.
                primary_key = -static_cast<double>(state.visited_count);
            }
            const auto bucket_hash =
                std::hash<std::int64_t>{}(rc_bucket) %
                guidance_stats_->bucket_hashes.size();
            guidance_stats_->bucket_hashes.set(bucket_hash);
        }
        const auto creation_sequence_id = next_creation_sequence_id_++;
        const auto entry = CachedQueueEntry{
            .value = value,
            .can_terminate = (
                state.at_depot && state.task_visit_count > 0
            ),
            .primary_key = primary_key,
            .secondary_key = secondary_key,
            .reduced_cost_bucket = rc_bucket,
            .guidance_score = guidance_score,
            .partial_cost = partial_cost,
            .creation_sequence_id = creation_sequence_id,
        };
        if (counterfactual_prefix_config_.mode !=
            CounterfactualPrefixMode::Disabled) {
            creation_sequence_ids_[value.first] = creation_sequence_id;
        }
        if (trace_ != nullptr) {
            trace_->record_label(
                *value.first,
                *model_,
                guidance_score);
        }
        unprocessed_experimental_.push(entry);
    }

    void prepareNextPhase() override {}

    void on_memory_pressure() override {
        // Exact mode configures pressure at the hard limit, and the upstream
        // main loop checks the hard limit first. Reaching this callback is a
        // certificate blocker, never permission to drop a label.
        this->memory_pressure_triggered_ = true;
    }

    void release_label_memory() override {
        unprocessed_q0_ = decltype(unprocessed_q0_){};
        unprocessed_experimental_ =
            decltype(unprocessed_experimental_)(
                GreaterCachedKey{guidance_stats_});
        creation_sequence_ids_.clear();
        counterfactual_base_label_ids_.clear();
        Base::release_label_memory();
    }

    std::shared_ptr<const Model> model_;
    ProofQueuePolicy proof_queue_policy_ =
        ProofQueuePolicy::Q0PartialCost;
    double proof_queue_guidance_bucket_width_ = 0.01;
    double negative_epsilon_ = 1.0e-6;
    std::shared_ptr<ProofQueuePotentialTrace> trace_;
    FrontierProbeConfig frontier_probe_config_;
    FrontierProbeTelemetry frontier_probe_telemetry_;
    bool frontier_probe_decided_ = false;
    std::size_t frontier_observation_index_ = 0;
    CounterfactualPrefixConfig counterfactual_prefix_config_;
    CounterfactualPrefixTelemetry counterfactual_prefix_telemetry_;
    std::size_t counterfactual_checkpoint_index_ = 0;
    std::unordered_set<std::uint64_t> counterfactual_base_label_ids_;
    std::unordered_map<const Label*, std::uint64_t> creation_sequence_ids_;
    std::shared_ptr<GuidanceStats> guidance_stats_;
    std::priority_queue<Pair, std::vector<Pair>, GreaterCost>
        unprocessed_q0_;
    std::priority_queue<
        CachedQueueEntry,
        std::vector<CachedQueueEntry>,
        GreaterCachedKey
    > unprocessed_experimental_;
    std::uint64_t next_creation_sequence_id_ = 0;
    std::size_t processed_labels_ = 0;
    static constexpr std::size_t max_best_reduced_cost_events_ = 512;
    Clock::time_point trace_started_{};
    Clock::time_point counterfactual_request_started_{};
    Clock::time_point counterfactual_boundary_started_{};
    Clock::time_point temporal_trial_started_{};
    bool counterfactual_timing_started_ = false;
    bool counterfactual_boundary_timing_started_ = false;
    bool trace_enabled_ = false;
    double first_true_negative_wall_time_seconds_ =
        std::numeric_limits<double>::infinity();
    std::size_t labels_processed_before_first_true_negative_ = 0;
    double best_reduced_cost_ = std::numeric_limits<double>::infinity();
    std::size_t best_reduced_cost_event_count_total_ = 0;
    std::vector<BestReducedCostEvent> best_reduced_cost_events_;
};

struct BuiltGraph {
    std::unique_ptr<rcspp::ResourceGraph<JourneyResource>> graph;
    std::vector<Action> actions_by_arc_id;
};

struct CachedGraph {
    std::string key;
    std::shared_ptr<Model> model;
    BuiltGraph built;
};

std::list<std::unique_ptr<CachedGraph>>& graph_cache() {
    static std::list<std::unique_ptr<CachedGraph>> value;
    return value;
}

std::mutex& graph_cache_mutex() {
    static std::mutex value;
    return value;
}

std::size_t& graph_cache_build_count() {
    static std::size_t value = 0;
    return value;
}

std::size_t& graph_cache_hit_count() {
    static std::size_t value = 0;
    return value;
}

std::string graph_cache_key(const Model& model, const SolveParams& params) {
    if (model.structure_hash.empty()) {
        return {};
    }
    return model.structure_hash + ":d=" + std::to_string(params.dominance_epsilon) +
           ":r=" + std::to_string(params.resource_epsilon) +
           ":tw=no_task_wait_base_departure_shift_v1" +
           ":dssr=" + (params.dssr_enabled ? params.dssr_policy_version
                                            : std::string{"off"});
}

void refresh_dynamic_model(const Model& source, Model* target) {
    if (source.tasks.size() != target->tasks.size()) {
        throw std::invalid_argument("native graph cache task-count mismatch");
    }
    for (std::size_t index = 0; index < source.tasks.size(); ++index) {
        if (source.tasks[index].id != target->tasks[index].id ||
            source.tasks[index].index != target->tasks[index].index) {
            throw std::invalid_argument("native graph cache task mapping mismatch");
        }
        target->tasks[index].dual = source.tasks[index].dual;
        target->tasks[index].guidance_priority =
            source.tasks[index].guidance_priority;
    }
    if (source.arcs.size() != target->arcs.size()) {
        throw std::invalid_argument("native graph cache arc-count mismatch");
    }
    for (std::size_t index = 0; index < source.arcs.size(); ++index) {
        if (source.arcs[index].source != target->arcs[index].source ||
            source.arcs[index].target != target->arcs[index].target ||
            source.arcs[index].path_type != target->arcs[index].path_type) {
            throw std::invalid_argument("native graph cache arc mapping mismatch");
        }
        target->arcs[index].guidance_priority =
            source.arcs[index].guidance_priority;
    }
    target->cost_coefficient = source.cost_coefficient;
    target->risk_coefficient = source.risk_coefficient;
    target->completion_coefficient = source.completion_coefficient;
    target->fleet_dual = source.fleet_dual;
    target->branch_decisions = source.branch_decisions;
    target->cuts = source.cuts;
    target->guidance_task_arc_enabled = source.guidance_task_arc_enabled;
    target->guidance_label_state_enabled =
        source.guidance_label_state_enabled;
    target->guidance_label_state_coefficients =
        source.guidance_label_state_coefficients;
    target->dssr_relaxation_enabled = source.dssr_relaxation_enabled;
    target->dssr_critical_task_mask = source.dssr_critical_task_mask;
    target->dssr_branch_task_mask = source.dssr_branch_task_mask;
    target->ng_dssr_memory_enabled = source.ng_dssr_memory_enabled;
    target->ng_dssr_task_memory_masks =
        source.ng_dssr_task_memory_masks;
}

BuiltGraph build_graph(std::shared_ptr<const Model> model, const SolveParams& params) {
    const std::size_t task_count = model->tasks.size();
    const std::size_t sink_id = task_count + 1;
    auto graph = std::make_unique<rcspp::ResourceGraph<JourneyResource>>();
    State initial_state;
    if (ng_dssr_active(*model)) {
        initial_state.auxiliary.ng_memory = VisitedMask{};
    }
    auto initial = JourneyValue::from_state(std::move(initial_state));
    graph->add_resource<JourneyResource>(
        std::make_unique<JourneyExtension>(model),
        std::make_unique<JourneyFeasibility>(model, sink_id),
        std::make_unique<JourneyCost>(model),
        std::make_unique<JourneyDominance>(model, params.dominance_epsilon,
                                           params.resource_epsilon),
        std::make_tuple(initial));

    graph->add_node(0, true, false);
    for (std::size_t index = 0; index < task_count; ++index) {
        graph->add_node(index + 1, false, false);
    }
    graph->add_node(sink_id, false, true);

    std::unordered_map<std::string, std::size_t> node_by_name{{"depot", 0}};
    std::unordered_map<std::string, std::size_t> task_index_by_name;
    for (const auto& task : model->tasks) {
        node_by_name[task.id] = task.index + 1;
        task_index_by_name[task.id] = task.index;
    }

    std::vector<Action> actions;
    auto add_action = [&](const Action& action, std::size_t origin, std::size_t destination) {
        auto action_value = JourneyValue::from_action(action);
        auto& arc = graph->add_arc<JourneyResource>(
            std::make_tuple(std::make_tuple(action_value)),
            origin, destination, 0.0);
        if (actions.size() <= arc.id) {
            actions.resize(arc.id + 1);
        }
        actions[arc.id] = action;
    };

    auto option_is_dominated = [&](const ArcData& candidate) {
        constexpr double epsilon = 1.0e-12;
        return std::ranges::any_of(model->arcs, [&](const ArcData& other) {
            if (candidate.source != other.source || candidate.target != other.target ||
                candidate.path_type == other.path_type) {
                return false;
            }
            const bool same_travel_time =
                std::abs(other.travel_time - candidate.travel_time) <= epsilon;
            const bool no_worse = same_travel_time &&
                                  other.energy <= candidate.energy + epsilon &&
                                  other.risk <= candidate.risk + epsilon &&
                                  other.distance <= candidate.distance + epsilon &&
                                  other.shadow <= candidate.shadow + epsilon;
            const bool strictly_better = other.energy < candidate.energy - epsilon ||
                                         other.risk < candidate.risk - epsilon ||
                                         other.distance < candidate.distance - epsilon ||
                                         other.shadow < candidate.shadow - epsilon;
            return no_worse && strictly_better;
        });
    };

    for (std::size_t model_arc_index = 0;
         model_arc_index < model->arcs.size();
         ++model_arc_index) {
        const auto& arc = model->arcs[model_arc_index];
        if (arc.source == "depot" && arc.target == "depot") {
            continue;
        }
        // Under no-task-wait timing, a slower arc may absorb time that would
        // otherwise require an infeasible retroactive depot departure shift.
        // Therefore only equal-travel alternatives may dominate one another.
        if (option_is_dominated(arc)) {
            continue;
        }
        const auto origin_it = node_by_name.find(arc.source);
        const auto destination_it = node_by_name.find(arc.target);
        if (origin_it == node_by_name.end() || destination_it == node_by_name.end()) {
            continue;
        }
        Action action;
        action.model_arc_index = model_arc_index;
        action.path_type = arc.path_type;
        action.travel_time = arc.travel_time;
        action.energy = arc.energy;
        action.risk = arc.risk;
        action.distance = arc.distance;
        action.shadow = arc.shadow;
        if (arc.target == "depot") {
            action.kind = ActionKind::ReturnDepot;
        } else {
            action.kind = ActionKind::VisitTask;
            action.task_index = task_index_by_name.at(arc.target);
        }
        add_action(action, origin_it->second, destination_it->second);
    }
    add_action(Action{.kind = ActionKind::Terminate}, 0, sink_id);
    return {.graph = std::move(graph), .actions_by_arc_id = std::move(actions)};
}

Route reconstruct_route(const rcspp::Solution& solution, const Model& model,
                        const std::vector<Action>& actions) {
    Route route;
    route.reduced_cost = solution.cost;
    route.arc_ids = solution.path_arc_ids;
    SortiePath current;
    for (const auto arc_id : solution.path_arc_ids) {
        if (arc_id >= actions.size()) {
            throw std::runtime_error("solution contains unknown arc id");
        }
        const auto& action = actions[arc_id];
        if (action.kind == ActionKind::VisitTask) {
            current.tasks.push_back(model.tasks.at(action.task_index).id);
            current.path_types.push_back(action.path_type);
        } else if (action.kind == ActionKind::ReturnDepot) {
            if (current.tasks.empty()) {
                throw std::runtime_error("empty sortie in native route");
            }
            current.path_types.push_back(action.path_type);
            route.sorties.push_back(std::move(current));
            current = SortiePath{};
        } else if (!current.tasks.empty()) {
            throw std::runtime_error("native route terminated before returning to depot");
        }
    }
    if (!current.tasks.empty() || route.sorties.empty()) {
        throw std::runtime_error("native route reconstruction is incomplete");
    }
    return route;
}

}  // namespace

std::array<double, 3> evaluate_frontier_gat_seed(
    const FrontierGatSeedModel& model,
    const FrontierGatBundle& bundle,
    const FrontierProbeTelemetry& graph
) {
    if (!frontier_bundle_is_valid(bundle)) {
        throw std::invalid_argument("invalid V7 frontier GAT bundle");
    }
    return frontier_gat_forward(model, bundle, graph);
}

std::array<double, 3> evaluate_counterfactual_gat_seed(
    const FrontierGatSeedModel& model,
    const CounterfactualPortableBundle& bundle,
    const CounterfactualPortableTriplet& triplet
) {
    if (bundle.schema_version !=
            "lunar_ice_bpc.p0v5_counterfactual_prefix_gat_native_bundle.v1" ||
        bundle.node_mean.size() != kCounterfactualPortableNodeFeatureCount ||
        bundle.node_scale.size() != kCounterfactualPortableNodeFeatureCount ||
        bundle.edge_mean.size() != kCounterfactualPortableEdgeFeatureCount ||
        bundle.edge_scale.size() != kCounterfactualPortableEdgeFeatureCount ||
        bundle.context_mean.size() != kFrontierContextFeatureCount ||
        bundle.context_scale.size() != kFrontierContextFeatureCount ||
        bundle.counter_mean.size() != kCounterfactualCounterFeatureCount ||
        bundle.counter_scale.size() != kCounterfactualCounterFeatureCount ||
        !(bundle.layer_norm_epsilon > 0.0)) {
        throw std::invalid_argument("invalid V8 counterfactual GAT bundle");
    }
    auto normalize = [](double value, double mean, double scale) {
        if (!std::isfinite(value) || !std::isfinite(mean) ||
            !std::isfinite(scale) || !(scale > 0.0)) {
            throw std::invalid_argument(
                "counterfactual normalization value invalid");
        }
        return (value - mean) / scale;
    };
    const auto& node_weight = frontier_tensor(
        model, "node_encoder.weight",
        {kFrontierHiddenSize, kCounterfactualPortableNodeFeatureCount});
    const auto& node_bias = frontier_tensor(
        model, "node_encoder.bias", {kFrontierHiddenSize});
    const auto& edge_weight = frontier_tensor(
        model, "edge_encoder.weight",
        {kFrontierHiddenSize, kCounterfactualPortableEdgeFeatureCount});
    const auto& edge_bias = frontier_tensor(
        model, "edge_encoder.bias", {kFrontierHiddenSize});
    const auto& context_weight = frontier_tensor(
        model, "context_encoder.weight",
        {kFrontierHiddenSize, kFrontierContextFeatureCount});
    const auto& context_bias = frontier_tensor(
        model, "context_encoder.bias", {kFrontierHiddenSize});
    const auto& pool_weight = frontier_tensor(
        model, "attention_pool.weight", {1U, kFrontierHiddenSize});
    const auto& pool_bias = frontier_tensor(
        model, "attention_pool.bias", {1U});

    auto encode = [&](const CounterfactualPortableGraph& graph) {
        if (graph.node_features.empty() || graph.edges.empty()) {
            throw std::invalid_argument(
                "counterfactual portable graph cannot be empty");
        }
        std::vector<std::vector<double>> nodes;
        nodes.reserve(graph.node_features.size());
        for (const auto& raw : graph.node_features) {
            if (raw.size() != kCounterfactualPortableNodeFeatureCount) {
                throw std::invalid_argument(
                    "counterfactual node feature shape mismatch");
            }
            std::vector<double> row(raw.size());
            for (std::size_t index = 0; index < row.size(); ++index) {
                row[index] = normalize(
                    raw[index], bundle.node_mean[index],
                    bundle.node_scale[index]);
            }
            nodes.push_back(frontier_dense(row, node_weight, node_bias));
            frontier_relu(&nodes.back());
        }
        std::vector<std::vector<double>> encoded_edges;
        encoded_edges.reserve(graph.edges.size());
        for (const auto& raw : graph.edges) {
            std::vector<double> row(kCounterfactualPortableEdgeFeatureCount);
            for (std::size_t index = 0; index < row.size(); ++index) {
                row[index] = normalize(
                    raw.features[index], bundle.edge_mean[index],
                    bundle.edge_scale[index]);
            }
            encoded_edges.push_back(
                frontier_dense(row, edge_weight, edge_bias));
            frontier_relu(&encoded_edges.back());
        }
        nodes = frontier_gat_layer(
            nodes, encoded_edges, graph.edges, model, 0U,
            bundle.layer_norm_epsilon);
        nodes = frontier_gat_layer(
            nodes, encoded_edges, graph.edges, model, 1U,
            bundle.layer_norm_epsilon);

        std::vector<double> node_mean(kFrontierHiddenSize, 0.0);
        std::vector<double> node_max(
            kFrontierHiddenSize,
            -std::numeric_limits<double>::infinity());
        std::vector<double> attention_scores;
        double max_attention = -std::numeric_limits<double>::infinity();
        for (const auto& node : nodes) {
            for (std::size_t index = 0; index < kFrontierHiddenSize; ++index) {
                node_mean[index] +=
                    node[index] / static_cast<double>(nodes.size());
                node_max[index] = std::max(node_max[index], node[index]);
            }
            const auto score =
                frontier_dense(node, pool_weight, pool_bias).front();
            attention_scores.push_back(score);
            max_attention = std::max(max_attention, score);
        }
        double denominator = 0.0;
        for (auto& score : attention_scores) {
            score = std::exp(score - max_attention);
            denominator += score;
        }
        if (!(denominator > 0.0)) {
            throw std::invalid_argument(
                "counterfactual attention pool invalid");
        }
        std::vector<double> attention_pool(kFrontierHiddenSize, 0.0);
        for (std::size_t index = 0; index < nodes.size(); ++index) {
            const auto probability = attention_scores[index] / denominator;
            for (std::size_t hidden = 0; hidden < kFrontierHiddenSize; ++hidden) {
                attention_pool[hidden] +=
                    probability * nodes[index][hidden];
            }
        }
        std::vector<double> edge_mean(kFrontierHiddenSize, 0.0);
        std::vector<double> edge_max(
            kFrontierHiddenSize,
            -std::numeric_limits<double>::infinity());
        for (const auto& edge : encoded_edges) {
            for (std::size_t hidden = 0; hidden < kFrontierHiddenSize; ++hidden) {
                edge_mean[hidden] += edge[hidden] /
                                     static_cast<double>(encoded_edges.size());
                edge_max[hidden] = std::max(edge_max[hidden], edge[hidden]);
            }
        }
        std::vector<double> raw_context(kFrontierContextFeatureCount);
        for (std::size_t index = 0; index < raw_context.size(); ++index) {
            raw_context[index] = normalize(
                graph.context_features[index], bundle.context_mean[index],
                bundle.context_scale[index]);
        }
        auto context = frontier_dense(
            raw_context, context_weight, context_bias);
        frontier_relu(&context);
        std::vector<double> output;
        output.reserve(96U);
        output.insert(output.end(), node_mean.begin(), node_mean.end());
        output.insert(output.end(), node_max.begin(), node_max.end());
        output.insert(
            output.end(), attention_pool.begin(), attention_pool.end());
        output.insert(output.end(), edge_mean.begin(), edge_mean.end());
        output.insert(output.end(), edge_max.begin(), edge_max.end());
        output.insert(output.end(), context.begin(), context.end());
        return output;
    };

    const auto base = encode(triplet.base);
    const auto q0 = encode(triplet.q0);
    const auto qd1 = encode(triplet.qd1);
    std::vector<double> combined;
    combined.reserve(504U);
    combined.insert(combined.end(), base.begin(), base.end());
    combined.insert(combined.end(), q0.begin(), q0.end());
    combined.insert(combined.end(), qd1.begin(), qd1.end());
    for (std::size_t index = 0; index < q0.size(); ++index) {
        combined.push_back(qd1[index] - q0[index]);
    }
    for (std::size_t index = 0; index < q0.size(); ++index) {
        combined.push_back(std::abs(qd1[index] - q0[index]));
    }
    for (std::size_t index = 0; index < triplet.counter_features.size(); ++index) {
        combined.push_back(normalize(
            triplet.counter_features[index], bundle.counter_mean[index],
            bundle.counter_scale[index]));
    }
    const auto& head0_weight = frontier_tensor(
        model, "head.0.weight", {32U, 504U});
    const auto& head0_bias = frontier_tensor(
        model, "head.0.bias", {32U});
    const auto& head2_weight = frontier_tensor(
        model, "head.2.weight", {3U, 32U});
    const auto& head2_bias = frontier_tensor(
        model, "head.2.bias", {3U});
    auto hidden = frontier_dense(combined, head0_weight, head0_bias);
    frontier_relu(&hidden);
    const auto logits = frontier_dense(hidden, head2_weight, head2_bias);
    return {
        frontier_sigmoid(logits[0]),
        frontier_sigmoid(logits[1]),
        frontier_sigmoid(logits[2]),
    };
}

std::array<double, 3> evaluate_temporal_gat_seed(
    const FrontierGatSeedModel& model,
    const TemporalGatBundle& bundle,
    const FrontierProbeSnapshot& cell_t0,
    const FrontierProbeSnapshot& cell_tk,
    const TemporalPortableGraph& graph_t0,
    const TemporalPortableGraph& graph_tk,
    const std::array<double, kTemporalGatCounterFeatureCount>& counters,
    const std::array<double, kFrontierContextFeatureCount>& context,
    std::size_t scale
) {
    if (!temporal_bundle_is_valid(bundle) || bundle.selected_scale != scale) {
        throw std::invalid_argument("invalid Temporal-GAT v2 bundle");
    }
    return temporal_gat_forward(
        model, bundle, cell_t0, cell_tk, graph_t0, graph_tk,
        counters, context, scale);
}

TemporalGatDecision decide_temporal_gat_outputs(
    const TemporalGatBundle& bundle,
    const std::vector<std::array<double, 3>>& outputs
) {
    if (outputs.empty()) {
        throw std::invalid_argument("Temporal-GAT ensemble is empty");
    }
    double benefit_sum = 0.0;
    double benefit_min = 1.0;
    double benefit_max = 0.0;
    double gain_min = 1.0;
    double gain_max = 0.0;
    double adverse_min = 1.0;
    double adverse_max = 0.0;
    for (const auto& output : outputs) {
        if (std::ranges::any_of(output, [](double value) {
                return !std::isfinite(value) || value < 0.0 || value > 1.0;
            })) {
            throw std::invalid_argument("invalid Temporal-GAT output");
        }
        benefit_sum += output[0];
        benefit_min = std::min(benefit_min, output[0]);
        benefit_max = std::max(benefit_max, output[0]);
        gain_min = std::min(gain_min, output[1]);
        gain_max = std::max(gain_max, output[1]);
        adverse_min = std::min(adverse_min, output[2]);
        adverse_max = std::max(adverse_max, output[2]);
    }
    TemporalGatDecision decision;
    decision.p_benefit = frontier_calibrated_probability(
        benefit_sum / static_cast<double>(outputs.size()),
        bundle.benefit_calibration);
    decision.positive_gain = std::clamp(
        gain_min * bundle.gain_scale, 0.0, 1.0);
    decision.p_adverse = frontier_calibrated_probability(
        adverse_max, bundle.adverse_calibration);
    decision.disagreement = std::max({
        benefit_max - benefit_min,
        gain_max - gain_min,
        adverse_max - adverse_min,
    });
    decision.expected_gain = decision.p_benefit * decision.positive_gain;
    decision.risk_score = decision.expected_gain -
                          bundle.adverse_penalty * decision.p_adverse;
    decision.continue_qd1 = bundle.controller_kind != "temporal_gat"
        ? (decision.p_benefit >= 0.5 &&
           decision.p_adverse <= 0.5 &&
           decision.positive_gain > 0.0)
        : (decision.p_benefit >= bundle.minimum_benefit_probability &&
           decision.p_adverse <= bundle.maximum_adverse_probability &&
           decision.expected_gain >= bundle.minimum_expected_gain &&
           decision.risk_score > 0.0 &&
           decision.disagreement <= bundle.maximum_disagreement);
    return decision;
}

SolveOutput solve_once(const Model& input_model, const SolveParams& params) {
    if (input_model.tasks.empty() || input_model.tasks.size() > 100) {
        throw std::invalid_argument("native v1 requires 1..100 tasks");
    }
    if (
        !std::isfinite(params.proof_queue_guidance_bucket_width) ||
        params.proof_queue_guidance_bucket_width <= 0.0
    ) {
        throw std::invalid_argument(
            "proof queue guidance bucket width must be finite and positive");
    }
    if (params.exact_admission_batch_size == 0U) {
        throw std::invalid_argument(
            "exact admission batch size must be positive");
    }
    if (
        params.exact_raw_negative_pool_size <
        params.exact_admission_batch_size
    ) {
        throw std::invalid_argument(
            "exact raw negative pool must cover the admission batch");
    }
    if (params.exact_raw_negative_pool_size > 4096U) {
        throw std::invalid_argument(
            "exact raw negative pool exceeds the bounded interface");
    }
    if (
        params.exact_negative_escape_enabled &&
        (!params.exact_proof || params.dssr_enabled)
    ) {
        throw std::invalid_argument(
            "negative escape is elementary exact-proof only");
    }
    if (
        params.exact_negative_escape_enabled &&
        params.exact_negative_escape_policy_id !=
            "diverse_raw_4x_then_p0v4_selector_v1"
    ) {
        throw std::invalid_argument(
            "unsupported exact negative escape policy");
    }
    if (input_model.cost_coefficient < 0.0 || input_model.risk_coefficient < 0.0 ||
        input_model.completion_coefficient < 0.0 || input_model.recharge_power <= 0.0) {
        throw std::invalid_argument(
            "native v1 requires non-negative objective coefficients and positive recharge power");
    }
    if (input_model.cuts.size() > kMaxActiveCuts) {
        throw std::invalid_argument("native v1 supports at most 16 active cuts");
    }
    for (const auto& task : input_model.tasks) {
        if (!std::isfinite(task.guidance_priority)) {
            throw std::invalid_argument("native task guidance priority must be finite");
        }
    }
    for (const auto& arc : input_model.arcs) {
        if (!std::isfinite(arc.guidance_priority)) {
            throw std::invalid_argument("native arc guidance priority must be finite");
        }
    }
    for (const auto coefficient :
         input_model.guidance_label_state_coefficients) {
        if (!std::isfinite(coefficient)) {
            throw std::invalid_argument(
                "native label-state guidance coefficient must be finite");
        }
    }
    if (
        input_model.guidance_label_state_enabled &&
        params.proof_queue_policy !=
            ProofQueuePolicy::QG2LabelStatePotential &&
        params.proof_queue_policy !=
            ProofQueuePolicy::QGR1DepthResidualGAT
    ) {
        throw std::invalid_argument(
            "label-state guidance requires QG2 or QGR1 proof queue policy");
    }
    const bool counterfactual_prefix_active =
        params.counterfactual_prefix.mode !=
        CounterfactualPrefixMode::Disabled;
    if (counterfactual_prefix_active) {
        const auto& prefix = params.counterfactual_prefix;
        if (!params.exact_proof || params.dssr_enabled ||
            params.proof_queue_policy != ProofQueuePolicy::Q0PartialCost ||
            params.frontier_probe.mode != FrontierProbeMode::Disabled ||
            prefix.processed_label_boundary != 4096U ||
            prefix.label_sample_cap == 0U ||
            prefix.label_sample_cap > kCounterfactualLabelSampleCap ||
            !prefix.telemetry_only || !prefix.public_routes_forbidden ||
            !prefix.certificate_forbidden ||
            !std::ranges::is_sorted(prefix.rollout_checkpoints) ||
            prefix.rollout_checkpoints.front() == 0U ||
            std::ranges::find(
                prefix.rollout_checkpoints,
                prefix.maximum_rollout_budget) ==
                prefix.rollout_checkpoints.end() ||
            std::ranges::adjacent_find(prefix.rollout_checkpoints) !=
                prefix.rollout_checkpoints.end()) {
            throw std::invalid_argument(
                "counterfactual prefix contract is invalid");
        }
    }
    if (
        params.dssr_enabled &&
        (params.proof_queue_policy ==
             ProofQueuePolicy::QG2LabelStatePotential ||
         params.proof_queue_policy ==
             ProofQueuePolicy::QGR1DepthResidualGAT)
    ) {
        throw std::invalid_argument(
            "label-state guidance is unavailable with DSSR");
    }
    if (
        params.proof_queue_label_trace_enabled &&
        params.proof_queue_label_trace_max_rows == 0U
    ) {
        throw std::invalid_argument(
            "proof queue label trace requires a positive row limit");
    }
    if (
        params.proof_queue_label_trace_enabled &&
        params.proof_queue_label_trace_sampling_mode ==
            LabelTraceSamplingMode::QGR1StratifiedReservoirV1 &&
        (
            params.proof_queue_preference_cap_per_family == 0U ||
            params.proof_queue_surface_reservoir_count == 0U ||
            params.proof_queue_surface_labels_per_bucket < 2U ||
            params.proof_queue_witness_route_cap == 0U ||
            params.proof_queue_witness_ancestor_cap == 0U
        )
    ) {
        throw std::invalid_argument(
            "QGR1 stratified trace reservoir caps are invalid");
    }
    if (ng_dssr_active(input_model)) {
        const auto mask_words =
            (input_model.tasks.size() + 63U) / 64U;
        if (
            input_model.ng_dssr_task_memory_masks.size() !=
            input_model.tasks.size()
        ) {
            throw std::invalid_argument(
                "ng-DSSR requires one memory mask per task");
        }
        for (const auto& task : input_model.tasks) {
            if (
                task.index >=
                    input_model.ng_dssr_task_memory_masks.size() ||
                input_model.ng_dssr_task_memory_masks[task.index].size() !=
                    mask_words ||
                !mask_contains(
                    input_model.ng_dssr_task_memory_masks[task.index],
                    task.index
                )
            ) {
                throw std::invalid_argument(
                    "ng-DSSR task memory mask is invalid");
            }
        }
        if (
            input_model.guidance_task_arc_enabled ||
            input_model.guidance_label_state_enabled ||
            params.completion_bound_enabled ||
            params.proof_queue_potential_trace_enabled ||
            params.proof_queue_label_trace_enabled ||
            params.proof_queue_policy !=
                ProofQueuePolicy::Q0PartialCost
        ) {
            throw std::invalid_argument(
                "ng-DSSR auxiliary memory requires Q0 with guidance, "
                "completion bounds, and proof trace disabled");
        }
    }
    std::size_t expected_state_bit_offset = 0;
    for (const auto& cut : input_model.cuts) {
        if (cut.kind != CutKind::SubsetRow || cut.divisor != 2U) {
            throw std::invalid_argument("native live-cut v1 supports divisor-2 subset-row cuts only");
        }
        if (!std::isfinite(cut.dual)) {
            throw std::invalid_argument("native live-cut dual must be finite");
        }
        if (cut.task_mask.size() !=
            (input_model.tasks.size() + 63U) / 64U) {
            throw std::invalid_argument("native cut mask width is invalid");
        }
        if (cut.state_bit_offset != expected_state_bit_offset ||
            (cut.state_bit_width != 2U && cut.state_bit_width != 3U) ||
            cut.max_overlap == 0U ||
            cut.max_overlap >
                ((std::uint8_t{1} << cut.state_bit_width) - 1U) ||
            expected_state_bit_offset + cut.state_bit_width > 64U) {
            throw std::invalid_argument("native packed cut-state layout is invalid");
        }
        std::size_t member_count = 0;
        for (std::size_t word_index = 0; word_index < cut.task_mask.size();
             ++word_index) {
            auto word = cut.task_mask[word_index];
            if (word_index + 1U == cut.task_mask.size() &&
                input_model.tasks.size() % 64U != 0U) {
                const auto valid_bits = input_model.tasks.size() % 64U;
                const auto valid_mask =
                    (std::uint64_t{1} << valid_bits) - 1U;
                if ((word & ~valid_mask) != 0U) {
                    throw std::invalid_argument(
                        "native cut mask references an unknown task");
                }
            }
            member_count += std::popcount(word);
        }
        if (member_count != cut.max_overlap) {
            throw std::invalid_argument(
                "native packed cut-state overlap bound does not match cut tasks");
        }
        expected_state_bit_offset += cut.state_bit_width;
    }
    std::unique_lock cache_lock(graph_cache_mutex());
    auto& cache = graph_cache();
    const auto capacity = params.graph_cache_entries;
    while (cache.size() > capacity) {
        cache.pop_back();
    }
    const auto key = graph_cache_key(input_model, params);
    bool cache_hit = false;
    std::unique_ptr<CachedGraph> local_problem;
    CachedGraph* problem = nullptr;
    if (capacity > 0 && !key.empty()) {
        const auto found = std::find_if(cache.begin(), cache.end(), [&](const auto& row) {
            return row->key == key;
        });
        if (found != cache.end()) {
            cache.splice(cache.begin(), cache, found);
            problem = cache.front().get();
            refresh_dynamic_model(input_model, problem->model.get());
            cache_hit = true;
            ++graph_cache_hit_count();
        } else {
            auto model = std::make_shared<Model>(input_model);
            auto row = std::make_unique<CachedGraph>(
                CachedGraph{.key = key, .model = model, .built = build_graph(model, params)});
            problem = row.get();
            cache.push_front(std::move(row));
            ++graph_cache_build_count();
            while (cache.size() > capacity) {
                cache.pop_back();
            }
        }
    } else {
        auto model = std::make_shared<Model>(input_model);
        local_problem = std::make_unique<CachedGraph>(
            CachedGraph{.key = key, .model = model, .built = build_graph(model, params)});
        problem = local_problem.get();
        ++graph_cache_build_count();
    }
    auto& built = problem->built;
    const auto& model = problem->model;
    model->positive_task_dual_sum = 0.0;
    model->absolute_dual_sum = std::abs(model->fleet_dual);
    for (const auto& task : model->tasks) {
        model->positive_task_dual_sum += std::max(0.0, task.dual);
        model->absolute_dual_sum += std::abs(task.dual);
    }
    for (const auto& cut : model->cuts) {
        model->absolute_dual_sum += std::abs(cut.dual);
    }
    model->absolute_dual_sum = std::max(1.0, model->absolute_dual_sum);
    model->completion_bound_enabled = params.completion_bound_enabled;
    model->completion_bound_threshold = -params.negative_epsilon;
    model->completion_bound_evaluated_labels = 0;
    model->completion_bound_pruned_labels = 0;
    model->subset_dominance_enabled = params.subset_dominance_enabled;

    rcspp::AlgorithmBaseParams base;
    // Collect a wider raw pool in harvest mode. The Python audit keeps the
    // objective-best representative of each task set and caps the public
    // result at harvest_target, avoiding dozens of same-cover replacements.
    const auto dssr_raw_solution_target = std::min<std::size_t>(
        256U,
        std::clamp<std::size_t>(
            params.dssr_negative_batch_target,
            1U,
            64U
        ) * 4U
    );
    const bool exact_negative_escape_active =
        params.exact_proof &&
        params.exact_negative_escape_enabled &&
        !params.dssr_enabled;
    base.stop_after_X_solutions =
        params.dssr_enabled
            ? (
                  uses_dssr_batch(params)
                      ? dssr_raw_solution_target
                      : 1U
              )
            : (params.exact_proof
                   ? (
                         exact_negative_escape_active
                             ? params.exact_raw_negative_pool_size
                             : rcspp::MAX_INT
                     )
                   : std::min<std::size_t>(
                         rcspp::MAX_INT, params.harvest_target * 8U));
    base.return_dominated_solutions =
        params.dssr_enabled ||
        !params.exact_proof ||
        exact_negative_escape_active;
    base.num_labels_to_extend_by_node = rcspp::MAX_INT;
    base.num_max_phases = 1;
    base.max_iterations =
        params.exact_proof || params.harvest_max_processed_labels == 0U
            ? rcspp::MAX_INT
            : params.harvest_max_processed_labels;
    // Harvest calls are allowed to return any audited negative subset.  Bound
    // their internal search slice so a dual with fewer than harvest_target
    // negatives cannot consume the entire proof clock before the explicit
    // proof pass. Exact proof calls retain the caller's full remaining budget.
    base.timeout_s = params.exact_proof
                         ? params.timeout_seconds
                         : std::min(params.timeout_seconds, 10.0);
    base.max_memory_gb = params.max_memory_gb;
    // RSS sampling reads /proc and is material at scale 30.  Controlled A/B
    // runs showed that 32 and 256 made the same proof several times slower.
    // Retain upstream's 1000-label cadence; per-request label-pool release
    // prevents the cross-round accumulation that caused the observed 012/014
    // failures, while this check still enforces the single-call hard limit.
    base.memory_check_interval = params.dssr_enabled ? 250U : 1000U;
    // Exact mode must never discard truncated labels. At the hard threshold the upstream
    // main loop checks is_exceeded() before is_under_pressure(), so 1.0 disables trimming.
    base.memory_pressure_fraction = 1.0;
    base.memory_pressure_max_labels_per_node = rcspp::MAX_INT;
    // Keep the frontier alive only long enough to snapshot container-level
    // telemetry and all_labels_processed() below.  We then explicitly release
    // it before returning to Python.  Letting upstream release inside solve()
    // clears the custom per-node counters before they can be audited.
    base.release_after_solve = false;
    base.tolerance = params.dominance_epsilon;

    auto proof_queue_potential_trace =
        params.proof_queue_potential_trace_enabled ||
                params.proof_queue_label_trace_enabled
            ? std::make_shared<ProofQueuePotentialTrace>(
                  model->tasks.size(),
                  model->arcs.size(),
                  params.proof_queue_label_trace_enabled,
                  params.proof_queue_label_trace_max_rows,
                  params.proof_queue_guidance_bucket_width,
                  params.proof_queue_label_trace_sampling_mode,
                  params.proof_queue_label_trace_seed,
                  params.proof_queue_preference_cap_per_family,
                  params.proof_queue_surface_reservoir_count,
                  params.proof_queue_surface_labels_per_bucket,
                  params.proof_queue_witness_route_cap,
                  params.proof_queue_witness_ancestor_cap)
            : nullptr;
    auto dssr_pressure =
        is_dssr_v2(params) &&
                params.dssr_pressure_refinement_enabled
            ? std::make_shared<DssrPressureMonitor>(
                  model,
                  params.dssr_pressure_max_bucket_size,
                  params.dssr_pressure_max_candidate_checks)
            : nullptr;
    if (dssr_pressure != nullptr) {
        base.should_stop = [dssr_pressure]() {
            return dssr_pressure->triggered;
        };
    }
    rcspp::AlgorithmParams<LabelList> algorithm_params(
        base,
        LabelList{
            model,
            10,
            params.dominance_epsilon,
            params.resource_epsilon,
            proof_queue_potential_trace,
            dssr_pressure
        });
    AuditedBestFirstDominance algorithm(&built.graph->get_resource_factory(),
                                        std::move(algorithm_params),
                                        model,
                                        params.proof_queue_policy,
                                        params.proof_queue_guidance_bucket_width,
                                        params.negative_epsilon,
                                        proof_queue_potential_trace,
                                        params.frontier_probe,
                                        params.counterfactual_prefix);
    const auto started = std::chrono::steady_clock::now();
    algorithm.begin_best_reduced_cost_trace(
        started, !params.exact_proof || counterfactual_prefix_active);
    auto result = built.graph->solve<AuditedBestFirstDominance, rcspp::RealResource>(
        &algorithm, -params.negative_epsilon, false, 0);
    const auto elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - started);

    SolveOutput output;
    output.status = rcspp::to_string(result.status);
    output.search_exhaustive = result.status == rcspp::AlgorithmStatus::COMPLETE;
    output.frontier_empty = output.search_exhaustive && algorithm.all_labels_processed();
    output.labels_dropped = algorithm.memory_pressure_triggered();
    output.telemetry.processed_labels = algorithm.processed_labels();
    output.telemetry.extended_labels = algorithm.extended_labels();
    output.telemetry.dominated_labels = algorithm.dominated_labels();
    output.telemetry.dominance_candidate_checks = algorithm.dominance_candidate_checks();
    output.telemetry.max_visited_bucket_size = algorithm.max_visited_bucket_size();
    output.telemetry.solution_count = result.solutions.size();
    output.telemetry.negative_escape_enabled =
        exact_negative_escape_active;
    output.telemetry.negative_escape_triggered = bool(
        exact_negative_escape_active &&
        result.status == rcspp::AlgorithmStatus::MAX_SOLUTIONS &&
        result.solutions.size() >=
            params.exact_raw_negative_pool_size
    );
    output.telemetry.exact_admission_batch_size =
        params.exact_admission_batch_size;
    output.telemetry.exact_raw_negative_pool_size =
        params.exact_raw_negative_pool_size;
    output.telemetry.raw_unique_negative_count =
        result.solutions.size();
    output.telemetry.negative_escape_policy_id =
        params.exact_negative_escape_policy_id;
    output.telemetry.negative_escape_termination_reason =
        output.telemetry.negative_escape_triggered
            ? "RAW_TRUE_NEGATIVE_POOL_REACHED"
            : (
                  output.search_exhaustive
                      ? "EXHAUSTIVE_FRONTIER_COMPLETE"
                      : output.status
              );
    if (output.telemetry.negative_escape_triggered) {
        output.status = "FOUND_NEGATIVE_PARTIAL";
    }
    output.telemetry.memory_pressure_triggered = algorithm.memory_pressure_triggered();
    output.telemetry.graph_cache_hit = cache_hit;
    output.telemetry.graph_cache_size = cache.size();
    output.telemetry.graph_cache_build_count = graph_cache_build_count();
    output.telemetry.graph_cache_hit_count = graph_cache_hit_count();
    output.telemetry.completion_bound_evaluated_labels =
        model->completion_bound_evaluated_labels;
    output.telemetry.completion_bound_pruned_labels =
        model->completion_bound_pruned_labels;
    output.telemetry.subset_dominance_key_lookups =
        algorithm.subset_dominance_key_lookups();
    output.telemetry.subset_dominance_nonempty_buckets =
        algorithm.subset_dominance_nonempty_buckets();
    output.telemetry.subset_dominance_summary_skipped_buckets =
        algorithm.subset_dominance_summary_skipped_buckets();
    output.telemetry.subset_dominance_candidate_checks =
        algorithm.subset_dominance_candidate_checks();
    output.telemetry.subset_dominance_rejected_labels =
        algorithm.subset_dominance_rejected_labels();
    output.telemetry.extension_wall_time_seconds = algorithm.extension_wall_time_seconds();
    output.telemetry.dominance_wall_time_seconds = algorithm.dominance_wall_time_seconds();
    output.telemetry.wall_time_seconds = elapsed.count();
    output.telemetry.frontier_probe = algorithm.frontier_probe_telemetry();
    output.telemetry.counterfactual_prefix =
        algorithm.counterfactual_prefix_telemetry();
    if (dssr_pressure != nullptr) {
        output.telemetry.dssr_pressure_triggered =
            dssr_pressure->triggered;
        output.telemetry.dssr_pressure_split_task_id =
            dssr_pressure->split_task_id;
        output.telemetry.dssr_max_bucket_size =
            dssr_pressure->max_bucket_size;
        output.telemetry.dssr_dominance_candidate_checks =
            dssr_pressure->dominance_candidate_checks;
    }
    output.telemetry.best_reduced_cost_events = algorithm.best_reduced_cost_events();
    output.telemetry.best_reduced_cost_event_count_total =
        algorithm.best_reduced_cost_event_count_total();
    output.telemetry.best_reduced_cost_events_truncated =
        algorithm.best_reduced_cost_events_truncated();
    output.telemetry.proof_queue_potential_trace_enabled =
        params.proof_queue_potential_trace_enabled;
    if (proof_queue_potential_trace != nullptr) {
        proof_queue_potential_trace->finalize_label_trace();
        if (params.proof_queue_potential_trace_enabled) {
            output.telemetry.proof_queue_potential_trace =
                proof_queue_potential_trace->task_rows;
            output.telemetry.proof_queue_arc_potential_trace =
                proof_queue_potential_trace->arc_rows;
        }
        output.telemetry.proof_queue_label_trace_enabled =
            params.proof_queue_label_trace_enabled;
        output.telemetry.proof_queue_label_trace_truncated =
            proof_queue_potential_trace->label_trace_truncated;
        output.telemetry.proof_queue_label_trace_incomplete =
            proof_queue_potential_trace->label_trace_incomplete;
        output.telemetry.proof_queue_label_trace_sampling_mode =
            params.proof_queue_label_trace_sampling_mode ==
                    LabelTraceSamplingMode::QGR1StratifiedReservoirV1
                ? "qgr1_stratified_reservoir_v1"
                : "prefix_v1";
        output.telemetry.proof_queue_label_trace_seed =
            params.proof_queue_label_trace_seed;
        output.telemetry.proof_queue_existing_preference_seen =
            proof_queue_potential_trace->existing_preference_seen;
        output.telemetry.proof_queue_existing_preference_retained =
            proof_queue_potential_trace->existing_preference_retained;
        output.telemetry.proof_queue_incoming_preference_seen =
            proof_queue_potential_trace->incoming_preference_seen;
        output.telemetry.proof_queue_incoming_preference_retained =
            proof_queue_potential_trace->incoming_preference_retained;
        output.telemetry.proof_queue_surface_seen =
            proof_queue_potential_trace->surface_seen_count;
        output.telemetry.proof_queue_surface_retained =
            proof_queue_potential_trace->surface_retained_count;
        output.telemetry.proof_queue_surface_label_retained =
            proof_queue_potential_trace->surface_label_retained_count;
        output.telemetry.proof_queue_witness_seen =
            proof_queue_potential_trace->witness_seen_count;
        output.telemetry.proof_queue_witness_retained =
            proof_queue_potential_trace->witness_retained_count;
        output.telemetry.proof_queue_witness_ancestor_retained =
            proof_queue_potential_trace->witness_ancestor_retained_count;
        output.telemetry.proof_queue_label_trace_final_rows =
            proof_queue_potential_trace->final_label_row_count;
        output.telemetry.proof_queue_label_state_trace =
            std::move(proof_queue_potential_trace->label_rows);
        output.telemetry.proof_queue_label_preference_trace =
            std::move(proof_queue_potential_trace->preference_rows);
        output.telemetry.proof_queue_negative_witness_trace =
            std::move(proof_queue_potential_trace->witness_rows);
    }
    output.telemetry.proof_queue_label_state_scored_count =
        algorithm.label_state_scored_count();
    output.telemetry.proof_queue_guidance_nonzero_score_count =
        algorithm.guidance_nonzero_score_count();
    output.telemetry.proof_queue_guidance_ordering_decision_count =
        algorithm.guidance_ordering_decision_count();
    output.telemetry.proof_queue_guidance_reordered_label_hash_count =
        algorithm.guidance_reordered_label_hash_count();
    output.telemetry.proof_queue_guidance_bucket_hash_count =
        algorithm.guidance_bucket_hash_count();
    output.telemetry.proof_queue_label_state_scoring_estimated_wall_seconds =
        algorithm.label_state_scoring_estimated_wall_seconds();
    output.telemetry.first_true_negative_wall_time_seconds =
        algorithm.first_true_negative_wall_time_seconds();
    output.telemetry.labels_processed_before_first_true_negative =
        algorithm.labels_processed_before_first_true_negative();
    if (!counterfactual_prefix_active) {
        output.routes.reserve(result.solutions.size());
        for (const auto& solution : result.solutions) {
            output.routes.push_back(
                reconstruct_route(solution, *model, built.actions_by_arc_id));
        }
    } else {
        output.routes.clear();
        output.search_exhaustive = false;
        output.frontier_empty = false;
        output.status = output.telemetry.counterfactual_prefix.complete
                            ? "COUNTERFACTUAL_PREFIX_COMPLETE"
                            : "COUNTERFACTUAL_PREFIX_INCOMPLETE";
        output.telemetry.counterfactual_prefix.truncated_diagnostic = true;
        output.telemetry.counterfactual_prefix.exact = false;
        output.telemetry.counterfactual_prefix.routes_suppressed = true;
        output.telemetry.counterfactual_prefix.certificate_suppressed = true;
    }
    algorithm.release_request_memory();
    return output;
}

SolveOutput solve_dssr_v1(
    const Model& input_model,
    const SolveParams& params
) {
    if (!params.dssr_enabled) {
        return solve_once(input_model, params);
    }
    if (!params.exact_proof) {
        throw std::invalid_argument(
            "DSSR relaxation is available only for exact-proof pricing");
    }

    Model model = input_model;
    model.dssr_relaxation_enabled = true;
    const auto mask_words = (model.tasks.size() + 63U) / 64U;
    model.dssr_critical_task_mask.assign(mask_words, 0U);
    model.dssr_branch_task_mask.assign(mask_words, 0U);
    for (const auto& decision : model.branch_decisions) {
        const auto mark_branch_task = [&](std::size_t task_index,
                                          bool exists) {
            if (!exists || task_index >= model.tasks.size()) {
                return;
            }
            model.dssr_branch_task_mask[task_index / 64U] |=
                std::uint64_t{1} << (task_index % 64U);
        };
        mark_branch_task(decision.task_a, decision.task_a_exists);
        mark_branch_task(decision.task_b, decision.task_b_exists);
    }

    SolveParams iteration_params = params;
    iteration_params.completion_bound_enabled = false;
    iteration_params.subset_dominance_enabled = false;
    iteration_params.proof_queue_potential_trace_enabled = false;

    const auto overall_started = std::chrono::steady_clock::now();
    std::size_t total_processed_labels = 0;
    std::size_t total_extended_labels = 0;
    std::size_t total_dominated_labels = 0;
    std::size_t total_dominance_checks = 0;
    std::size_t max_bucket_size = 0;
    double total_extension_seconds = 0.0;
    double total_dominance_seconds = 0.0;
    std::size_t refinement_count = 0;
    std::size_t repeated_witness_count = 0;
    std::vector<DssrIterationTraceRow> iteration_trace;

    const auto critical_count = [&]() {
        std::size_t count = 0;
        for (const auto word : model.dssr_critical_task_mask) {
            count += std::popcount(word);
        }
        return count;
    };
    const auto finalize = [&](SolveOutput output,
                              bool elementary_witness,
                              bool relaxation_certificate) {
        output.telemetry.processed_labels = total_processed_labels;
        output.telemetry.extended_labels = total_extended_labels;
        output.telemetry.dominated_labels = total_dominated_labels;
        output.telemetry.dominance_candidate_checks =
            total_dominance_checks;
        output.telemetry.max_visited_bucket_size = max_bucket_size;
        output.telemetry.extension_wall_time_seconds =
            total_extension_seconds;
        output.telemetry.dominance_wall_time_seconds =
            total_dominance_seconds;
        output.telemetry.wall_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - overall_started)
                .count();
        output.telemetry.dssr_enabled = true;
        output.telemetry.dssr_policy_version = kDssrPolicyVersionV1;
        output.telemetry.dssr_iteration_count = iteration_trace.size();
        output.telemetry.dssr_refinement_count = refinement_count;
        output.telemetry.dssr_initial_critical_task_count = 0;
        output.telemetry.dssr_final_critical_task_count =
            critical_count();
        output.telemetry.dssr_repeated_witness_count =
            repeated_witness_count;
        output.telemetry.dssr_elementary_witness_returned =
            elementary_witness;
        output.telemetry.dssr_relaxation_no_negative_certificate =
            relaxation_certificate;
        output.telemetry.dssr_iteration_trace = iteration_trace;
        return output;
    };

    std::unordered_map<std::string, std::size_t> task_index_by_id;
    for (const auto& task : model.tasks) {
        task_index_by_id.emplace(task.id, task.index);
    }

    for (std::size_t iteration = 0;
         iteration <= model.tasks.size();
         ++iteration) {
        if (std::isfinite(params.timeout_seconds)) {
            const auto elapsed = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - overall_started);
            const double remaining = params.timeout_seconds - elapsed.count();
            if (remaining <= 0.0) {
                SolveOutput timeout;
                timeout.status = "timeout";
                return finalize(std::move(timeout), false, false);
            }
            iteration_params.timeout_seconds = remaining;
        }

        const auto critical_before = critical_count();
        auto output = solve_once(model, iteration_params);
        total_processed_labels += output.telemetry.processed_labels;
        total_extended_labels += output.telemetry.extended_labels;
        total_dominated_labels += output.telemetry.dominated_labels;
        total_dominance_checks +=
            output.telemetry.dominance_candidate_checks;
        max_bucket_size = std::max(
            max_bucket_size,
            output.telemetry.max_visited_bucket_size);
        total_extension_seconds +=
            output.telemetry.extension_wall_time_seconds;
        total_dominance_seconds +=
            output.telemetry.dominance_wall_time_seconds;

        std::unordered_set<std::size_t> repeated_tasks;
        bool witness_found = !output.routes.empty();
        if (witness_found) {
            std::unordered_set<std::size_t> seen_tasks;
            for (const auto& sortie : output.routes.front().sorties) {
                for (const auto& task_id : sortie.tasks) {
                    const auto found = task_index_by_id.find(task_id);
                    if (found == task_index_by_id.end()) {
                        throw std::runtime_error(
                            "DSSR witness references an unknown task");
                    }
                    if (!seen_tasks.insert(found->second).second) {
                        repeated_tasks.insert(found->second);
                    }
                }
            }
        }
        const bool witness_elementary =
            witness_found && repeated_tasks.empty();
        iteration_trace.push_back(DssrIterationTraceRow{
            .iteration = iteration,
            .critical_task_count_before = critical_before,
            .repeated_task_count = repeated_tasks.size(),
            .processed_labels = output.telemetry.processed_labels,
            .extended_labels = output.telemetry.extended_labels,
            .dominated_labels = output.telemetry.dominated_labels,
            .max_visited_bucket_size =
                output.telemetry.max_visited_bucket_size,
            .wall_time_seconds = output.telemetry.wall_time_seconds,
            .status = output.status,
            .search_exhaustive = output.search_exhaustive,
            .frontier_empty = output.frontier_empty,
            .labels_dropped = output.labels_dropped,
            .negative_witness_found = witness_found,
            .witness_elementary = witness_elementary,
        });

        if (!witness_found) {
            const bool certificate =
                output.search_exhaustive && output.frontier_empty &&
                !output.labels_dropped;
            return finalize(std::move(output), false, certificate);
        }
        if (witness_elementary) {
            return finalize(std::move(output), true, false);
        }

        ++repeated_witness_count;
        std::size_t newly_critical = 0;
        for (const auto task_index : repeated_tasks) {
            const auto word = task_index / 64U;
            const auto bit = task_index % 64U;
            const auto bit_mask = std::uint64_t{1} << bit;
            if ((model.dssr_critical_task_mask[word] & bit_mask) == 0U) {
                model.dssr_critical_task_mask[word] |= bit_mask;
                ++newly_critical;
            }
        }
        if (newly_critical == 0U) {
            output.status = "dssr_refinement_stalled";
            output.routes.clear();
            output.search_exhaustive = false;
            output.frontier_empty = false;
            return finalize(std::move(output), false, false);
        }
        ++refinement_count;
    }

    SolveOutput exhausted;
    exhausted.status = "dssr_refinement_limit";
    return finalize(std::move(exhausted), false, false);
}

struct DssrRouteBatchAudit {
    std::vector<Route> elementary_routes;
    std::unordered_set<std::size_t> repeated_tasks;
    std::size_t raw_solution_count = 0;
    std::size_t non_elementary_solution_count = 0;
};

std::string dssr_route_signature(const Route& route) {
    std::ostringstream stream;
    for (const auto& sortie : route.sorties) {
        stream << "S" << sortie.tasks.size() << ":";
        for (const auto& task_id : sortie.tasks) {
            stream << task_id.size() << ":" << task_id << ";";
        }
        stream << "P" << sortie.path_types.size() << ":";
        for (const auto& path_type : sortie.path_types) {
            stream << path_type.size() << ":" << path_type << ";";
        }
    }
    return stream.str();
}

DssrRouteBatchAudit audit_dssr_v2_routes(
    const std::vector<Route>& routes,
    const std::unordered_map<std::string, std::size_t>& task_index_by_id,
    std::size_t public_batch_target
) {
    DssrRouteBatchAudit audit;
    audit.raw_solution_count = routes.size();
    std::unordered_set<std::string> elementary_signatures;
    for (const auto& route : routes) {
        std::unordered_set<std::size_t> seen_tasks;
        std::unordered_set<std::size_t> route_repeated_tasks;
        for (const auto& sortie : route.sorties) {
            for (const auto& task_id : sortie.tasks) {
                const auto found = task_index_by_id.find(task_id);
                if (found == task_index_by_id.end()) {
                    throw std::runtime_error(
                        "DSSR V2 route references an unknown task");
                }
                if (!seen_tasks.insert(found->second).second) {
                    route_repeated_tasks.insert(found->second);
                }
            }
        }
        if (!route_repeated_tasks.empty()) {
            ++audit.non_elementary_solution_count;
            audit.repeated_tasks.insert(
                route_repeated_tasks.begin(),
                route_repeated_tasks.end());
            continue;
        }
        if (audit.elementary_routes.size() >= public_batch_target) {
            continue;
        }
        const auto signature = dssr_route_signature(route);
        if (elementary_signatures.insert(signature).second) {
            audit.elementary_routes.push_back(route);
        }
    }
    return audit;
}

std::size_t ng_relation_count(
    const std::vector<std::vector<std::uint64_t>>& masks
) {
    std::size_t count = 0;
    for (const auto& mask : masks) {
        for (const auto word : mask) {
            count += std::popcount(word);
        }
    }
    return count;
}

bool add_ng_relation(
    std::vector<std::vector<std::uint64_t>>* masks,
    std::size_t host_task_index,
    std::size_t remembered_task_index
) {
    if (
        masks == nullptr ||
        host_task_index >= masks->size() ||
        remembered_task_index >= masks->size()
    ) {
        return false;
    }
    auto& mask = masks->at(host_task_index);
    const auto word = remembered_task_index / 64U;
    const auto bit = remembered_task_index % 64U;
    if (word >= mask.size()) {
        return false;
    }
    const auto bit_mask = std::uint64_t{1} << bit;
    if ((mask[word] & bit_mask) != 0U) {
        return false;
    }
    mask[word] |= bit_mask;
    return true;
}

std::vector<std::vector<std::uint64_t>>
initial_ng_memory_masks(
    const Model& model,
    std::size_t requested_neighborhood_size
) {
    const auto task_count = model.tasks.size();
    const auto mask_words = (task_count + 63U) / 64U;
    const auto neighborhood_size = std::clamp<std::size_t>(
        requested_neighborhood_size,
        1U,
        task_count
    );
    std::unordered_map<std::string, std::size_t> task_index_by_id;
    for (const auto& task : model.tasks) {
        task_index_by_id.emplace(task.id, task.index);
    }
    std::vector<std::vector<double>> directed(
        task_count,
        std::vector<double>(
            task_count,
            std::numeric_limits<double>::infinity()
        )
    );
    for (std::size_t task_index = 0; task_index < task_count; ++task_index) {
        directed[task_index][task_index] = 0.0;
    }
    for (const auto& arc : model.arcs) {
        const auto source = task_index_by_id.find(arc.source);
        const auto target = task_index_by_id.find(arc.target);
        if (
            source == task_index_by_id.end() ||
            target == task_index_by_id.end()
        ) {
            continue;
        }
        directed[source->second][target->second] = std::min(
            directed[source->second][target->second],
            arc.travel_time
        );
    }
    std::vector<std::vector<std::uint64_t>> masks(
        task_count,
        std::vector<std::uint64_t>(mask_words, 0U)
    );
    for (const auto& host : model.tasks) {
        add_ng_relation(&masks, host.index, host.index);
        std::vector<std::tuple<double, std::string, std::size_t>>
            candidates;
        candidates.reserve(task_count - 1U);
        for (const auto& remembered : model.tasks) {
            if (remembered.index == host.index) {
                continue;
            }
            const auto score = std::min(
                directed[host.index][remembered.index],
                directed[remembered.index][host.index]
            );
            candidates.emplace_back(
                score,
                remembered.id,
                remembered.index
            );
        }
        std::ranges::sort(candidates);
        for (
            std::size_t rank = 0;
            rank + 1U < neighborhood_size;
            ++rank
        ) {
            const auto remembered_index =
                std::get<2>(candidates[rank]);
            add_ng_relation(
                &masks,
                host.index,
                remembered_index
            );
        }
    }
    return masks;
}

struct NgDssrRouteBatchAudit {
    std::vector<Route> elementary_routes;
    std::unordered_set<std::size_t> cycle_relations;
    std::size_t raw_solution_count = 0;
    std::size_t non_elementary_solution_count = 0;
    std::size_t forbidden_cycle_count = 0;
};

NgDssrRouteBatchAudit audit_ng_dssr_routes(
    const std::vector<Route>& routes,
    const std::unordered_map<std::string, std::size_t>& task_index_by_id,
    std::size_t task_count,
    std::size_t public_batch_target
) {
    NgDssrRouteBatchAudit audit;
    audit.raw_solution_count = routes.size();
    std::unordered_set<std::string> elementary_signatures;
    for (const auto& route : routes) {
        std::vector<std::size_t> sequence;
        for (const auto& sortie : route.sorties) {
            for (const auto& task_id : sortie.tasks) {
                const auto found = task_index_by_id.find(task_id);
                if (found == task_index_by_id.end()) {
                    throw std::runtime_error(
                        "ng-DSSR route references an unknown task");
                }
                sequence.push_back(found->second);
            }
        }
        std::unordered_map<std::size_t, std::size_t> last_position;
        bool elementary = true;
        for (std::size_t position = 0; position < sequence.size(); ++position) {
            const auto remembered_task = sequence[position];
            const auto previous = last_position.find(remembered_task);
            if (previous != last_position.end()) {
                elementary = false;
                ++audit.forbidden_cycle_count;
                for (
                    std::size_t cycle_position = previous->second;
                    cycle_position < position;
                    ++cycle_position
                ) {
                    const auto host_task = sequence[cycle_position];
                    audit.cycle_relations.insert(
                        host_task * task_count + remembered_task
                    );
                }
            }
            last_position[remembered_task] = position;
        }
        if (!elementary) {
            ++audit.non_elementary_solution_count;
            continue;
        }
        if (audit.elementary_routes.size() >= public_batch_target) {
            continue;
        }
        const auto signature = dssr_route_signature(route);
        if (elementary_signatures.insert(signature).second) {
            audit.elementary_routes.push_back(route);
        }
    }
    return audit;
}

SolveOutput solve_dssr_v2(
    const Model& input_model,
    const SolveParams& params
) {
    if (!params.exact_proof) {
        throw std::invalid_argument(
            "DSSR V2 relaxation is available only for exact-proof pricing");
    }

    Model model = input_model;
    model.dssr_relaxation_enabled = true;
    const auto mask_words = (model.tasks.size() + 63U) / 64U;
    model.dssr_critical_task_mask.assign(mask_words, 0U);
    model.dssr_branch_task_mask.assign(mask_words, 0U);
    for (const auto& decision : model.branch_decisions) {
        const auto mark_branch_task = [&](std::size_t task_index,
                                          bool exists) {
            if (!exists || task_index >= model.tasks.size()) {
                return;
            }
            model.dssr_branch_task_mask[task_index / 64U] |=
                std::uint64_t{1} << (task_index % 64U);
        };
        mark_branch_task(decision.task_a, decision.task_a_exists);
        mark_branch_task(decision.task_b, decision.task_b_exists);
    }

    SolveParams iteration_params = params;
    iteration_params.completion_bound_enabled = false;
    iteration_params.subset_dominance_enabled = false;
    iteration_params.proof_queue_potential_trace_enabled = false;
    iteration_params.dssr_negative_batch_target =
        std::clamp<std::size_t>(
            params.dssr_negative_batch_target,
            1U,
            64U);

    const auto overall_started = std::chrono::steady_clock::now();
    std::size_t total_processed_labels = 0;
    std::size_t total_extended_labels = 0;
    std::size_t total_dominated_labels = 0;
    std::size_t total_dominance_checks = 0;
    std::size_t max_bucket_size = 0;
    double total_extension_seconds = 0.0;
    double total_dominance_seconds = 0.0;
    std::size_t refinement_count = 0;
    std::size_t repeated_witness_count = 0;
    std::size_t raw_solution_count = 0;
    std::size_t elementary_batch_count = 0;
    std::size_t pressure_refinement_count = 0;
    std::size_t pressure_abandoned_iteration_count = 0;
    std::vector<std::string> pressure_split_task_ids;
    std::vector<DssrIterationTraceRow> iteration_trace;

    const auto critical_count = [&]() {
        std::size_t count = 0;
        for (const auto word : model.dssr_critical_task_mask) {
            count += std::popcount(word);
        }
        return count;
    };
    const auto mark_critical = [&](std::size_t task_index) {
        if (task_index >= model.tasks.size()) {
            return false;
        }
        const auto word = task_index / 64U;
        const auto bit_mask =
            std::uint64_t{1} << (task_index % 64U);
        if ((model.dssr_critical_task_mask[word] & bit_mask) != 0U) {
            return false;
        }
        model.dssr_critical_task_mask[word] |= bit_mask;
        return true;
    };
    const auto finalize = [&](SolveOutput output,
                              bool elementary_witness,
                              bool relaxation_certificate) {
        output.telemetry.processed_labels = total_processed_labels;
        output.telemetry.extended_labels = total_extended_labels;
        output.telemetry.dominated_labels = total_dominated_labels;
        output.telemetry.dominance_candidate_checks =
            total_dominance_checks;
        output.telemetry.max_visited_bucket_size = max_bucket_size;
        output.telemetry.solution_count = output.routes.size();
        output.telemetry.extension_wall_time_seconds =
            total_extension_seconds;
        output.telemetry.dominance_wall_time_seconds =
            total_dominance_seconds;
        output.telemetry.wall_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - overall_started)
                .count();
        output.telemetry.dssr_enabled = true;
        output.telemetry.dssr_policy_version = kDssrPolicyVersionV2;
        output.telemetry.dssr_iteration_count = iteration_trace.size();
        output.telemetry.dssr_refinement_count = refinement_count;
        output.telemetry.dssr_initial_critical_task_count = 0;
        output.telemetry.dssr_final_critical_task_count =
            critical_count();
        output.telemetry.dssr_repeated_witness_count =
            repeated_witness_count;
        output.telemetry.dssr_elementary_witness_returned =
            elementary_witness;
        output.telemetry.dssr_relaxation_no_negative_certificate =
            relaxation_certificate;
        output.telemetry.dssr_elementary_batch_count =
            elementary_batch_count;
        output.telemetry.dssr_raw_solution_count =
            raw_solution_count;
        output.telemetry.dssr_pressure_refinement_count =
            pressure_refinement_count;
        output.telemetry.dssr_pressure_split_task_ids =
            pressure_split_task_ids;
        output.telemetry.dssr_pressure_abandoned_iteration_count =
            pressure_abandoned_iteration_count;
        output.telemetry.dssr_max_bucket_size = max_bucket_size;
        output.telemetry.dssr_dominance_candidate_checks =
            total_dominance_checks;
        output.telemetry.dssr_pressure_triggered = false;
        output.telemetry.dssr_pressure_split_task_id.clear();
        output.telemetry.dssr_iteration_trace = iteration_trace;
        return output;
    };

    std::unordered_map<std::string, std::size_t> task_index_by_id;
    for (const auto& task : model.tasks) {
        task_index_by_id.emplace(task.id, task.index);
    }

    for (std::size_t iteration = 0;
         iteration <= model.tasks.size();
         ++iteration) {
        if (std::isfinite(params.timeout_seconds)) {
            const auto elapsed = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - overall_started);
            const double remaining =
                params.timeout_seconds - elapsed.count();
            if (remaining <= 0.0) {
                SolveOutput timeout;
                timeout.status = "timeout";
                return finalize(std::move(timeout), false, false);
            }
            iteration_params.timeout_seconds = remaining;
        }

        const auto critical_before = critical_count();
        auto output = solve_once(model, iteration_params);
        total_processed_labels += output.telemetry.processed_labels;
        total_extended_labels += output.telemetry.extended_labels;
        total_dominated_labels += output.telemetry.dominated_labels;
        total_dominance_checks +=
            output.telemetry.dominance_candidate_checks;
        max_bucket_size = std::max(
            max_bucket_size,
            output.telemetry.max_visited_bucket_size);
        total_extension_seconds +=
            output.telemetry.extension_wall_time_seconds;
        total_dominance_seconds +=
            output.telemetry.dominance_wall_time_seconds;

        if (output.telemetry.dssr_pressure_triggered) {
            const auto split_task_id =
                output.telemetry.dssr_pressure_split_task_id;
            output.routes.clear();
            output.search_exhaustive = false;
            output.frontier_empty = false;
            output.status = "dssr_pressure_refinement";
            iteration_trace.push_back(DssrIterationTraceRow{
                .iteration = iteration,
                .critical_task_count_before = critical_before,
                .processed_labels = output.telemetry.processed_labels,
                .extended_labels = output.telemetry.extended_labels,
                .dominated_labels = output.telemetry.dominated_labels,
                .max_visited_bucket_size =
                    output.telemetry.max_visited_bucket_size,
                .wall_time_seconds = output.telemetry.wall_time_seconds,
                .status = output.status,
                .search_exhaustive = false,
                .frontier_empty = false,
                .labels_dropped = output.labels_dropped,
                .pressure_refinement_triggered = true,
                .pressure_split_task_id = split_task_id,
            });
            ++pressure_abandoned_iteration_count;
            const auto split_found =
                task_index_by_id.find(split_task_id);
            if (
                split_found == task_index_by_id.end() ||
                !mark_critical(split_found->second)
            ) {
                output.status = "dssr_pressure_refinement_stalled";
                return finalize(std::move(output), false, false);
            }
            ++refinement_count;
            ++pressure_refinement_count;
            pressure_split_task_ids.push_back(split_task_id);
            continue;
        }

        auto audit = audit_dssr_v2_routes(
            output.routes,
            task_index_by_id,
            iteration_params.dssr_negative_batch_target);
        raw_solution_count += audit.raw_solution_count;
        repeated_witness_count +=
            audit.non_elementary_solution_count;
        const auto elementary_count =
            audit.elementary_routes.size();

        std::size_t newly_critical = 0;
        for (const auto task_index : audit.repeated_tasks) {
            if (mark_critical(task_index)) {
                ++newly_critical;
            }
        }
        if (newly_critical > 0U) {
            ++refinement_count;
        }

        iteration_trace.push_back(DssrIterationTraceRow{
            .iteration = iteration,
            .critical_task_count_before = critical_before,
            .repeated_task_count = audit.repeated_tasks.size(),
            .processed_labels = output.telemetry.processed_labels,
            .extended_labels = output.telemetry.extended_labels,
            .dominated_labels = output.telemetry.dominated_labels,
            .max_visited_bucket_size =
                output.telemetry.max_visited_bucket_size,
            .wall_time_seconds = output.telemetry.wall_time_seconds,
            .status = output.status,
            .search_exhaustive = output.search_exhaustive,
            .frontier_empty = output.frontier_empty,
            .labels_dropped = output.labels_dropped,
            .negative_witness_found =
                audit.raw_solution_count > 0U,
            .witness_elementary = elementary_count > 0U,
            .raw_solution_count = audit.raw_solution_count,
            .elementary_solution_count = elementary_count,
            .non_elementary_solution_count =
                audit.non_elementary_solution_count,
        });

        if (elementary_count > 0U) {
            output.routes = std::move(audit.elementary_routes);
            elementary_batch_count += output.routes.size();
            output.search_exhaustive =
                output.search_exhaustive &&
                audit.non_elementary_solution_count == 0U;
            output.frontier_empty =
                output.frontier_empty && output.search_exhaustive;
            return finalize(std::move(output), true, false);
        }

        output.routes.clear();
        if (audit.raw_solution_count == 0U) {
            const bool certificate =
                output.search_exhaustive && output.frontier_empty &&
                !output.labels_dropped;
            return finalize(std::move(output), false, certificate);
        }
        if (newly_critical == 0U) {
            output.status = "dssr_refinement_stalled";
            output.search_exhaustive = false;
            output.frontier_empty = false;
            return finalize(std::move(output), false, false);
        }
    }

    SolveOutput exhausted;
    exhausted.status = "dssr_refinement_limit";
    return finalize(std::move(exhausted), false, false);
}

SolveOutput solve_ng_dssr_v3(
    const Model& input_model,
    const SolveParams& params
) {
    if (!params.exact_proof) {
        throw std::invalid_argument(
            "ng-DSSR V3 is available only for exact-proof pricing");
    }

    Model model = input_model;
    model.dssr_relaxation_enabled = true;
    model.ng_dssr_memory_enabled = true;
    model.guidance_task_arc_enabled = false;
    const auto mask_words = (model.tasks.size() + 63U) / 64U;
    model.dssr_critical_task_mask.assign(mask_words, 0U);
    model.dssr_branch_task_mask.assign(mask_words, 0U);
    for (const auto& decision : model.branch_decisions) {
        const auto mark_branch_task = [&](std::size_t task_index,
                                          bool exists) {
            if (!exists || task_index >= model.tasks.size()) {
                return;
            }
            model.dssr_branch_task_mask[task_index / 64U] |=
                std::uint64_t{1} << (task_index % 64U);
        };
        mark_branch_task(decision.task_a, decision.task_a_exists);
        mark_branch_task(decision.task_b, decision.task_b_exists);
    }
    const auto initial_neighborhood_size =
        std::clamp<std::size_t>(
            params.ng_dssr_initial_neighborhood_size,
            1U,
            model.tasks.size()
        );
    model.ng_dssr_task_memory_masks = initial_ng_memory_masks(
        model,
        initial_neighborhood_size
    );
    const auto initial_relation_count =
        ng_relation_count(model.ng_dssr_task_memory_masks);

    SolveParams iteration_params = params;
    iteration_params.completion_bound_enabled = false;
    iteration_params.subset_dominance_enabled = false;
    iteration_params.proof_queue_potential_trace_enabled = false;
    iteration_params.dssr_pressure_refinement_enabled = false;
    iteration_params.proof_queue_policy =
        ProofQueuePolicy::Q0PartialCost;
    iteration_params.dssr_negative_batch_target =
        std::clamp<std::size_t>(
            params.dssr_negative_batch_target,
            1U,
            64U
        );

    const auto overall_started = std::chrono::steady_clock::now();
    std::size_t total_processed_labels = 0;
    std::size_t total_extended_labels = 0;
    std::size_t total_dominated_labels = 0;
    std::size_t total_dominance_checks = 0;
    std::size_t max_bucket_size = 0;
    double total_extension_seconds = 0.0;
    double total_dominance_seconds = 0.0;
    std::size_t refinement_count = 0;
    std::size_t repeated_witness_count = 0;
    std::size_t raw_solution_count = 0;
    std::size_t elementary_batch_count = 0;
    std::size_t relation_add_count = 0;
    std::size_t forbidden_cycle_count = 0;
    std::size_t full_elementary_fallback_count = 0;
    std::vector<DssrIterationTraceRow> iteration_trace;

    const auto finalize = [&](SolveOutput output,
                              bool elementary_witness,
                              bool relaxation_certificate) {
        output.telemetry.processed_labels = total_processed_labels;
        output.telemetry.extended_labels = total_extended_labels;
        output.telemetry.dominated_labels = total_dominated_labels;
        output.telemetry.dominance_candidate_checks =
            total_dominance_checks;
        output.telemetry.max_visited_bucket_size = max_bucket_size;
        output.telemetry.solution_count = output.routes.size();
        output.telemetry.extension_wall_time_seconds =
            total_extension_seconds;
        output.telemetry.dominance_wall_time_seconds =
            total_dominance_seconds;
        output.telemetry.wall_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - overall_started
            ).count();
        output.telemetry.dssr_enabled = true;
        output.telemetry.dssr_policy_version =
            kNgDssrPolicyVersionV3;
        output.telemetry.dssr_iteration_count =
            iteration_trace.size();
        output.telemetry.dssr_refinement_count = refinement_count;
        output.telemetry.dssr_initial_critical_task_count = 0;
        output.telemetry.dssr_final_critical_task_count = 0;
        output.telemetry.dssr_repeated_witness_count =
            repeated_witness_count;
        output.telemetry.dssr_elementary_witness_returned =
            elementary_witness;
        output.telemetry.dssr_relaxation_no_negative_certificate =
            relaxation_certificate;
        output.telemetry.dssr_elementary_batch_count =
            elementary_batch_count;
        output.telemetry.dssr_raw_solution_count =
            raw_solution_count;
        output.telemetry.dssr_max_bucket_size = max_bucket_size;
        output.telemetry.dssr_dominance_candidate_checks =
            total_dominance_checks;
        output.telemetry.ng_dssr_enabled = true;
        output.telemetry.ng_dssr_initial_neighborhood_size =
            initial_neighborhood_size;
        output.telemetry.ng_dssr_initial_relation_count =
            initial_relation_count;
        output.telemetry.ng_dssr_final_relation_count =
            ng_relation_count(model.ng_dssr_task_memory_masks);
        output.telemetry.ng_dssr_relation_add_count =
            relation_add_count;
        output.telemetry.ng_dssr_forbidden_cycle_count =
            forbidden_cycle_count;
        output.telemetry.ng_dssr_full_elementary_fallback_count =
            full_elementary_fallback_count;
        output.telemetry.dssr_iteration_trace = iteration_trace;
        return output;
    };

    std::unordered_map<std::string, std::size_t> task_index_by_id;
    for (const auto& task : model.tasks) {
        task_index_by_id.emplace(task.id, task.index);
    }
    const auto max_relation_count =
        model.tasks.size() * model.tasks.size();
    for (
        std::size_t iteration = 0;
        iteration <= max_relation_count;
        ++iteration
    ) {
        if (std::isfinite(params.timeout_seconds)) {
            const auto elapsed = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - overall_started
            );
            const auto remaining =
                params.timeout_seconds - elapsed.count();
            if (remaining <= 0.0) {
                SolveOutput timeout;
                timeout.status = "timeout";
                return finalize(std::move(timeout), false, false);
            }
            iteration_params.timeout_seconds = remaining;
        }

        const auto relations_before =
            ng_relation_count(model.ng_dssr_task_memory_masks);
        auto output = solve_once(model, iteration_params);
        total_processed_labels += output.telemetry.processed_labels;
        total_extended_labels += output.telemetry.extended_labels;
        total_dominated_labels += output.telemetry.dominated_labels;
        total_dominance_checks +=
            output.telemetry.dominance_candidate_checks;
        max_bucket_size = std::max(
            max_bucket_size,
            output.telemetry.max_visited_bucket_size
        );
        total_extension_seconds +=
            output.telemetry.extension_wall_time_seconds;
        total_dominance_seconds +=
            output.telemetry.dominance_wall_time_seconds;

        auto audit = audit_ng_dssr_routes(
            output.routes,
            task_index_by_id,
            model.tasks.size(),
            iteration_params.dssr_negative_batch_target
        );
        raw_solution_count += audit.raw_solution_count;
        repeated_witness_count +=
            audit.non_elementary_solution_count;
        forbidden_cycle_count += audit.forbidden_cycle_count;
        const auto elementary_count =
            audit.elementary_routes.size();

        std::size_t newly_added = 0;
        for (const auto encoded : audit.cycle_relations) {
            const auto host_task = encoded / model.tasks.size();
            const auto remembered_task = encoded % model.tasks.size();
            if (add_ng_relation(
                    &model.ng_dssr_task_memory_masks,
                    host_task,
                    remembered_task
                )) {
                ++newly_added;
            }
        }
        relation_add_count += newly_added;
        if (newly_added > 0U) {
            ++refinement_count;
        }
        iteration_trace.push_back(DssrIterationTraceRow{
            .iteration = iteration,
            .processed_labels = output.telemetry.processed_labels,
            .extended_labels = output.telemetry.extended_labels,
            .dominated_labels = output.telemetry.dominated_labels,
            .max_visited_bucket_size =
                output.telemetry.max_visited_bucket_size,
            .wall_time_seconds = output.telemetry.wall_time_seconds,
            .status = output.status,
            .search_exhaustive = output.search_exhaustive,
            .frontier_empty = output.frontier_empty,
            .labels_dropped = output.labels_dropped,
            .negative_witness_found =
                audit.raw_solution_count > 0U,
            .witness_elementary = elementary_count > 0U,
            .raw_solution_count = audit.raw_solution_count,
            .elementary_solution_count = elementary_count,
            .non_elementary_solution_count =
                audit.non_elementary_solution_count,
            .ng_relation_count_before = relations_before,
            .ng_relation_add_count = newly_added,
            .ng_forbidden_cycle_count =
                audit.forbidden_cycle_count,
        });

        if (elementary_count > 0U) {
            output.routes = std::move(audit.elementary_routes);
            elementary_batch_count += output.routes.size();
            output.search_exhaustive =
                output.search_exhaustive &&
                audit.non_elementary_solution_count == 0U;
            output.frontier_empty =
                output.frontier_empty && output.search_exhaustive;
            return finalize(std::move(output), true, false);
        }

        output.routes.clear();
        if (audit.raw_solution_count == 0U) {
            const bool certificate =
                output.search_exhaustive &&
                output.frontier_empty &&
                !output.labels_dropped;
            return finalize(std::move(output), false, certificate);
        }
        if (newly_added == 0U) {
            // A permitted repeated cycle must be missing at least one local
            // memory relation.  If an unforeseen reconstruction edge case
            // violates that invariant, fail over deterministically to full
            // elementarity instead of accepting a route or certificate.
            std::size_t fallback_add_count = 0;
            for (
                std::size_t host_task = 0;
                host_task < model.tasks.size();
                ++host_task
            ) {
                for (
                    std::size_t remembered_task = 0;
                    remembered_task < model.tasks.size();
                    ++remembered_task
                ) {
                    fallback_add_count += add_ng_relation(
                        &model.ng_dssr_task_memory_masks,
                        host_task,
                        remembered_task
                    );
                }
            }
            if (fallback_add_count == 0U) {
                output.status = "ng_dssr_refinement_stalled";
                output.search_exhaustive = false;
                output.frontier_empty = false;
                return finalize(std::move(output), false, false);
            }
            relation_add_count += fallback_add_count;
            ++refinement_count;
            ++full_elementary_fallback_count;
        }
    }

    SolveOutput exhausted;
    exhausted.status = "ng_dssr_refinement_limit";
    return finalize(std::move(exhausted), false, false);
}

SolveOutput solve(const Model& input_model, const SolveParams& params) {
    if (!params.dssr_enabled) {
        return solve_once(input_model, params);
    }
    if (params.dssr_policy_version == kDssrPolicyVersionV1) {
        return solve_dssr_v1(input_model, params);
    }
    if (params.dssr_policy_version == kDssrPolicyVersionV2) {
        return solve_dssr_v2(input_model, params);
    }
    if (params.dssr_policy_version == kNgDssrPolicyVersionV3) {
        if constexpr (kNgDssrV3Compiled) {
            return solve_ng_dssr_v3(input_model, params);
        }
        throw std::invalid_argument(
            "ng-DSSR V3 is disabled in this Native build");
    }
    throw std::invalid_argument(
        "unsupported DSSR policy version: " +
        params.dssr_policy_version);
}

std::unordered_map<std::string, std::string> build_info() {
    return {
        {"rcspp_commit", LUNAR_SPPRC_RCSPP_COMMIT},
        {"build_type", LUNAR_SPPRC_BUILD_TYPE},
        {"compiler", __VERSION__},
        {"cxx_standard", "23"},
        {"memory_pressure_policy", "disabled_for_exact_hard_limit_only"},
        {"branch_support", "ryan_foster_same_different_feasibility"},
        {"cut_support", "sri3_sri5_divisor2_threshold_crossing_v1"},
        {"cut_state_schema", "packed_exact_overlap_u64_sri3_2bit_sri5_3bit_v2"},
        {"cut_state_bytes", std::to_string(sizeof(CutState))},
        {"label_state_bytes", std::to_string(sizeof(State))},
        {"journey_value_bytes", std::to_string(sizeof(JourneyValue))},
        {"journey_resource_bytes", std::to_string(sizeof(JourneyResource))},
        {
            "rcspp_label_object_bytes",
            std::to_string(sizeof(rcspp::Label<Composition>))
        },
        {
            "rcspp_outer_resource_object_bytes",
            std::to_string(sizeof(rcspp::Resource<Composition>))
        },
        {
            "rcspp_journey_component_object_bytes",
            std::to_string(sizeof(rcspp::Resource<JourneyResource>))
        },
        {
            "label_memory_representation",
            "u16_counts_single_component_variant_compact_bucket_v2"
        },
        {"cut_state_max_bits", "48"},
        {"max_active_cuts", "16"},
        {"completion_bound", "positive_cover_dual_threshold_pruning_v1"},
        {"guidance_ordering", "q0_anchored_rc_bucket_label_state_priority_v2"},
        {"guidance_label_state_schema", "lunar_spprc.qg2_label_state.v1"},
        {"guidance_label_state_feature_count", "15"},
        {"frontier_probe_policy", "native_q0_4096_inplace_qd1_switch_v7"},
        {
            "frontier_temporal_observation_policy",
            "single_request_q0_snapshots_4096_8192_16384_v1"
        },
        {"frontier_graph_schema", "lunar_ice_bpc.p0v5_frontier_depth_rc_graph.v1"},
        {"frontier_feature_schema", "lunar_ice_bpc.p0v5_frontier_probe_features.v1"},
        {"frontier_gat_bundle_schema", "lunar_ice_bpc.p0v5_frontier_gat_native_bundle.v1"},
        {"frontier_gat_native_inference", "two_layer_edge_attention_16x2_v1"},
        {
            "frontier_temporal_trial_policy",
            "q0_boundary_qd1_k_then_continue_or_atomic_q0_v1"
        },
        {
            "frontier_temporal_gat_bundle_schema",
            "lunar_ice_bpc.p0v5_temporal_frontier_gat_bundle.v2"
        },
        {
            "frontier_temporal_gat_native_inference",
            "shared_cell_label_task_32x4_scale_heads_v2"
        },
        {
            "counterfactual_prefix_policy",
            "q0_4096_then_selected_q0_or_qd1_rollout_v8r1"
        },
        {"counterfactual_prefix_timing", "per_checkpoint_native_wall_v8r1"},
        {
            "counterfactual_frontier_graph_schema",
            "lunar_ice_bpc.p0v5_frontier_label_sample_graph.v1"
        },
        {
            "counterfactual_prefix_probe_schema",
            "lunar_ice_bpc.p0v5_counterfactual_prefix_probe.v1"
        },
        {"counterfactual_label_sample_cap", "256"},
        {"counterfactual_public_routes", "forbidden"},
        {"counterfactual_certificate", "forbidden"},
        {"best_reduced_cost_event_trace", "harvest_improvements_v1"},
        {"harvest_work_budget", "deterministic_processed_labels_v1"},
        {
            "exact_negative_escape_policy",
            "diverse_raw_4x_then_p0v4_selector_v1"
        },
        {"exact_negative_escape_certificate_semantics", "partial_fail_closed_v1"},
        {"service_timing_policy_id", "no_task_wait_base_departure_shift_v1"},
        {"large_scale_exact_pricer", kDssrPolicyVersionV1},
        {"dssr_v2_policy", kDssrPolicyVersionV2},
        {
            "ng_dssr_v3_policy",
            kNgDssrV3Compiled
                ? kNgDssrPolicyVersionV3
                : "disabled"
        },
        {
            "ng_dssr_v3_compiled",
            kNgDssrV3Compiled ? "true" : "false"
        },
        {
            "bidirectional_feasibility_compiled",
            kBidirectionalFeasibilityCompiled ? "true" : "false"
        },
        {
            "bidirectional_feasibility_policy",
            kBidirectionalFeasibilityCompiled
                ? "p0v4_frozen_dual_depot_meet_max_plus_v1"
                : "disabled"
        },
        {
            "bidirectional_task_meet_policy",
            kBidirectionalFeasibilityCompiled
                ? "p0v4_frozen_dual_task_meet_max_plus_v1"
                : "disabled"
        },
        {
            "bidirectional_journey_probe_policy",
            kBidirectionalFeasibilityCompiled
                ? "p0v4_frozen_dual_task_meet_journey_label_v1"
                : "disabled"
        },
        {
            "bidirectional_midpoint_meet_policy",
            kBidirectionalFeasibilityCompiled
                ? "p0v4_frozen_dual_depot_midpoint_meet_v1"
                : "disabled"
        },
        {
            "bidirectional_feasibility_certificate_authority",
            "none"
        },
        {"dssr_certificate_kind", "DSSR_RELAXATION_LOWER_BOUND"},
    };
}

}  // namespace lunar_spprc
