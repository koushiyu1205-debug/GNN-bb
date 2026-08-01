#include "lunar_spprc/native_pricer.hpp"

#include <algorithm>
#include <array>
#include <cassert>
#include <bit>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <list>
#include <memory>
#include <mutex>
#include <queue>
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
            state->guidance_score += task.guidance_priority;
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
        std::size_t arc_count
    )
        : task_rows(task_count), arc_rows(arc_count) {
        for (std::size_t index = 0; index < task_rows.size(); ++index) {
            task_rows[index].task_index = index;
        }
        for (std::size_t index = 0; index < arc_rows.size(); ++index) {
            arc_rows[index].task_index = index;
        }
    }

    std::vector<TaskDominanceTraceRow> task_rows;
    std::vector<TaskDominanceTraceRow> arc_rows;
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
                              double proof_queue_guidance_bucket_width)
        : Base(factory, std::move(params)),
          model_(std::move(model)),
          proof_queue_policy_(proof_queue_policy),
          proof_queue_guidance_bucket_width_(
              proof_queue_guidance_bucket_width) {}

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
    void release_request_memory() { release_label_memory(); }

  private:
    void extract_solution(const Label& end_label) override {
        const auto size_before = this->solutions_.size();
        Base::extract_solution(end_label);
        if (!trace_enabled_ || this->solutions_.size() == size_before) {
            return;
        }
        const double reduced_cost = end_label.get_cost();
        constexpr double improvement_epsilon = 1.0e-12;
        if (!(reduced_cost < best_reduced_cost_ - improvement_epsilon)) {
            return;
        }
        best_reduced_cost_ = reduced_cost;
        ++best_reduced_cost_event_count_total_;
        if (best_reduced_cost_events_.size() >= max_best_reduced_cost_events_) {
            return;
        }
        const auto elapsed =
            std::chrono::duration<double>(Clock::now() - trace_started_).count();
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
        double guidance_score = 0.0;
        double partial_cost = 0.0;
        std::uint64_t creation_sequence_id = 0;
    };

    struct GreaterCachedKey {
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
            if (
                std::abs(lhs.guidance_score - rhs.guidance_score) >
                key_epsilon
            ) {
                return lhs.guidance_score < rhs.guidance_score;
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

    Pair next_label_iterator() override {
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
            return value;
        }
        if (unprocessed_experimental_.empty()) {
            return Pair{};
        }
        auto entry = unprocessed_experimental_.top();
        unprocessed_experimental_.pop();
        ++processed_labels_;
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
        }
        unprocessed_experimental_.push(CachedQueueEntry{
            .value = value,
            .can_terminate = (
                state.at_depot && state.task_visit_count > 0
            ),
            .primary_key = primary_key,
            .secondary_key = secondary_key,
            .guidance_score = state.guidance_score,
            .partial_cost = partial_cost,
            .creation_sequence_id = next_creation_sequence_id_++,
        });
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
            decltype(unprocessed_experimental_){};
        Base::release_label_memory();
    }

    std::priority_queue<Pair, std::vector<Pair>, GreaterCost>
        unprocessed_q0_;
    std::priority_queue<
        CachedQueueEntry,
        std::vector<CachedQueueEntry>,
        GreaterCachedKey
    > unprocessed_experimental_;
    std::shared_ptr<const Model> model_;
    ProofQueuePolicy proof_queue_policy_ =
        ProofQueuePolicy::Q0PartialCost;
    double proof_queue_guidance_bucket_width_ = 0.01;
    std::uint64_t next_creation_sequence_id_ = 0;
    std::size_t processed_labels_ = 0;
    static constexpr std::size_t max_best_reduced_cost_events_ = 512;
    Clock::time_point trace_started_{};
    bool trace_enabled_ = false;
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
            params.completion_bound_enabled ||
            params.proof_queue_potential_trace_enabled ||
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
    for (const auto& task : model->tasks) {
        model->positive_task_dual_sum += std::max(0.0, task.dual);
    }
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
        params.proof_queue_potential_trace_enabled
            ? std::make_shared<ProofQueuePotentialTrace>(
                  model->tasks.size(),
                  model->arcs.size())
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
                                        params.proof_queue_guidance_bucket_width);
    const auto started = std::chrono::steady_clock::now();
    algorithm.begin_best_reduced_cost_trace(started, !params.exact_proof);
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
        output.telemetry.proof_queue_potential_trace =
            proof_queue_potential_trace->task_rows;
        output.telemetry.proof_queue_arc_potential_trace =
            proof_queue_potential_trace->arc_rows;
    }
    output.routes.reserve(result.solutions.size());
    for (const auto& solution : result.solutions) {
        output.routes.push_back(reconstruct_route(solution, *model, built.actions_by_arc_id));
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
        {"guidance_ordering", "negative_harvest_task_arc_priority_v1"},
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
