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
#include <utility>

#include "rcspp/rcspp.hpp"

namespace lunar_spprc {
namespace {

// Native v1 accepts at most 100 tasks, so the elementary visited set always
// fits in two machine words.  Keep it inline in every label: State is copied on
// each arc extension, and a heap-backed vector here would turn the hottest
// exact-search operation into an allocation/copy/deallocation cycle.
using VisitedMask = std::array<std::uint64_t, 2>;

struct Action {
    ActionKind kind = ActionKind::Terminate;
    std::size_t task_index = 0;
    std::string path_type;
    double travel_time = 0.0;
    double energy = 0.0;
    double risk = 0.0;
    double distance = 0.0;
    double shadow = 0.0;
};

struct State {
    bool valid = true;
    bool at_depot = true;
    VisitedMask visited{};
    std::size_t visited_count = 0;
    std::size_t sortie_task_count = 0;
    std::size_t sortie_count = 0;
    std::size_t visited_at_sortie_start = 0;
    double global_time = 0.0;
    double sortie_start_time = 0.0;
    double sortie_demand = 0.0;
    double sortie_energy = 0.0;
    double sortie_shadow = 0.0;
    double raw_operating_cost = 0.0;
    double raw_risk = 0.0;
    double raw_weighted_completion = 0.0;
    double task_dual_reward = 0.0;
    double positive_task_dual_reward = 0.0;
    double cut_dual_reward = 0.0;
    std::vector<std::size_t> cut_overlap_counts;
};

struct JourneyValue {
    bool is_action = false;
    State state;
    Action action;
};

class JourneyResource {
  public:
    JourneyResource() = default;
    explicit JourneyResource(JourneyValue value) : value_(std::move(value)) {}

    void reset() { value_ = JourneyValue{}; }
    [[nodiscard]] const JourneyValue& get_value() const { return value_; }
    void set_value(const JourneyValue& value) { value_ = value; }
    [[nodiscard]] std::string to_string() const {
        std::ostringstream stream;
        stream << "visited=" << value_.state.visited_count << ",time=" << value_.state.global_time;
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
        State next = current_value.state;
        if (next.cut_overlap_counts.empty() && !model_->cuts.empty()) {
            next.cut_overlap_counts.assign(model_->cuts.size(), 0U);
        }
        if (!next.valid || !action_value.is_action) {
            next.valid = false;
            output->set_value(JourneyValue{.state = std::move(next)});
            return;
        }
        const auto& action = action_value.action;
        if (action.kind == ActionKind::VisitTask) {
            extend_visit(action, &next);
        } else if (action.kind == ActionKind::ReturnDepot) {
            extend_return(action, &next);
        } else {
            next.valid = next.at_depot && next.visited_count > 0 &&
                         next.sortie_task_count == 0 &&
                         branch_terminal_feasible(*model_, next);
        }
        output->set_value(JourneyValue{.state = std::move(next)});
    }

    void extend_back(const JourneyResource&, const JourneyResource&, JourneyResource* output) override {
        State invalid;
        invalid.valid = false;
        output->set_value(JourneyValue{.state = std::move(invalid)});
    }

    [[nodiscard]] std::unique_ptr<rcspp::ExtensionFunction<JourneyResource>> clone() const override {
        return std::make_unique<JourneyExtension>(*this);
    }

  private:
    void extend_visit(const Action& action, State* state) const {
        const auto epsilon = 1.0e-9;
        if (action.task_index >= model_->tasks.size() || visited(*state, action.task_index) ||
            state->sortie_task_count >= model_->max_tasks_per_trip) {
            state->valid = false;
            return;
        }
        const auto& task = model_->tasks[action.task_index];
        if (state->sortie_task_count == 0) {
            state->visited_at_sortie_start = state->visited_count;
            state->sortie_start_time = state->global_time;
        }
        const double arrival = state->global_time + action.travel_time;
        const double service_start = std::max(arrival, task.ready_time);
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
        state->task_dual_reward += task.dual;
        state->positive_task_dual_reward += std::max(0.0, task.dual);
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
            auto& overlap = state->cut_overlap_counts.at(cut_index);
            const auto old_coefficient = overlap / cut.divisor;
            ++overlap;
            const auto new_coefficient = overlap / cut.divisor;
            if (new_coefficient > old_coefficient) {
                state->cut_dual_reward +=
                    static_cast<double>(new_coefficient - old_coefficient) * cut.dual;
            }
        }
        state->at_depot = false;
        ++state->sortie_task_count;
        mark_visited(state, action.task_index);
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
            state->visited_count <= state->visited_at_sortie_start) {
            state->valid = false;
            return;
        }
        state->global_time = end_time;
        state->raw_operating_cost += action.distance + action.energy;
        state->raw_risk += action.risk;
        state->at_depot = true;
        state->sortie_demand = 0.0;
        state->sortie_energy = 0.0;
        state->sortie_shadow = 0.0;
        state->sortie_task_count = 0;
        ++state->sortie_count;
        assert(state->visited_count > state->visited_at_sortie_start);
        assert(state->global_time > state->sortie_start_time);
        if (state->sortie_count > state->visited_count) {
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
        const auto& state = resource.get_value().state;
        if (!state.valid) {
            return false;
        }
        if (model_->completion_bound_enabled && node_id_ != sink_id_) {
            ++model_->completion_bound_evaluated_labels;
            const double remaining_positive_dual = std::max(
                0.0,
                model_->positive_task_dual_sum - state.positive_task_dual_reward);
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
            return state.at_depot && state.visited_count > 0 &&
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
        const auto& state = resource.get_value().state;
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
        const auto& lhs = lhs_resource.get_value().state;
        const auto& rhs = rhs_resource.get_value().state;
        if (!lhs.valid || !rhs.valid || lhs.at_depot != rhs.at_depot) {
            return false;
        }
        if (lhs.visited != rhs.visited) {
            if (!model_->subset_dominance_enabled || lhs.visited_count == 0 ||
                !visited_subset(lhs, rhs) ||
                lhs.cut_overlap_counts != rhs.cut_overlap_counts ||
                !branch_subset_dominance_compatible(*model_, lhs, rhs)) {
                return false;
            }
        }
        return lhs.global_time <= rhs.global_time + resource_epsilon_ &&
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

using Composition = rcspp::ResourceTypeComposition<JourneyResource, rcspp::RealResource>;

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

class VisitedLabelList {
  public:
    using Label = rcspp::Label<Composition>;
    using LabelPosition = std::list<Label*>::iterator;
    using VisitedKey = VisitedMask;

    explicit VisitedLabelList(std::shared_ptr<const Model> model = nullptr,
                              std::size_t subset_enumeration_limit = 10,
                              double dominance_epsilon = 1.0e-12,
                              double resource_epsilon = 1.0e-9)
        : model_(std::move(model)),
          subset_enumeration_limit_(subset_enumeration_limit),
          dominance_epsilon_(dominance_epsilon),
          resource_epsilon_(resource_epsilon) {}
    // AlgorithmParams only copies the empty prototype container. Runtime
    // containers are created through copy(), so iterator-bearing state is
    // never copied.
    VisitedLabelList(const VisitedLabelList& other)
        : model_(other.model_),
          subset_enumeration_limit_(other.subset_enumeration_limit_),
          dominance_epsilon_(other.dominance_epsilon_),
          resource_epsilon_(other.resource_epsilon_) {}
    VisitedLabelList& operator=(const VisitedLabelList&) = delete;

    [[nodiscard]] VisitedLabelList copy() const {
        return VisitedLabelList{model_, subset_enumeration_limit_, dominance_epsilon_,
                                resource_epsilon_};
    }

    [[nodiscard]] const std::list<Label*>& get_labels() const { return labels_; }

    LabelPosition add_label(Label* label) {
        auto position = labels_.insert(labels_.end(), label);
        auto key = visited_key(*label);
        auto& bucket = buckets_[key];
        const auto bucket_index = bucket.labels.size();
        bucket.labels.push_back(label);
        update_summary(&bucket, *label);
        locations_.emplace(label,
                           Location{.key = std::move(key),
                                    .bucket_index = bucket_index,
                                    .position = position});
        max_bucket_size_ = std::max(max_bucket_size_, bucket.labels.size());
        return position;
    }

    void erase_label(const LabelPosition& position) {
        Label* label = *position;
        remove_location(label, true);
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
            Label* candidate = bucket_it->second.labels[index];
            if (&label == candidate) {
                ++index;
                continue;
            }
            ++dominance_candidate_checks_;
            if (label <= *candidate) {
                candidate->dominated = true;
                remove_location(candidate, true);
                ++removed;
                bucket_it = buckets_.find(key);
            } else {
                ++index;
            }
        }
        return removed;
    }

    [[nodiscard]] bool is_dominated(const Label& label) const {
        const auto bucket_it = buckets_.find(visited_key(label));
        if (bucket_it != buckets_.end()) {
            for (const auto* candidate : bucket_it->second.labels) {
                if (&label == candidate) {
                    continue;
                }
                ++dominance_candidate_checks_;
                if (*candidate <= label) {
                    return true;
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
            if (!branch_subset_dominance_compatible(*model_, state(*bucket.labels.front()), rhs)) {
                continue;
            }
            for (const auto* candidate : bucket.labels) {
                ++dominance_candidate_checks_;
                ++subset_dominance_candidate_checks_;
                if (known_subset_candidate_dominates(*candidate, label)) {
                    ++subset_dominance_rejected_labels_;
                    return true;
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
    struct Bucket {
        std::vector<Label*> labels;
        double min_global_time = std::numeric_limits<double>::infinity();
        double min_sortie_demand = std::numeric_limits<double>::infinity();
        double min_sortie_energy = std::numeric_limits<double>::infinity();
        double min_sortie_shadow = std::numeric_limits<double>::infinity();
        std::size_t min_sortie_task_count = std::numeric_limits<std::size_t>::max();
        double min_reduced_cost = std::numeric_limits<double>::infinity();
    };

    struct Location {
        VisitedKey key;
        std::size_t bucket_index = 0;
        LabelPosition position;
    };

    static const State& state(const Label& label) {
        return label.get_resource()
            .template get_component<JourneyResource>(0)
            .get_value()
            .get_value()
            .state;
    }

    static VisitedKey visited_key(const Label& label) { return state(label).visited; }

    void update_summary(Bucket* bucket, const Label& label) const {
        const auto& value = state(label);
        bucket->min_global_time = std::min(bucket->min_global_time, value.global_time);
        bucket->min_sortie_demand = std::min(bucket->min_sortie_demand, value.sortie_demand);
        bucket->min_sortie_energy = std::min(bucket->min_sortie_energy, value.sortie_energy);
        bucket->min_sortie_shadow = std::min(bucket->min_sortie_shadow, value.sortie_shadow);
        bucket->min_sortie_task_count =
            std::min(bucket->min_sortie_task_count, value.sortie_task_count);
        bucket->min_reduced_cost =
            std::min(bucket->min_reduced_cost, reduced_cost(*model_, value));
    }

    [[nodiscard]] bool summary_can_contain_dominator(const Bucket& bucket,
                                                     const State& rhs) const {
        // These are independent optimistic minima.  A stale minimum after a label
        // deletion can only admit an unnecessary bucket scan; it can never suppress
        // a real dominator, so no exactness or certificate assumption is introduced.
        return bucket.min_global_time <= rhs.global_time + resource_epsilon_ &&
               bucket.min_sortie_demand <= rhs.sortie_demand + resource_epsilon_ &&
               bucket.min_sortie_energy <= rhs.sortie_energy + resource_epsilon_ &&
               bucket.min_sortie_shadow <= rhs.sortie_shadow + resource_epsilon_ &&
               bucket.min_sortie_task_count <= rhs.sortie_task_count &&
               bucket.min_reduced_cost <=
                   reduced_cost(*model_, rhs) + dominance_epsilon_;
    }

    [[nodiscard]] bool known_subset_candidate_dominates(const Label& lhs_label,
                                                         const Label& rhs_label) const {
        const auto& lhs = state(lhs_label);
        const auto& rhs = state(rhs_label);
        if (!lhs.valid || !rhs.valid || lhs.at_depot != rhs.at_depot ||
            lhs.cut_overlap_counts != rhs.cut_overlap_counts) {
            return false;
        }
        if (lhs.global_time > rhs.global_time + resource_epsilon_ ||
            lhs.sortie_demand > rhs.sortie_demand + resource_epsilon_ ||
            lhs.sortie_energy > rhs.sortie_energy + resource_epsilon_ ||
            lhs.sortie_shadow > rhs.sortie_shadow + resource_epsilon_ ||
            lhs.sortie_task_count > rhs.sortie_task_count ||
            reduced_cost(*model_, lhs) >
                reduced_cost(*model_, rhs) + dominance_epsilon_) {
            return false;
        }
        // The composed graph currently carries one auxiliary RealResource.  Mirror
        // its component-wise dominance check explicitly so this hot-path shortcut
        // remains equivalent to Label::operator<= if that resource becomes nonzero.
        const auto& lhs_aux = lhs_label.get_resource()
                                  .template get_component<rcspp::RealResource>(0)
                                  .get_value();
        const auto& rhs_aux = rhs_label.get_resource()
                                  .template get_component<rcspp::RealResource>(0)
                                  .get_value();
        return lhs_aux.leq(rhs_aux);
    }

    void remove_location(Label* label, bool erase_from_master) {
        const auto location_it = locations_.find(label);
        if (location_it == locations_.end()) {
            return;
        }
        const auto key = location_it->second.key;
        const auto index = location_it->second.bucket_index;
        const auto position = location_it->second.position;
        auto bucket_it = buckets_.find(key);
        assert(bucket_it != buckets_.end());
        auto& bucket = bucket_it->second;
        assert(index < bucket.labels.size() && bucket.labels[index] == label);
        Label* moved = bucket.labels.back();
        bucket.labels[index] = moved;
        bucket.labels.pop_back();
        if (moved != label) {
            locations_.at(moved).bucket_index = index;
        }
        locations_.erase(location_it);
        if (bucket.labels.empty()) {
            buckets_.erase(bucket_it);
        }
        if (erase_from_master) {
            labels_.erase(position);
        }
    }

    std::list<Label*> labels_;
    std::unordered_map<VisitedKey, Bucket, VisitedKeyHash> buckets_;
    std::unordered_map<Label*, Location> locations_;
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
};

using LabelList = VisitedLabelList;

class AuditedBestFirstDominance final
    : public rcspp::DominanceAlgorithm<Composition, LabelList> {
  public:
    using Base = rcspp::DominanceAlgorithm<Composition, LabelList>;
    using Pair = rcspp::LabelIteratorPair<Composition>;

    AuditedBestFirstDominance(rcspp::ResourceFactory<Composition>* factory,
                              rcspp::AlgorithmParams<LabelList> params)
        : Base(factory, std::move(params)) {}

    [[nodiscard]] std::size_t extended_labels() const { return this->num_extended_labels_; }
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
    void release_request_memory() { release_label_memory(); }

  private:
    struct GreaterCost {
        bool operator()(const Pair& lhs, const Pair& rhs) const {
            const auto& lhs_state = lhs.first->get_resource()
                                        .template get_component<JourneyResource>(0)
                                        .get_value()
                                        .get_value()
                                        .state;
            const auto& rhs_state = rhs.first->get_resource()
                                        .template get_component<JourneyResource>(0)
                                        .get_value()
                                        .get_value()
                                        .state;
            const bool lhs_can_terminate = lhs_state.at_depot && lhs_state.visited_count > 0;
            const bool rhs_can_terminate = rhs_state.at_depot && rhs_state.visited_count > 0;
            if (lhs_can_terminate != rhs_can_terminate) {
                return !lhs_can_terminate;
            }
            return lhs.first->get_cost() > rhs.first->get_cost();
        }
    };

    Pair next_label_iterator() override {
        if (unprocessed_.empty()) {
            return Pair{};
        }
        auto value = unprocessed_.top();
        unprocessed_.pop();
        return value;
    }

    [[nodiscard]] std::size_t number_of_labels() const override {
        return unprocessed_.size();
    }

    void add_new_unprocessed_label(const Pair& value) override { unprocessed_.push(value); }

    void prepareNextPhase() override {}

    void on_memory_pressure() override {
        // Exact mode configures pressure at the hard limit, and the upstream
        // main loop checks the hard limit first. Reaching this callback is a
        // certificate blocker, never permission to drop a label.
        this->memory_pressure_triggered_ = true;
    }

    void release_label_memory() override {
        unprocessed_ = decltype(unprocessed_){};
        Base::release_label_memory();
    }

    std::priority_queue<Pair, std::vector<Pair>, GreaterCost> unprocessed_;
};

struct BuiltGraph {
    std::unique_ptr<rcspp::ResourceGraph<JourneyResource, rcspp::RealResource>> graph;
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
           ":r=" + std::to_string(params.resource_epsilon);
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
    }
    target->cost_coefficient = source.cost_coefficient;
    target->risk_coefficient = source.risk_coefficient;
    target->completion_coefficient = source.completion_coefficient;
    target->fleet_dual = source.fleet_dual;
    target->branch_decisions = source.branch_decisions;
    target->cuts = source.cuts;
}

BuiltGraph build_graph(std::shared_ptr<const Model> model, const SolveParams& params) {
    const std::size_t task_count = model->tasks.size();
    const std::size_t sink_id = task_count + 1;
    auto graph = std::make_unique<rcspp::ResourceGraph<JourneyResource, rcspp::RealResource>>();
    JourneyValue initial;
    graph->add_resource<JourneyResource>(
        std::make_unique<JourneyExtension>(model),
        std::make_unique<JourneyFeasibility>(model, sink_id),
        std::make_unique<JourneyCost>(model),
        std::make_unique<JourneyDominance>(model, params.dominance_epsilon,
                                           params.resource_epsilon),
        std::make_tuple(initial));
    graph->add_resource<rcspp::RealResource>(
        std::make_unique<rcspp::AdditionExtensionFunction<rcspp::RealResource>>(),
        std::make_unique<rcspp::TrivialFeasibilityFunction<rcspp::RealResource>>(),
        std::make_unique<rcspp::TrivialCostFunction<rcspp::RealResource>>(),
        std::make_unique<rcspp::ValueDominanceFunction<rcspp::RealResource>>());

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
        JourneyValue action_value;
        action_value.is_action = true;
        action_value.action = action;
        auto& arc = graph->add_arc<JourneyResource, rcspp::RealResource>(
            std::make_tuple(std::make_tuple(action_value), std::make_tuple(0.0)),
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
            const bool no_worse = other.travel_time <= candidate.travel_time + epsilon &&
                                  other.energy <= candidate.energy + epsilon &&
                                  other.risk <= candidate.risk + epsilon &&
                                  other.distance <= candidate.distance + epsilon &&
                                  other.shadow <= candidate.shadow + epsilon;
            const bool strictly_better = other.travel_time < candidate.travel_time - epsilon ||
                                         other.energy < candidate.energy - epsilon ||
                                         other.risk < candidate.risk - epsilon ||
                                         other.distance < candidate.distance - epsilon ||
                                         other.shadow < candidate.shadow - epsilon;
            return no_worse && strictly_better;
        });
    };

    for (const auto& arc : model->arcs) {
        if (arc.source == "depot" && arc.target == "depot") {
            continue;
        }
        // All objective coefficients are non-negative. For the same endpoints,
        // an option weakly worse in time and every additive resource/objective
        // component cannot belong to an optimal or negative journey.
        if (option_is_dominated(arc)) {
            continue;
        }
        const auto origin_it = node_by_name.find(arc.source);
        const auto destination_it = node_by_name.find(arc.target);
        if (origin_it == node_by_name.end() || destination_it == node_by_name.end()) {
            continue;
        }
        Action action;
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

SolveOutput solve(const Model& input_model, const SolveParams& params) {
    if (input_model.tasks.empty() || input_model.tasks.size() > 100) {
        throw std::invalid_argument("native v1 requires 1..100 tasks");
    }
    if (input_model.cost_coefficient < 0.0 || input_model.risk_coefficient < 0.0 ||
        input_model.completion_coefficient < 0.0 || input_model.recharge_power <= 0.0) {
        throw std::invalid_argument(
            "native v1 requires non-negative objective coefficients and positive recharge power");
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
    base.stop_after_X_solutions =
        params.exact_proof
            ? rcspp::MAX_INT
            : std::min<std::size_t>(rcspp::MAX_INT, params.harvest_target * 8U);
    base.return_dominated_solutions = !params.exact_proof;
    base.num_labels_to_extend_by_node = rcspp::MAX_INT;
    base.num_max_phases = 1;
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
    base.memory_check_interval = 1000;
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

    rcspp::AlgorithmParams<LabelList> algorithm_params(
        base, LabelList{model, 10, params.dominance_epsilon, params.resource_epsilon});
    AuditedBestFirstDominance algorithm(&built.graph->get_resource_factory(),
                                        std::move(algorithm_params));
    const auto started = std::chrono::steady_clock::now();
    auto result = built.graph->solve<AuditedBestFirstDominance, rcspp::RealResource>(
        &algorithm, -params.negative_epsilon, false, 0);
    const auto elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - started);

    SolveOutput output;
    output.status = rcspp::to_string(result.status);
    output.search_exhaustive = result.status == rcspp::AlgorithmStatus::COMPLETE;
    output.frontier_empty = output.search_exhaustive && algorithm.all_labels_processed();
    output.labels_dropped = algorithm.memory_pressure_triggered();
    output.telemetry.extended_labels = algorithm.extended_labels();
    output.telemetry.dominated_labels = algorithm.dominated_labels();
    output.telemetry.dominance_candidate_checks = algorithm.dominance_candidate_checks();
    output.telemetry.max_visited_bucket_size = algorithm.max_visited_bucket_size();
    output.telemetry.solution_count = result.solutions.size();
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
    output.routes.reserve(result.solutions.size());
    for (const auto& solution : result.solutions) {
        output.routes.push_back(reconstruct_route(solution, *model, built.actions_by_arc_id));
    }
    algorithm.release_request_memory();
    return output;
}

std::unordered_map<std::string, std::string> build_info() {
    return {
        {"rcspp_commit", LUNAR_SPPRC_RCSPP_COMMIT},
        {"build_type", LUNAR_SPPRC_BUILD_TYPE},
        {"compiler", __VERSION__},
        {"cxx_standard", "23"},
        {"memory_pressure_policy", "disabled_for_exact_hard_limit_only"},
        {"branch_support", "ryan_foster_same_different_feasibility"},
        {"cut_support", "subset_row_threshold_crossing_and_fleet_v1"},
        {"completion_bound", "positive_cover_dual_threshold_pruning_v1"},
    };
}

}  // namespace lunar_spprc
