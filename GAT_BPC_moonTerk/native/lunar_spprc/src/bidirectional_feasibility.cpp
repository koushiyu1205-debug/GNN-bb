#include "lunar_spprc/bidirectional_feasibility.hpp"

#include <algorithm>
#include <bit>
#include <chrono>
#include <cmath>
#include <deque>
#include <optional>
#include <queue>
#include <stdexcept>
#include <unordered_map>

namespace lunar_spprc {
namespace {

constexpr double kEpsilon = 1.0e-9;

bool mask_contains(
    const std::array<std::uint64_t, 2>& mask,
    std::size_t task_index
) {
    return ((mask.at(task_index / 64U) >> (task_index % 64U)) & 1U) != 0U;
}

void mask_insert(
    std::array<std::uint64_t, 2>* mask,
    std::size_t task_index
) {
    mask->at(task_index / 64U) |=
        std::uint64_t{1} << (task_index % 64U);
}

bool masks_disjoint(
    const std::array<std::uint64_t, 2>& lhs,
    const std::array<std::uint64_t, 2>& rhs
) {
    return (lhs[0] & rhs[0]) == 0U && (lhs[1] & rhs[1]) == 0U;
}

bool option_is_dominated(
    const Model& model,
    const ArcData& candidate
) {
    constexpr double epsilon = 1.0e-12;
    return std::ranges::any_of(
        model.arcs,
        [&](const ArcData& other) {
            if (
                candidate.source != other.source ||
                candidate.target != other.target ||
                candidate.path_type == other.path_type
            ) {
                return false;
            }
            const bool same_travel_time =
                std::abs(
                    other.travel_time - candidate.travel_time
                ) <= epsilon;
            const bool no_worse =
                same_travel_time &&
                other.energy <= candidate.energy + epsilon &&
                other.risk <= candidate.risk + epsilon &&
                other.distance <= candidate.distance + epsilon &&
                other.shadow <= candidate.shadow + epsilon;
            const bool strictly_better =
                other.energy < candidate.energy - epsilon ||
                other.risk < candidate.risk - epsilon ||
                other.distance < candidate.distance - epsilon ||
                other.shadow < candidate.shadow - epsilon;
            return no_worse && strictly_better;
        });
}

std::array<std::uint64_t, 2> mask_union(
    const std::array<std::uint64_t, 2>& lhs,
    const std::array<std::uint64_t, 2>& rhs
) {
    return {lhs[0] | rhs[0], lhs[1] | rhs[1]};
}

const ArcData& unique_arc(
    const Model& model,
    const std::string& source,
    const std::string& target,
    const std::string& path_type
) {
    const ArcData* found = nullptr;
    for (const auto& arc : model.arcs) {
        if (
            arc.source == source && arc.target == target &&
            arc.path_type == path_type
        ) {
            if (found != nullptr) {
                throw std::invalid_argument(
                    "bidirectional skeleton arc is not unique");
            }
            found = &arc;
        }
    }
    if (found == nullptr) {
        throw std::invalid_argument(
            "bidirectional skeleton references a missing arc");
    }
    return *found;
}

struct JourneyAccumulator {
    std::array<std::uint64_t, 2> task_mask{};
    double current_time = 0.0;
    double raw_operating_cost = 0.0;
    double raw_risk = 0.0;
    double raw_weighted_completion = 0.0;
    double task_dual_reward = 0.0;
    std::size_t task_count = 0;
};

struct ReverseSortiePartial {
    SortiePath skeleton;
    std::array<std::uint64_t, 2> task_mask{};
    double demand = 0.0;
    double energy = 0.0;
    double shadow = 0.0;
};

struct TaskMeetPartial {
    std::array<std::uint16_t, 3> task_indices{};
    std::array<std::size_t, 3> arc_indices{};
    std::uint8_t depth = 0;
    std::array<std::uint64_t, 2> task_mask{};
    double demand = 0.0;
    double energy = 0.0;
    double shadow = 0.0;
    double elapsed = 0.0;
    double release_time = 0.0;
    double latest_departure = std::numeric_limits<double>::infinity();
    double raw_operating_cost = 0.0;
    double raw_risk = 0.0;
    double science_weight = 0.0;
    double weighted_completion_offset = 0.0;
};

struct TaskMeetSortieSummary {
    std::array<std::uint64_t, 2> task_mask{};
    std::array<std::uint16_t, 6> task_indices{};
    std::array<std::size_t, 7> arc_indices{};
    std::size_t task_count = 0;
    double release_time = 0.0;
    double latest_departure = 0.0;
    double duration = 0.0;
    double raw_operating_cost = 0.0;
    double raw_risk = 0.0;
    double science_weight = 0.0;
    double weighted_completion_offset = 0.0;
};

struct InlineTaskMaskHash {
    std::size_t operator()(
        const std::array<std::uint64_t, 2>& mask
    ) const noexcept {
        const auto mixed =
            mask[1] +
            0x9e3779b97f4a7c15ULL +
            (mask[0] << 6U) +
            (mask[0] >> 2U);
        return static_cast<std::size_t>(mask[0] ^ mixed);
    }
};

bool append_sortie(
    const BidirectionalStaticSortie& sortie,
    JourneyAccumulator* accumulator
) {
    if (
        !sortie.structurally_feasible ||
        !masks_disjoint(accumulator->task_mask, sortie.task_mask)
    ) {
        return false;
    }
    const double departure = std::max(
        accumulator->current_time,
        sortie.release_time);
    if (departure > sortie.latest_departure + kEpsilon) {
        return false;
    }
    accumulator->raw_operating_cost += sortie.raw_operating_cost;
    accumulator->raw_risk += sortie.raw_risk;
    accumulator->raw_weighted_completion +=
        sortie.science_weight * departure +
        sortie.weighted_completion_offset;
    accumulator->task_dual_reward += sortie.task_dual_reward;
    accumulator->current_time = departure + sortie.duration;
    accumulator->task_mask =
        mask_union(accumulator->task_mask, sortie.task_mask);
    accumulator->task_count +=
        std::popcount(sortie.task_mask[0]) +
        std::popcount(sortie.task_mask[1]);
    return true;
}

bool branch_feasible(
    const Model& model,
    const std::array<std::uint64_t, 2>& mask
) {
    for (const auto& decision : model.branch_decisions) {
        const bool has_a =
            decision.task_a_exists &&
            mask_contains(mask, decision.task_a);
        const bool has_b =
            decision.task_b_exists &&
            mask_contains(mask, decision.task_b);
        if (
            decision.sense == BranchSense::SameJourney &&
            has_a != has_b
        ) {
            return false;
        }
        if (
            decision.sense == BranchSense::DifferentJourney &&
            has_a && has_b
        ) {
            return false;
        }
    }
    return true;
}

bool different_branch_feasible(
    const Model& model,
    const std::array<std::uint64_t, 2>& mask
) {
    for (const auto& decision : model.branch_decisions) {
        if (decision.sense != BranchSense::DifferentJourney) {
            continue;
        }
        const bool has_a =
            decision.task_a_exists &&
            mask_contains(mask, decision.task_a);
        const bool has_b =
            decision.task_b_exists &&
            mask_contains(mask, decision.task_b);
        if (has_a && has_b) {
            return false;
        }
    }
    return true;
}

bool branch_subset_compatible(
    const Model& model,
    const std::array<std::uint64_t, 2>& lhs,
    const std::array<std::uint64_t, 2>& rhs
) {
    for (const auto& decision : model.branch_decisions) {
        if (decision.sense != BranchSense::SameJourney) {
            continue;
        }
        const unsigned lhs_code =
            (
                decision.task_a_exists &&
                mask_contains(lhs, decision.task_a)
                    ? 1U
                    : 0U
            ) |
            (
                decision.task_b_exists &&
                mask_contains(lhs, decision.task_b)
                    ? 2U
                    : 0U
            );
        const unsigned rhs_code =
            (
                decision.task_a_exists &&
                mask_contains(rhs, decision.task_a)
                    ? 1U
                    : 0U
            ) |
            (
                decision.task_b_exists &&
                mask_contains(rhs, decision.task_b)
                    ? 2U
                    : 0U
            );
        if (
            lhs_code != rhs_code &&
            !(lhs_code == 0U && rhs_code == 3U)
        ) {
            return false;
        }
    }
    return true;
}

bool cut_subset_compatible(
    const Model& model,
    const std::array<std::uint64_t, 2>& lhs,
    const std::array<std::uint64_t, 2>& rhs
) {
    for (const auto& cut : model.cuts) {
        if (cut.kind == CutKind::FleetLowerBound) {
            const bool lhs_nonempty =
                lhs[0] != 0U || lhs[1] != 0U;
            const bool rhs_nonempty =
                rhs[0] != 0U || rhs[1] != 0U;
            if (lhs_nonempty != rhs_nonempty) {
                return false;
            }
            continue;
        }
        std::size_t lhs_overlap = 0U;
        std::size_t rhs_overlap = 0U;
        for (
            std::size_t word = 0U;
            word < lhs.size();
            ++word
        ) {
            const auto cut_word =
                word < cut.task_mask.size()
                    ? cut.task_mask[word]
                    : std::uint64_t{0};
            lhs_overlap += std::popcount(lhs[word] & cut_word);
            rhs_overlap += std::popcount(rhs[word] & cut_word);
        }
        if (
            lhs_overlap % cut.divisor !=
            rhs_overlap % cut.divisor
        ) {
            return false;
        }
    }
    return true;
}

double cut_dual_reward(
    const Model& model,
    const std::array<std::uint64_t, 2>& mask
) {
    double reward = 0.0;
    for (const auto& cut : model.cuts) {
        if (cut.kind == CutKind::FleetLowerBound) {
            if (mask[0] != 0U || mask[1] != 0U) {
                reward += cut.dual;
            }
            continue;
        }
        std::size_t overlap = 0;
        for (std::size_t word = 0; word < mask.size(); ++word) {
            const auto cut_word =
                word < cut.task_mask.size()
                    ? cut.task_mask[word]
                    : std::uint64_t{0};
            overlap += std::popcount(mask[word] & cut_word);
        }
        reward +=
            static_cast<double>(overlap / cut.divisor) * cut.dual;
    }
    return reward;
}

}  // namespace

BidirectionalStaticSortie build_bidirectional_static_sortie(
    const Model& model,
    const SortiePath& skeleton
) {
    BidirectionalStaticSortie result;
    result.skeleton = skeleton;
    if (
        skeleton.tasks.empty() ||
        skeleton.tasks.size() > model.max_tasks_per_trip ||
        skeleton.path_types.size() != skeleton.tasks.size() + 1U
    ) {
        return result;
    }
    std::unordered_map<std::string, const Task*> task_by_id;
    for (const auto& task : model.tasks) {
        task_by_id.emplace(task.id, &task);
    }
    std::string current = "depot";
    double elapsed = 0.0;
    double release = 0.0;
    double latest = model.horizon;
    double distance = 0.0;
    double energy = 0.0;
    double risk = 0.0;
    double shadow = 0.0;
    double demand = 0.0;
    double service_cost = 0.0;
    for (
        std::size_t position = 0;
        position < skeleton.tasks.size();
        ++position
    ) {
        const auto found = task_by_id.find(skeleton.tasks[position]);
        if (found == task_by_id.end()) {
            throw std::invalid_argument(
                "bidirectional skeleton references an unknown task");
        }
        const auto& task = *found->second;
        if (mask_contains(result.task_mask, task.index)) {
            return result;
        }
        const auto& arc = unique_arc(
            model,
            current,
            task.id,
            skeleton.path_types[position]);
        elapsed += arc.travel_time;
        distance += arc.distance;
        energy += arc.energy;
        risk += arc.risk;
        shadow += arc.shadow;
        release = std::max(
            release,
            task.ready_time - elapsed);
        latest = std::min(
            latest,
            task.due_time - task.service_time - elapsed);
        result.weighted_completion_offset +=
            task.science_weight * (elapsed + task.service_time);
        result.science_weight += task.science_weight;
        elapsed += task.service_time;
        energy += task.service_energy;
        risk +=
            task.local_thermal_risk * task.service_time * 0.01;
        shadow +=
            task.local_shadow_score * task.service_time;
        demand += task.demand;
        service_cost += task.service_cost;
        result.task_dual_reward += task.dual;
        mask_insert(&result.task_mask, task.index);
        current = task.id;
    }
    const auto& back = unique_arc(
        model,
        current,
        "depot",
        skeleton.path_types.back());
    elapsed += back.travel_time;
    distance += back.distance;
    energy += back.energy;
    risk += back.risk;
    shadow += back.shadow;
    const double recharge =
        model.dock_overhead +
        energy / std::max(kEpsilon, model.recharge_power);
    result.duration = elapsed + recharge;
    result.release_time = release;
    result.latest_departure = std::min(
        latest,
        model.horizon - result.duration);
    result.raw_operating_cost =
        distance + energy + service_cost;
    result.raw_risk = risk;
    result.structurally_feasible =
        demand <= model.capacity + kEpsilon &&
        energy <= model.energy_limit + kEpsilon &&
        shadow <= model.shadow_limit + kEpsilon &&
        result.release_time <= result.latest_departure + kEpsilon;
    return result;
}

BidirectionalSuffixSummary summarize_bidirectional_suffix(
    const std::vector<BidirectionalStaticSortie>& sorties
) {
    BidirectionalSuffixSummary result;
    result.sorties = sorties;
    result.structurally_feasible = true;
    for (const auto& sortie : sorties) {
        if (
            !sortie.structurally_feasible ||
            !masks_disjoint(result.task_mask, sortie.task_mask)
        ) {
            result.structurally_feasible = false;
        }
        result.task_mask =
            mask_union(result.task_mask, sortie.task_mask);
    }
    double latest = std::numeric_limits<double>::infinity();
    for (auto it = sorties.rbegin(); it != sorties.rend(); ++it) {
        double cap = it->latest_departure;
        if (std::isfinite(latest)) {
            cap = std::min(cap, latest - it->duration);
        }
        if (it->release_time > cap + kEpsilon) {
            result.structurally_feasible = false;
        }
        latest = cap;
    }
    result.latest_input_time = latest;
    return result;
}

BidirectionalFeasibilityOutput audit_bidirectional_depot_join(
    const Model& model,
    const std::vector<SortiePath>& forward_sorties,
    const std::vector<SortiePath>& backward_sorties
) {
    BidirectionalFeasibilityOutput output;
    output.status = "BIDIRECTIONAL_FEASIBILITY_INCOMPLETE";
    std::vector<BidirectionalStaticSortie> forward;
    std::vector<BidirectionalStaticSortie> backward;
    forward.reserve(forward_sorties.size());
    backward.reserve(backward_sorties.size());
    for (const auto& skeleton : forward_sorties) {
        forward.push_back(
            build_bidirectional_static_sortie(model, skeleton));
    }
    for (const auto& skeleton : backward_sorties) {
        backward.push_back(
            build_bidirectional_static_sortie(model, skeleton));
    }
    const auto suffix = summarize_bidirectional_suffix(backward);
    output.suffix_latest_input_time = suffix.latest_input_time;
    JourneyAccumulator accumulator;
    for (const auto& sortie : forward) {
        if (!append_sortie(sortie, &accumulator)) {
            output.status = "FORWARD_PREFIX_INFEASIBLE";
            return output;
        }
    }
    output.prefix_end_time = accumulator.current_time;
    output.task_sets_disjoint =
        masks_disjoint(accumulator.task_mask, suffix.task_mask);
    output.suffix_boundary_feasible =
        suffix.structurally_feasible &&
        accumulator.current_time <=
            suffix.latest_input_time + kEpsilon;
    if (!output.task_sets_disjoint) {
        output.status = "TASK_SET_OVERLAP";
        return output;
    }
    if (!output.suffix_boundary_feasible) {
        output.status = "BACKWARD_SUFFIX_BOUNDARY_INFEASIBLE";
        return output;
    }
    for (const auto& sortie : backward) {
        if (!append_sortie(sortie, &accumulator)) {
            output.status = "JOIN_REPLAY_INFEASIBLE";
            return output;
        }
    }
    if (accumulator.task_count == 0U) {
        output.status = "EMPTY_JOURNEY";
        return output;
    }
    output.branch_feasible =
        branch_feasible(model, accumulator.task_mask);
    if (!output.branch_feasible) {
        output.status = "BRANCH_CONTEXT_INFEASIBLE";
        return output;
    }
    output.cut_dual_reward =
        cut_dual_reward(model, accumulator.task_mask);
    output.journey_end_time = accumulator.current_time;
    output.raw_operating_cost = accumulator.raw_operating_cost;
    output.raw_risk = accumulator.raw_risk;
    output.raw_weighted_completion =
        accumulator.raw_weighted_completion;
    output.task_dual_reward = accumulator.task_dual_reward;
    output.true_reduced_cost =
        model.cost_coefficient * accumulator.raw_operating_cost +
        model.risk_coefficient * accumulator.raw_risk +
        model.completion_coefficient *
            accumulator.raw_weighted_completion -
        accumulator.task_dual_reward -
        model.fleet_dual -
        output.cut_dual_reward;
    output.task_count = accumulator.task_count;
    output.sortie_count =
        forward_sorties.size() + backward_sorties.size();
    output.static_objective_finite =
        std::isfinite(output.true_reduced_cost);
    output.feasible = output.static_objective_finite;
    output.status = output.feasible
        ? "FEASIBLE_JOIN_DIAGNOSTIC_ONLY"
        : "OBJECTIVE_RECOMPOSITION_MISMATCH";
    return output;
}

BidirectionalBackwardProbeOutput probe_bidirectional_backward_frontier(
    const Model& model,
    const BidirectionalBackwardProbeParams& params
) {
    if (
        model.tasks.empty() ||
        model.tasks.size() > 100U ||
        model.max_tasks_per_trip == 0U
    ) {
        throw std::invalid_argument(
            "bidirectional backward probe requires 1..100 tasks "
            "and a positive sortie task limit");
    }
    if (
        !std::isfinite(params.timeout_seconds) ||
        params.timeout_seconds <= 0.0
    ) {
        throw std::invalid_argument(
            "bidirectional backward probe timeout must be finite "
            "and positive");
    }
    const auto started = std::chrono::steady_clock::now();
    BidirectionalBackwardProbeOutput output;
    output.status = "BACKWARD_FRONTIER_INCOMPLETE";
    output.partial_states_by_task_depth.assign(
        model.max_tasks_per_trip + 1U,
        0U);
    output.feasible_sorties_by_task_depth.assign(
        model.max_tasks_per_trip + 1U,
        0U);

    std::unordered_map<std::string, const Task*> task_by_id;
    for (const auto& task : model.tasks) {
        task_by_id.emplace(task.id, &task);
    }
    std::unordered_map<
        std::string,
        std::vector<const ArcData*>
    > incoming_by_target;
    std::vector<const ArcData*> return_arcs;
    for (const auto& arc : model.arcs) {
        if (
            (arc.source == "depot" && arc.target == "depot") ||
            option_is_dominated(model, arc)
        ) {
            continue;
        }
        incoming_by_target[arc.target].push_back(&arc);
        if (
            arc.target == "depot" &&
            task_by_id.contains(arc.source)
        ) {
            return_arcs.push_back(&arc);
        }
    }
    auto arc_order = [](const ArcData* lhs, const ArcData* rhs) {
        return std::tie(
                   lhs->source,
                   lhs->target,
                   lhs->path_type
               ) <
               std::tie(
                   rhs->source,
                   rhs->target,
                   rhs->path_type
               );
    };
    std::ranges::sort(return_arcs, arc_order);
    for (auto& [_, arcs] : incoming_by_target) {
        std::ranges::sort(arcs, arc_order);
    }

    std::deque<ReverseSortiePartial> frontier;
    for (const auto* arc : return_arcs) {
        const auto task_it = task_by_id.find(arc->source);
        if (task_it == task_by_id.end()) {
            continue;
        }
        const auto& task = *task_it->second;
        ReverseSortiePartial partial;
        partial.skeleton.tasks = {task.id};
        partial.skeleton.path_types = {arc->path_type};
        mask_insert(&partial.task_mask, task.index);
        partial.demand = task.demand;
        partial.energy = arc->energy + task.service_energy;
        partial.shadow =
            arc->shadow +
            task.local_shadow_score * task.service_time;
        if (
            partial.demand > model.capacity + kEpsilon ||
            partial.energy > model.energy_limit + kEpsilon ||
            partial.shadow > model.shadow_limit + kEpsilon
        ) {
            ++output.resource_pruned_partial_states;
            continue;
        }
        frontier.push_back(std::move(partial));
        ++output.generated_partial_states;
        ++output.partial_states_by_task_depth[1];
    }
    output.max_frontier_size = frontier.size();

    auto limit_reached = [&]() {
        return (
            params.max_partial_states > 0U &&
            output.generated_partial_states >=
                params.max_partial_states
        ) || (
            params.max_completed_sorties > 0U &&
            output.feasible_backward_sortie_seeds >=
                params.max_completed_sorties
        );
    };
    auto timed_out = [&]() {
        return std::chrono::duration<double>(
                   std::chrono::steady_clock::now() - started
               ).count() >= params.timeout_seconds;
    };

    while (!frontier.empty()) {
        if (limit_reached()) {
            output.status = "BACKWARD_FRONTIER_LIMIT";
            break;
        }
        if (
            output.processed_partial_states % 4096U == 0U &&
            timed_out()
        ) {
            output.status = "BACKWARD_FRONTIER_TIMEOUT";
            break;
        }
        auto current = std::move(frontier.front());
        frontier.pop_front();
        ++output.processed_partial_states;
        const auto first_task = current.skeleton.tasks.front();
        const auto incoming_it =
            incoming_by_target.find(first_task);
        if (incoming_it == incoming_by_target.end()) {
            continue;
        }
        for (const auto* arc : incoming_it->second) {
            if (arc->source == "depot") {
                auto completed = current.skeleton;
                completed.path_types.insert(
                    completed.path_types.begin(),
                    arc->path_type);
                ++output.completed_sortie_candidates;
                const auto transform =
                    build_bidirectional_static_sortie(
                        model,
                        completed);
                if (transform.structurally_feasible) {
                    ++output.feasible_backward_sortie_seeds;
                    ++output.feasible_sorties_by_task_depth.at(
                        completed.tasks.size());
                } else {
                    ++output.infeasible_completed_sorties;
                }
                if (limit_reached()) {
                    break;
                }
                continue;
            }
            const auto predecessor_it =
                task_by_id.find(arc->source);
            if (predecessor_it == task_by_id.end()) {
                continue;
            }
            const auto& predecessor = *predecessor_it->second;
            if (
                mask_contains(
                    current.task_mask,
                    predecessor.index)
            ) {
                ++output.duplicate_task_pruned_extensions;
                continue;
            }
            if (
                current.skeleton.tasks.size() >=
                model.max_tasks_per_trip
            ) {
                continue;
            }
            ReverseSortiePartial next = current;
            next.skeleton.tasks.insert(
                next.skeleton.tasks.begin(),
                predecessor.id);
            next.skeleton.path_types.insert(
                next.skeleton.path_types.begin(),
                arc->path_type);
            mask_insert(&next.task_mask, predecessor.index);
            next.demand += predecessor.demand;
            next.energy +=
                arc->energy + predecessor.service_energy;
            next.shadow +=
                arc->shadow +
                predecessor.local_shadow_score *
                    predecessor.service_time;
            if (
                next.demand > model.capacity + kEpsilon ||
                next.energy > model.energy_limit + kEpsilon ||
                next.shadow > model.shadow_limit + kEpsilon
            ) {
                ++output.resource_pruned_partial_states;
                continue;
            }
            const auto depth = next.skeleton.tasks.size();
            frontier.push_back(std::move(next));
            ++output.generated_partial_states;
            ++output.partial_states_by_task_depth.at(depth);
            output.max_frontier_size =
                std::max(
                    output.max_frontier_size,
                    frontier.size());
            if (limit_reached()) {
                break;
            }
        }
    }
    if (frontier.empty() && !limit_reached()) {
        output.search_exhaustive = true;
        output.frontier_empty = true;
        output.status =
            "BACKWARD_SORTIE_SEED_ENUMERATION_COMPLETE";
    }
    output.wall_time_seconds =
        std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started
        ).count();
    return output;
}

BidirectionalTaskMeetProbeOutput probe_bidirectional_task_meet_frontier(
    const Model& model,
    const BidirectionalTaskMeetProbeParams& params
) {
    if (
        model.tasks.empty() ||
        model.tasks.size() > 100U ||
        model.max_tasks_per_trip == 0U ||
        model.max_tasks_per_trip > 6U
    ) {
        throw std::invalid_argument(
            "bidirectional task-meet probe requires 1..100 tasks "
            "and a P0V4 sortie task limit in 1..6");
    }
    if (
        params.max_partial_states_per_direction == 0U ||
        params.max_join_checks == 0U ||
        !std::isfinite(params.timeout_seconds) ||
        params.timeout_seconds <= 0.0
    ) {
        throw std::invalid_argument(
            "bidirectional task-meet probe limits must be positive");
    }
    const auto started = std::chrono::steady_clock::now();
    auto timed_out = [&]() {
        return std::chrono::duration<double>(
                   std::chrono::steady_clock::now() - started
               ).count() >= params.timeout_seconds;
    };
    BidirectionalTaskMeetProbeOutput output;
    output.status = "TASK_MEET_INCOMPLETE";
    const auto half_depth =
        (model.max_tasks_per_trip + 1U) / 2U;
    output.forward_states_by_task_depth.assign(
        half_depth + 1U,
        0U);
    output.backward_states_by_task_depth.assign(
        half_depth + 1U,
        0U);
    output.feasible_joined_sorties_by_task_count.assign(
        model.max_tasks_per_trip + 1U,
        0U);
    output.nondominated_sorties_by_task_count.assign(
        model.max_tasks_per_trip + 1U,
        0U);
    std::vector<TaskMeetSortieSummary> feasible_summaries;

    std::vector<const Task*> task_by_index(
        model.tasks.size(),
        nullptr);
    std::unordered_map<std::string, std::size_t> index_by_id;
    for (const auto& task : model.tasks) {
        if (
            task.index >= task_by_index.size() ||
            task_by_index[task.index] != nullptr
        ) {
            throw std::invalid_argument(
                "bidirectional task-meet requires contiguous "
                "unique task indices");
        }
        task_by_index[task.index] = &task;
        index_by_id.emplace(task.id, task.index);
    }
    if (std::ranges::any_of(
            task_by_index,
            [](const Task* task) { return task == nullptr; })) {
        throw std::invalid_argument(
            "bidirectional task-meet task index mapping is incomplete");
    }

    std::vector<std::size_t> start_arcs;
    std::vector<std::size_t> return_arcs;
    std::vector<std::size_t> task_link_arcs;
    std::vector<std::vector<std::size_t>> outgoing(
        model.tasks.size());
    std::vector<std::vector<std::size_t>> incoming(
        model.tasks.size());
    for (
        std::size_t arc_index = 0;
        arc_index < model.arcs.size();
        ++arc_index
    ) {
        const auto& arc = model.arcs[arc_index];
        if (
            (arc.source == "depot" && arc.target == "depot") ||
            option_is_dominated(model, arc)
        ) {
            continue;
        }
        const auto source = index_by_id.find(arc.source);
        const auto target = index_by_id.find(arc.target);
        if (arc.source == "depot" && target != index_by_id.end()) {
            start_arcs.push_back(arc_index);
        } else if (
            arc.target == "depot" &&
            source != index_by_id.end()
        ) {
            return_arcs.push_back(arc_index);
        } else if (
            source != index_by_id.end() &&
            target != index_by_id.end()
        ) {
            task_link_arcs.push_back(arc_index);
            outgoing[source->second].push_back(arc_index);
            incoming[target->second].push_back(arc_index);
        }
    }
    auto deterministic_arc_order =
        [&](std::size_t lhs_index, std::size_t rhs_index) {
            const auto& lhs = model.arcs[lhs_index];
            const auto& rhs = model.arcs[rhs_index];
            return std::tie(
                       lhs.source,
                       lhs.target,
                       lhs.path_type
                   ) <
                   std::tie(
                       rhs.source,
                       rhs.target,
                       rhs.path_type
                   );
        };
    std::ranges::sort(start_arcs, deterministic_arc_order);
    std::ranges::sort(return_arcs, deterministic_arc_order);
    std::ranges::sort(task_link_arcs, deterministic_arc_order);
    for (auto& rows : outgoing) {
        std::ranges::sort(rows, deterministic_arc_order);
    }
    for (auto& rows : incoming) {
        std::ranges::sort(rows, deterministic_arc_order);
    }

    using EndpointBuckets =
        std::vector<std::vector<TaskMeetPartial>>;
    std::vector<EndpointBuckets> forward(
        half_depth + 1U,
        EndpointBuckets(model.tasks.size()));
    std::vector<EndpointBuckets> backward(
        half_depth + 1U,
        EndpointBuckets(model.tasks.size()));

    auto partial_resource_feasible =
        [&](const TaskMeetPartial& row) {
            return
                row.demand <= model.capacity + kEpsilon &&
                row.energy <= model.energy_limit + kEpsilon &&
                row.shadow <= model.shadow_limit + kEpsilon;
        };

    for (const auto arc_index : start_arcs) {
        const auto& arc = model.arcs[arc_index];
        const auto task_index = index_by_id.at(arc.target);
        const auto& task = *task_by_index[task_index];
        TaskMeetPartial row;
        row.depth = 1U;
        row.task_indices[0] =
            static_cast<std::uint16_t>(task_index);
        row.arc_indices[0] = arc_index;
        mask_insert(&row.task_mask, task_index);
        row.demand = task.demand;
        row.energy = arc.energy + task.service_energy;
        row.shadow =
            arc.shadow +
            task.local_shadow_score * task.service_time;
        const double arrival_offset = arc.travel_time;
        row.release_time =
            std::max(0.0, task.ready_time - arrival_offset);
        row.latest_departure = std::min(
            model.horizon,
            task.due_time -
                task.service_time -
                arrival_offset);
        row.elapsed = arrival_offset + task.service_time;
        row.raw_operating_cost =
            arc.distance +
            arc.energy +
            task.service_energy +
            task.service_cost;
        row.raw_risk =
            arc.risk +
            task.local_thermal_risk *
                task.service_time * 0.01;
        row.science_weight = task.science_weight;
        row.weighted_completion_offset =
            task.science_weight * row.elapsed;
        if (
            !partial_resource_feasible(row) ||
            row.release_time >
                row.latest_departure + kEpsilon
        ) {
            ++output.forward_resource_pruned_states;
            continue;
        }
        forward[1][task_index].push_back(row);
        ++output.forward_generated_states;
        ++output.forward_states_by_task_depth[1];
    }
    bool forward_limit = false;
    for (
        std::size_t depth = 1U;
        depth < half_depth && !forward_limit;
        ++depth
    ) {
        for (
            std::size_t last_task = 0U;
            last_task < model.tasks.size() && !forward_limit;
            ++last_task
        ) {
            for (const auto& row : forward[depth][last_task]) {
                for (const auto arc_index : outgoing[last_task]) {
                    const auto& arc = model.arcs[arc_index];
                    const auto next_task =
                        index_by_id.at(arc.target);
                    if (mask_contains(row.task_mask, next_task)) {
                        ++output
                              .forward_duplicate_task_pruned_extensions;
                        continue;
                    }
                    auto next = row;
                    const auto& task = *task_by_index[next_task];
                    next.depth =
                        static_cast<std::uint8_t>(depth + 1U);
                    next.task_indices[depth] =
                        static_cast<std::uint16_t>(next_task);
                    next.arc_indices[depth] = arc_index;
                    mask_insert(&next.task_mask, next_task);
                    next.demand += task.demand;
                    next.energy +=
                        arc.energy + task.service_energy;
                    next.shadow +=
                        arc.shadow +
                        task.local_shadow_score *
                            task.service_time;
                    const double arrival_offset =
                        next.elapsed + arc.travel_time;
                    next.release_time = std::max(
                        next.release_time,
                        task.ready_time - arrival_offset);
                    next.latest_departure = std::min(
                        next.latest_departure,
                        task.due_time -
                            task.service_time -
                            arrival_offset);
                    next.elapsed =
                        arrival_offset + task.service_time;
                    next.raw_operating_cost +=
                        arc.distance +
                        arc.energy +
                        task.service_energy +
                        task.service_cost;
                    next.raw_risk +=
                        arc.risk +
                        task.local_thermal_risk *
                            task.service_time * 0.01;
                    next.science_weight +=
                        task.science_weight;
                    next.weighted_completion_offset +=
                        task.science_weight * next.elapsed;
                    if (
                        !partial_resource_feasible(next) ||
                        next.release_time >
                            next.latest_departure + kEpsilon
                    ) {
                        ++output.forward_resource_pruned_states;
                        continue;
                    }
                    forward[depth + 1U][next_task].push_back(next);
                    ++output.forward_generated_states;
                    ++output.forward_states_by_task_depth[
                        depth + 1U];
                    if (
                        output.forward_generated_states >=
                        params.max_partial_states_per_direction
                    ) {
                        forward_limit = true;
                        break;
                    }
                }
                if (
                    output.forward_generated_states % 4096U == 0U &&
                    timed_out()
                ) {
                    forward_limit = true;
                    break;
                }
            }
        }
    }
    output.forward_generation_exhaustive =
        !forward_limit && !timed_out();

    bool backward_limit = timed_out();
    if (!backward_limit) {
        for (const auto arc_index : return_arcs) {
            const auto& arc = model.arcs[arc_index];
            const auto task_index = index_by_id.at(arc.source);
            const auto& task = *task_by_index[task_index];
            TaskMeetPartial row;
            row.depth = 1U;
            row.task_indices[0] =
                static_cast<std::uint16_t>(task_index);
            row.arc_indices[0] = arc_index;
            mask_insert(&row.task_mask, task_index);
            row.demand = task.demand;
            row.energy = arc.energy + task.service_energy;
            row.shadow =
                arc.shadow +
                task.local_shadow_score * task.service_time;
            // Backward timing is represented at the service start of the
            // first task in this suffix.  Internal task windows propagate
            // independently of the unknown depot/meet prefix; the horizon
            // cap additionally includes the exact return and recharge tail.
            row.release_time = task.ready_time;
            row.latest_departure =
                task.due_time - task.service_time;
            row.elapsed =
                task.service_time + arc.travel_time;
            row.raw_operating_cost =
                arc.distance +
                arc.energy +
                task.service_energy +
                task.service_cost;
            row.raw_risk =
                arc.risk +
                task.local_thermal_risk *
                    task.service_time * 0.01;
            row.science_weight = task.science_weight;
            row.weighted_completion_offset =
                task.science_weight * task.service_time;
            const double horizon_latest =
                model.horizon -
                (
                    row.elapsed +
                    model.dock_overhead +
                    row.energy /
                        std::max(kEpsilon, model.recharge_power)
                );
            if (
                !partial_resource_feasible(row) ||
                row.release_time >
                    std::min(
                        row.latest_departure,
                        horizon_latest
                    ) + kEpsilon
            ) {
                ++output.backward_resource_pruned_states;
                continue;
            }
            backward[1][task_index].push_back(row);
            ++output.backward_generated_states;
            ++output.backward_states_by_task_depth[1];
        }
    }
    for (
        std::size_t depth = 1U;
        depth < half_depth && !backward_limit;
        ++depth
    ) {
        for (
            std::size_t first_task = 0U;
            first_task < model.tasks.size() && !backward_limit;
            ++first_task
        ) {
            for (const auto& row : backward[depth][first_task]) {
                for (const auto arc_index : incoming[first_task]) {
                    const auto& arc = model.arcs[arc_index];
                    const auto predecessor =
                        index_by_id.at(arc.source);
                    if (
                        mask_contains(
                            row.task_mask,
                            predecessor)
                    ) {
                        ++output
                              .backward_duplicate_task_pruned_extensions;
                        continue;
                    }
                    auto next = row;
                    const auto& task = *task_by_index[predecessor];
                    for (
                        std::size_t index = depth;
                        index > 0U;
                        --index
                    ) {
                        next.task_indices[index] =
                            next.task_indices[index - 1U];
                        next.arc_indices[index] =
                            next.arc_indices[index - 1U];
                    }
                    next.depth =
                        static_cast<std::uint8_t>(depth + 1U);
                    next.task_indices[0] =
                        static_cast<std::uint16_t>(predecessor);
                    next.arc_indices[0] = arc_index;
                    mask_insert(&next.task_mask, predecessor);
                    next.demand += task.demand;
                    next.energy +=
                        arc.energy + task.service_energy;
                    next.shadow +=
                        arc.shadow +
                        task.local_shadow_score *
                            task.service_time;
                    const double predecessor_to_old_first =
                        task.service_time + arc.travel_time;
                    next.release_time = std::max(
                        task.ready_time,
                        row.release_time -
                            predecessor_to_old_first);
                    next.latest_departure = std::min(
                        task.due_time - task.service_time,
                        row.latest_departure -
                            predecessor_to_old_first);
                    next.elapsed =
                        predecessor_to_old_first + row.elapsed;
                    next.raw_operating_cost +=
                        arc.distance +
                        arc.energy +
                        task.service_energy +
                        task.service_cost;
                    next.raw_risk +=
                        arc.risk +
                        task.local_thermal_risk *
                            task.service_time * 0.01;
                    next.weighted_completion_offset =
                        task.science_weight * task.service_time +
                        row.weighted_completion_offset +
                        row.science_weight *
                            predecessor_to_old_first;
                    next.science_weight += task.science_weight;
                    const double horizon_latest =
                        model.horizon -
                        (
                            next.elapsed +
                            model.dock_overhead +
                            next.energy /
                                std::max(
                                    kEpsilon,
                                    model.recharge_power)
                        );
                    if (
                        !partial_resource_feasible(next) ||
                        next.release_time >
                            std::min(
                                next.latest_departure,
                                horizon_latest
                            ) + kEpsilon
                    ) {
                        ++output.backward_resource_pruned_states;
                        continue;
                    }
                    backward[depth + 1U][predecessor].push_back(next);
                    ++output.backward_generated_states;
                    ++output.backward_states_by_task_depth[
                        depth + 1U];
                    if (
                        output.backward_generated_states >=
                        params.max_partial_states_per_direction
                    ) {
                        backward_limit = true;
                        break;
                    }
                }
                if (
                    output.backward_generated_states % 4096U == 0U &&
                    timed_out()
                ) {
                    backward_limit = true;
                    break;
                }
            }
        }
    }
    output.backward_generation_exhaustive =
        !backward_limit && !timed_out();

    bool join_limit = timed_out();
    if (!join_limit) {
        for (
            std::size_t last_task = 0U;
            last_task < model.tasks.size() && !join_limit;
            ++last_task
        ) {
            for (const auto& lhs : forward[1][last_task]) {
                for (const auto return_arc_index : return_arcs) {
                    const auto& back = model.arcs[return_arc_index];
                    if (back.source != task_by_index[last_task]->id) {
                        continue;
                    }
                    ++output.join_pair_checks;
                    ++output.disjoint_join_pairs;
                    if (
                        lhs.energy + back.energy >
                            model.energy_limit + kEpsilon ||
                        lhs.shadow + back.shadow >
                            model.shadow_limit + kEpsilon
                    ) {
                        continue;
                    }
                    ++output.resource_compatible_join_pairs;
                    const double full_energy =
                        lhs.energy + back.energy;
                    const double duration =
                        lhs.elapsed +
                        back.travel_time +
                        model.dock_overhead +
                        full_energy /
                            std::max(
                                kEpsilon,
                                model.recharge_power);
                    const double latest = std::min(
                        lhs.latest_departure,
                        model.horizon - duration);
                    if (
                        lhs.release_time <= latest + kEpsilon
                    ) {
                        ++output.feasible_joined_sorties;
                        ++output
                              .feasible_joined_sorties_by_task_count[1];
                        feasible_summaries.push_back({
                            .task_mask = lhs.task_mask,
                            .task_indices = {
                                lhs.task_indices[0],
                            },
                            .arc_indices = {
                                lhs.arc_indices[0],
                                return_arc_index,
                            },
                            .task_count = 1U,
                            .release_time = lhs.release_time,
                            .latest_departure = latest,
                            .duration = duration,
                            .raw_operating_cost =
                                lhs.raw_operating_cost +
                                back.distance +
                                back.energy,
                            .raw_risk =
                                lhs.raw_risk + back.risk,
                            .science_weight =
                                lhs.science_weight,
                            .weighted_completion_offset =
                                lhs.weighted_completion_offset,
                        });
                    } else {
                        ++output.infeasible_joined_sorties;
                    }
                    if (
                        output.join_pair_checks >=
                        params.max_join_checks
                    ) {
                        join_limit = true;
                        break;
                    }
                }
            }
        }
    }
    for (
        std::size_t total_tasks = 2U;
        total_tasks <= model.max_tasks_per_trip &&
        !join_limit;
        ++total_tasks
    ) {
        const auto forward_depth =
            (total_tasks + 1U) / 2U;
        const auto backward_depth = total_tasks / 2U;
        if (
            forward_depth >= forward.size() ||
            backward_depth >= backward.size()
        ) {
            continue;
        }
        for (const auto link_arc_index : task_link_arcs) {
            const auto& link = model.arcs[link_arc_index];
            const auto last_task = index_by_id.at(link.source);
            const auto first_task = index_by_id.at(link.target);
            for (
                const auto& lhs :
                forward[forward_depth][last_task]
            ) {
                for (
                    const auto& rhs :
                    backward[backward_depth][first_task]
                ) {
                    ++output.join_pair_checks;
                    if (
                        !masks_disjoint(
                            lhs.task_mask,
                            rhs.task_mask)
                    ) {
                        if (
                            output.join_pair_checks >=
                            params.max_join_checks
                        ) {
                            join_limit = true;
                            break;
                        }
                        continue;
                    }
                    ++output.disjoint_join_pairs;
                    if (
                        lhs.demand + rhs.demand >
                            model.capacity + kEpsilon ||
                        lhs.energy + link.energy + rhs.energy >
                            model.energy_limit + kEpsilon ||
                        lhs.shadow + link.shadow + rhs.shadow >
                            model.shadow_limit + kEpsilon
                    ) {
                        if (
                            output.join_pair_checks >=
                            params.max_join_checks
                        ) {
                            join_limit = true;
                            break;
                        }
                        continue;
                    }
                    ++output.resource_compatible_join_pairs;
                    const double rhs_first_offset =
                        lhs.elapsed + link.travel_time;
                    const double full_energy =
                        lhs.energy + link.energy + rhs.energy;
                    const double release = std::max(
                        lhs.release_time,
                        rhs.release_time - rhs_first_offset);
                    const double duration =
                        rhs_first_offset +
                        rhs.elapsed +
                        model.dock_overhead +
                        full_energy /
                            std::max(
                                kEpsilon,
                                model.recharge_power);
                    const double latest = std::min({
                        lhs.latest_departure,
                        rhs.latest_departure - rhs_first_offset,
                        model.horizon - duration,
                    });
                    if (release <= latest + kEpsilon) {
                        ++output.feasible_joined_sorties;
                        ++output
                              .feasible_joined_sorties_by_task_count[
                                  total_tasks];
                        TaskMeetSortieSummary summary;
                        summary.task_mask = mask_union(
                            lhs.task_mask,
                            rhs.task_mask);
                        summary.task_count = total_tasks;
                        for (
                            std::size_t index = 0U;
                            index < lhs.depth;
                            ++index
                        ) {
                            summary.task_indices[index] =
                                lhs.task_indices[index];
                            summary.arc_indices[index] =
                                lhs.arc_indices[index];
                        }
                        summary.arc_indices[lhs.depth] =
                            link_arc_index;
                        for (
                            std::size_t index = 0U;
                            index < rhs.depth;
                            ++index
                        ) {
                            summary.task_indices[
                                lhs.depth + index
                            ] = rhs.task_indices[index];
                            summary.arc_indices[
                                lhs.depth + 1U + index
                            ] = rhs.arc_indices[index];
                        }
                        summary.release_time = release;
                        summary.latest_departure = latest;
                        summary.duration = duration;
                        summary.raw_operating_cost =
                            lhs.raw_operating_cost +
                            link.distance +
                            link.energy +
                            rhs.raw_operating_cost;
                        summary.raw_risk =
                            lhs.raw_risk +
                            link.risk +
                            rhs.raw_risk;
                        summary.science_weight =
                            lhs.science_weight +
                            rhs.science_weight;
                        summary.weighted_completion_offset =
                            lhs.weighted_completion_offset +
                            rhs.weighted_completion_offset +
                            rhs.science_weight *
                                rhs_first_offset;
                        feasible_summaries.push_back(summary);
                    } else {
                        ++output.infeasible_joined_sorties;
                    }
                    if (
                        output.join_pair_checks >=
                            params.max_join_checks ||
                        (
                            output.join_pair_checks % 4096U == 0U &&
                            timed_out()
                        )
                    ) {
                        join_limit = true;
                        break;
                    }
                }
                if (join_limit) {
                    break;
                }
            }
            if (join_limit) {
                break;
            }
        }
    }
    output.join_exhaustive =
        !join_limit &&
        output.forward_generation_exhaustive &&
        output.backward_generation_exhaustive;

    std::unordered_map<
        std::array<std::uint64_t, 2>,
        std::vector<std::size_t>,
        InlineTaskMaskHash
    > summaries_by_task_set;
    summaries_by_task_set.reserve(feasible_summaries.size());
    for (
        std::size_t index = 0U;
        index < feasible_summaries.size();
        ++index
    ) {
        summaries_by_task_set[
            feasible_summaries[index].task_mask
        ].push_back(index);
    }
    output.distinct_task_set_count =
        summaries_by_task_set.size();
    output.task_set_duplicate_sortie_count =
        feasible_summaries.size() -
        output.distinct_task_set_count;

    auto objective_increment =
        [&](const TaskMeetSortieSummary& row, double input_time) {
            return
                model.cost_coefficient *
                    row.raw_operating_cost +
                model.risk_coefficient * row.raw_risk +
                model.completion_coefficient *
                    (
                        row.science_weight *
                            std::max(input_time, row.release_time) +
                        row.weighted_completion_offset
                    );
        };
    auto end_time =
        [](const TaskMeetSortieSummary& row, double input_time) {
            return
                std::max(input_time, row.release_time) +
                row.duration;
        };
    auto dominates_summary =
        [&](const TaskMeetSortieSummary& lhs,
            const TaskMeetSortieSummary& rhs) {
            ++output.sortie_dominance_candidate_checks;
            if (
                lhs.latest_departure + kEpsilon <
                rhs.latest_departure
            ) {
                return false;
            }
            std::array<double, 4> points{
                0.0,
                std::clamp(
                    lhs.release_time,
                    0.0,
                    rhs.latest_departure),
                std::clamp(
                    rhs.release_time,
                    0.0,
                    rhs.latest_departure),
                rhs.latest_departure,
            };
            for (const auto input_time : points) {
                const auto lhs_end = end_time(lhs, input_time);
                const auto rhs_end = end_time(rhs, input_time);
                const auto lhs_objective =
                    objective_increment(lhs, input_time);
                const auto rhs_objective =
                    objective_increment(rhs, input_time);
                if (
                    lhs_end > rhs_end + kEpsilon ||
                    lhs_objective >
                        rhs_objective + kEpsilon
                ) {
                    return false;
                }
            }
            // Exact equality is also safely removable for a fixed task set:
            // master coefficients, branch feasibility, and active-cut
            // coefficients are identical.  The stable insertion order keeps
            // the first representative.
            return true;
        };
    for (const auto& [_, variants] : summaries_by_task_set) {
        output.max_variants_per_task_set = std::max(
            output.max_variants_per_task_set,
            variants.size());
        std::vector<std::size_t> frontier;
        for (const auto candidate_index : variants) {
            bool rejected = false;
            for (const auto existing_index : frontier) {
                if (
                    dominates_summary(
                        feasible_summaries[existing_index],
                        feasible_summaries[candidate_index])
                ) {
                    rejected = true;
                    break;
                }
            }
            if (rejected) {
                ++output.dominated_sortie_count;
                continue;
            }
            std::erase_if(
                frontier,
                [&](std::size_t existing_index) {
                    if (
                        dominates_summary(
                            feasible_summaries[candidate_index],
                            feasible_summaries[existing_index])
                    ) {
                        ++output.dominated_sortie_count;
                        return true;
                    }
                    return false;
                });
            frontier.push_back(candidate_index);
        }
        output.nondominated_sortie_count += frontier.size();
        for (const auto index : frontier) {
            const auto& summary = feasible_summaries[index];
            ++output.nondominated_sorties_by_task_count.at(
                summary.task_count);
            BidirectionalStaticSortie sortie;
            sortie.task_mask = summary.task_mask;
            sortie.release_time = summary.release_time;
            sortie.latest_departure =
                summary.latest_departure;
            sortie.duration = summary.duration;
            sortie.science_weight =
                summary.science_weight;
            sortie.weighted_completion_offset =
                summary.weighted_completion_offset;
            sortie.raw_operating_cost =
                summary.raw_operating_cost;
            sortie.raw_risk = summary.raw_risk;
            sortie.structurally_feasible = true;
            for (
                std::size_t task_position = 0U;
                task_position < summary.task_count;
                ++task_position
            ) {
                const auto task_index =
                    summary.task_indices[task_position];
                sortie.skeleton.tasks.push_back(
                    task_by_index[task_index]->id);
                sortie.task_dual_reward +=
                    task_by_index[task_index]->dual;
            }
            for (
                std::size_t arc_position = 0U;
                arc_position < summary.task_count + 1U;
                ++arc_position
            ) {
                sortie.skeleton.path_types.push_back(
                    model.arcs[
                        summary.arc_indices[arc_position]
                    ].path_type);
            }
            output.nondominated_sorties.push_back(
                std::move(sortie));
        }
    }
    if (output.join_exhaustive) {
        output.status = "TASK_MEET_SORTIE_ENUMERATION_COMPLETE";
    } else if (timed_out()) {
        output.status = "TASK_MEET_TIMEOUT";
    } else if (
        !output.forward_generation_exhaustive ||
        !output.backward_generation_exhaustive
    ) {
        output.status = "TASK_MEET_PARTIAL_STATE_LIMIT";
    } else {
        output.status = "TASK_MEET_JOIN_LIMIT";
    }
    output.wall_time_seconds =
        std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started
        ).count();
    return output;
}

BidirectionalJourneyProbeOutput probe_bidirectional_journey_frontier(
    const Model& model,
    const BidirectionalTaskMeetProbeParams& sortie_params,
    const BidirectionalJourneyProbeParams& journey_params
) {
    if (
        journey_params.max_labels == 0U ||
        journey_params.max_extension_checks == 0U ||
        !std::isfinite(journey_params.timeout_seconds) ||
        journey_params.timeout_seconds <= 0.0 ||
        !std::isfinite(journey_params.negative_epsilon) ||
        journey_params.negative_epsilon < 0.0
    ) {
        throw std::invalid_argument(
            "bidirectional journey probe limits are invalid");
    }
    const auto started = std::chrono::steady_clock::now();
    BidirectionalJourneyProbeOutput output;
    output.status = "JOURNEY_FRONTIER_INCOMPLETE";
    output.accepted_labels_by_task_count.assign(
        model.tasks.size() + 1U,
        0U);
    auto pool_params = sortie_params;
    pool_params.timeout_seconds = std::min(
        pool_params.timeout_seconds,
        journey_params.timeout_seconds);
    auto sortie_pool =
        probe_bidirectional_task_meet_frontier(
            model,
            pool_params);
    output.sortie_pool_size =
        sortie_pool.nondominated_sorties.size();
    if (!sortie_pool.join_exhaustive) {
        output.status = "JOURNEY_SORTIE_POOL_INCOMPLETE";
        output.wall_time_seconds =
            std::chrono::duration<double>(
                std::chrono::steady_clock::now() - started
            ).count();
        return output;
    }

    struct JourneyLabel {
        std::array<std::uint64_t, 2> task_mask{};
        double current_time = 0.0;
        double partial_reduced_cost = 0.0;
        std::uint16_t task_count = 0;
        bool active = true;
    };
    std::vector<JourneyLabel> labels;
    labels.reserve(std::min<std::size_t>(
        journey_params.max_labels,
        1'000'000U));
    labels.push_back(JourneyLabel{});
    output.generated_labels = 1U;
    std::deque<std::size_t> frontier{0U};
    std::unordered_map<
        std::array<std::uint64_t, 2>,
        std::vector<std::size_t>,
        InlineTaskMaskHash
    > dominance_buckets;
    dominance_buckets[{}].push_back(0U);
    output.max_frontier_size = 1U;

    auto elapsed = [&]() {
        return std::chrono::duration<double>(
                   std::chrono::steady_clock::now() - started
               ).count();
    };
    bool label_limit = false;
    bool extension_limit = false;
    bool timeout = false;
    const auto& sorties = sortie_pool.nondominated_sorties;
    while (!frontier.empty()) {
        if (
            output.processed_labels % 256U == 0U &&
            elapsed() >= journey_params.timeout_seconds
        ) {
            timeout = true;
            break;
        }
        const auto label_index = frontier.front();
        frontier.pop_front();
        if (
            label_index >= labels.size() ||
            !labels[label_index].active
        ) {
            continue;
        }
        const auto current = labels[label_index];
        ++output.processed_labels;
        for (const auto& sortie : sorties) {
            if (
                output.extension_checks >=
                journey_params.max_extension_checks
            ) {
                extension_limit = true;
                break;
            }
            ++output.extension_checks;
            if (
                !masks_disjoint(
                    current.task_mask,
                    sortie.task_mask)
            ) {
                ++output.task_overlap_rejected_extensions;
                continue;
            }
            const auto next_mask =
                mask_union(
                    current.task_mask,
                    sortie.task_mask);
            if (!different_branch_feasible(model, next_mask)) {
                ++output.branch_rejected_extensions;
                continue;
            }
            const double departure = std::max(
                current.current_time,
                sortie.release_time);
            if (
                departure >
                sortie.latest_departure + kEpsilon
            ) {
                ++output.time_rejected_extensions;
                continue;
            }
            const double next_time =
                departure + sortie.duration;
            const double old_cut_reward =
                cut_dual_reward(model, current.task_mask);
            const double next_cut_reward =
                cut_dual_reward(model, next_mask);
            const double sortie_objective =
                model.cost_coefficient *
                    sortie.raw_operating_cost +
                model.risk_coefficient * sortie.raw_risk +
                model.completion_coefficient *
                    (
                        sortie.science_weight * departure +
                        sortie.weighted_completion_offset
                    );
            const double next_reduced_cost =
                current.partial_reduced_cost +
                sortie_objective -
                sortie.task_dual_reward -
                (next_cut_reward - old_cut_reward);
            const auto next_task_count =
                static_cast<std::uint16_t>(
                    current.task_count +
                    std::popcount(sortie.task_mask[0]) +
                    std::popcount(sortie.task_mask[1]));

            auto& bucket = dominance_buckets[next_mask];
            bool dominated = false;
            for (const auto existing_index : bucket) {
                if (
                    existing_index >= labels.size() ||
                    !labels[existing_index].active
                ) {
                    continue;
                }
                const auto& existing = labels[existing_index];
                if (
                    existing.current_time <=
                        next_time + kEpsilon &&
                    existing.partial_reduced_cost <=
                        next_reduced_cost + kEpsilon
                ) {
                    dominated = true;
                    break;
                }
            }
            if (dominated) {
                ++output.dominated_labels;
                continue;
            }
            if (
                journey_params
                    .immediate_subset_dominance_enabled
            ) {
                for (
                    std::size_t word = 0U;
                    word < next_mask.size() && !dominated;
                    ++word
                ) {
                    auto remaining = next_mask[word];
                    while (remaining != 0U && !dominated) {
                        const auto bit =
                            std::countr_zero(remaining);
                        auto subset_mask = next_mask;
                        subset_mask[word] &=
                            ~(
                                std::uint64_t{1}
                                << bit
                            );
                        const auto subset_it =
                            dominance_buckets.find(
                                subset_mask);
                        if (
                            subset_it !=
                            dominance_buckets.end()
                        ) {
                            for (
                                const auto existing_index :
                                subset_it->second
                            ) {
                                if (
                                    existing_index >=
                                        labels.size() ||
                                    !labels[existing_index].active
                                ) {
                                    continue;
                                }
                                ++output
                                      .subset_dominance_candidate_checks;
                                const auto& existing =
                                    labels[existing_index];
                                if (
                                    existing.current_time <=
                                        next_time + kEpsilon &&
                                    existing.partial_reduced_cost <=
                                        next_reduced_cost + kEpsilon &&
                                    branch_subset_compatible(
                                        model,
                                        existing.task_mask,
                                        next_mask) &&
                                    cut_subset_compatible(
                                        model,
                                        existing.task_mask,
                                        next_mask)
                                ) {
                                    dominated = true;
                                    break;
                                }
                            }
                        }
                        remaining &= remaining - 1U;
                    }
                }
            }
            if (dominated) {
                ++output.dominated_labels;
                ++output.subset_dominated_labels;
                continue;
            }
            for (const auto existing_index : bucket) {
                if (
                    existing_index >= labels.size() ||
                    !labels[existing_index].active
                ) {
                    continue;
                }
                auto& existing = labels[existing_index];
                if (
                    next_time <=
                        existing.current_time + kEpsilon &&
                    next_reduced_cost <=
                        existing.partial_reduced_cost + kEpsilon
                ) {
                    existing.active = false;
                    ++output.removed_existing_labels;
                }
            }
            if (labels.size() >= journey_params.max_labels) {
                label_limit = true;
                break;
            }
            const auto next_index = labels.size();
            labels.push_back({
                .task_mask = next_mask,
                .current_time = next_time,
                .partial_reduced_cost = next_reduced_cost,
                .task_count = next_task_count,
                .active = true,
            });
            bucket.push_back(next_index);
            frontier.push_back(next_index);
            ++output.generated_labels;
            ++output.accepted_extensions;
            ++output.accepted_labels_by_task_count.at(
                next_task_count);
            output.max_frontier_size = std::max(
                output.max_frontier_size,
                frontier.size());

            if (branch_feasible(model, next_mask)) {
                const double true_reduced_cost =
                    next_reduced_cost - model.fleet_dual;
                output.best_true_reduced_cost = std::min(
                    output.best_true_reduced_cost,
                    true_reduced_cost);
                if (
                    true_reduced_cost <
                    -journey_params.negative_epsilon
                ) {
                    ++output.negative_terminal_label_count;
                    if (
                        !std::isfinite(
                            output.first_negative_wall_time_seconds)
                    ) {
                        output.first_negative_wall_time_seconds =
                            elapsed();
                    }
                    if (
                        journey_params.negative_route_target > 0U &&
                        output.negative_terminal_label_count >=
                            journey_params.negative_route_target &&
                        !std::isfinite(
                            output.negative_target_wall_time_seconds)
                    ) {
                        output.negative_target_wall_time_seconds =
                            elapsed();
                    }
                }
            }
        }
        if (label_limit || extension_limit) {
            break;
        }
    }
    if (
        !label_limit &&
        !extension_limit &&
        !timeout &&
        frontier.empty()
    ) {
        output.search_exhaustive = true;
        output.frontier_empty = true;
        output.status =
            "JOURNEY_FRONTIER_COMPLETE_DIAGNOSTIC_ONLY";
    } else if (timeout) {
        output.status = "JOURNEY_FRONTIER_TIMEOUT";
    } else if (label_limit) {
        output.status = "JOURNEY_FRONTIER_LABEL_LIMIT";
    } else {
        output.status = "JOURNEY_FRONTIER_EXTENSION_LIMIT";
    }
    output.wall_time_seconds = elapsed();
    return output;
}

BidirectionalMidpointProbeOutput
probe_bidirectional_midpoint_journey_meet(
    const Model& model,
    const BidirectionalTaskMeetProbeParams& sortie_params,
    const BidirectionalMidpointProbeParams& midpoint_params
) {
    if (
        midpoint_params.max_forward_labels == 0U ||
        midpoint_params.max_backward_labels == 0U ||
        midpoint_params.max_crossing_labels == 0U ||
        midpoint_params.max_extension_checks == 0U ||
        midpoint_params.max_join_checks == 0U ||
        midpoint_params.max_returned_negative_routes == 0U ||
        !std::isfinite(midpoint_params.split_fraction) ||
        midpoint_params.split_fraction <= 0.0 ||
        midpoint_params.split_fraction >= 1.0 ||
        !std::isfinite(midpoint_params.timeout_seconds) ||
        midpoint_params.timeout_seconds <= 0.0 ||
        !std::isfinite(midpoint_params.negative_epsilon) ||
        midpoint_params.negative_epsilon < 0.0
    ) {
        throw std::invalid_argument(
            "bidirectional midpoint probe parameters are invalid");
    }
    const auto started = std::chrono::steady_clock::now();
    auto elapsed = [&]() {
        return std::chrono::duration<double>(
                   std::chrono::steady_clock::now() - started
               ).count();
    };
    BidirectionalMidpointProbeOutput output;
    output.status = "MIDPOINT_MEET_INCOMPLETE";
    output.split_time =
        model.horizon * midpoint_params.split_fraction;

    auto pool_params = sortie_params;
    pool_params.timeout_seconds = std::min(
        pool_params.timeout_seconds,
        midpoint_params.timeout_seconds);
    auto sortie_pool =
        probe_bidirectional_task_meet_frontier(
            model,
            pool_params);
    output.sortie_pool_size =
        sortie_pool.nondominated_sorties.size();
    if (!sortie_pool.join_exhaustive) {
        output.status = "MIDPOINT_SORTIE_POOL_INCOMPLETE";
        output.wall_time_seconds = elapsed();
        return output;
    }
    const auto& sorties = sortie_pool.nondominated_sorties;

    struct ForwardLabel {
        std::array<std::uint64_t, 2> task_mask{};
        double current_time = 0.0;
        double partial_reduced_cost = 0.0;
        std::size_t parent_label_index =
            std::numeric_limits<std::size_t>::max();
        std::size_t sortie_index =
            std::numeric_limits<std::size_t>::max();
        std::uint16_t task_count = 0;
        bool active = true;
    };
    struct HingeTerm {
        double threshold = 0.0;
        double coefficient = 0.0;
    };
    struct BackwardLabel {
        std::array<std::uint64_t, 2> task_mask{};
        double latest_input_time = 0.0;
        double objective_base = 0.0;
        std::vector<HingeTerm> objective_hinges;
        std::size_t next_label_index =
            std::numeric_limits<std::size_t>::max();
        std::size_t sortie_index =
            std::numeric_limits<std::size_t>::max();
        std::uint16_t task_count = 0;
        bool active = true;
    };
    enum class TerminalWitnessKind {
        Forward,
        Crossing,
        Joined,
    };
    struct TerminalWitness {
        TerminalWitnessKind kind = TerminalWitnessKind::Forward;
        std::size_t prefix_label_index = 0U;
        std::size_t suffix_label_index = 0U;
    };
    struct NegativeWitness {
        std::array<std::uint64_t, 2> task_mask{};
        double reduced_cost = std::numeric_limits<double>::infinity();
        TerminalWitness witness;
        std::size_t version = 0U;
    };
    struct NegativeHeapEntry {
        double reduced_cost = std::numeric_limits<double>::infinity();
        std::array<std::uint64_t, 2> task_mask{};
        std::size_t version = 0U;

        bool operator<(const NegativeHeapEntry& other) const {
            if (reduced_cost != other.reduced_cost) {
                return reduced_cost < other.reduced_cost;
            }
            return task_mask < other.task_mask;
        }
    };

    auto sortie_objective_at =
        [&](const BidirectionalStaticSortie& sortie,
            double departure) {
            return
                model.cost_coefficient *
                    sortie.raw_operating_cost +
                model.risk_coefficient * sortie.raw_risk +
                model.completion_coefficient *
                    (
                        sortie.science_weight * departure +
                        sortie.weighted_completion_offset
                    ) -
                sortie.task_dual_reward;
        };
    auto evaluate_backward =
        [](const BackwardLabel& label, double input_time) {
            double value = label.objective_base;
            for (const auto& term : label.objective_hinges) {
                value +=
                    term.coefficient *
                    std::max(input_time, term.threshold);
            }
            return value;
        };
    auto terminal_value =
        [&](const std::array<std::uint64_t, 2>& mask,
            double objective_without_cut) {
            return
                objective_without_cut -
                cut_dual_reward(model, mask) -
                model.fleet_dual;
        };
    std::unordered_map<
        std::array<std::uint64_t, 2>,
        NegativeWitness,
        InlineTaskMaskHash
    > negative_witnesses;
    negative_witnesses.reserve(
        midpoint_params.max_returned_negative_routes);
    std::priority_queue<NegativeHeapEntry> negative_worst_first;
    std::size_t negative_witness_version = 0U;
    auto push_negative_witness =
        [&](const std::array<std::uint64_t, 2>& mask,
            double value,
            const TerminalWitness& witness) {
            auto push_or_replace =
                [&](auto map_iterator) {
                    const auto version =
                        ++negative_witness_version;
                    NegativeWitness row{
                        .task_mask = mask,
                        .reduced_cost = value,
                        .witness = witness,
                        .version = version,
                    };
                    if (map_iterator == negative_witnesses.end()) {
                        negative_witnesses.emplace(mask, row);
                    } else {
                        map_iterator->second = row;
                    }
                    negative_worst_first.push({
                        .reduced_cost = value,
                        .task_mask = mask,
                        .version = version,
                    });
                };
            auto existing = negative_witnesses.find(mask);
            if (existing != negative_witnesses.end()) {
                if (value < existing->second.reduced_cost) {
                    push_or_replace(existing);
                }
                return;
            }
            if (
                negative_witnesses.size() <
                midpoint_params.max_returned_negative_routes
            ) {
                push_or_replace(existing);
                return;
            }
            while (!negative_worst_first.empty()) {
                const auto& top = negative_worst_first.top();
                const auto live =
                    negative_witnesses.find(top.task_mask);
                if (
                    live != negative_witnesses.end() &&
                    live->second.version == top.version
                ) {
                    break;
                }
                negative_worst_first.pop();
            }
            if (negative_worst_first.empty()) {
                throw std::logic_error(
                    "bidirectional negative witness heap lost "
                    "its live bounded-pool entry");
            }
            const auto worst = negative_worst_first.top();
            if (
                value > worst.reduced_cost ||
                (
                    value == worst.reduced_cost &&
                    !(mask < worst.task_mask)
                )
            ) {
                return;
            }
            negative_worst_first.pop();
            negative_witnesses.erase(worst.task_mask);
            push_or_replace(negative_witnesses.end());
        };
    auto record_terminal =
        [&](const std::array<std::uint64_t, 2>& mask,
            double objective_without_cut,
            const TerminalWitness& witness) {
            if (!branch_feasible(model, mask)) {
                return;
            }
            ++output.terminal_route_count;
            const auto value =
                terminal_value(mask, objective_without_cut);
            output.best_true_reduced_cost = std::min(
                output.best_true_reduced_cost,
                value);
            if (
                value <
                -midpoint_params.negative_epsilon
            ) {
                ++output.negative_terminal_route_count;
                if (
                    !std::isfinite(
                        output.first_negative_wall_time_seconds)
                ) {
                    output.first_negative_wall_time_seconds =
                        elapsed();
                }
                push_negative_witness(mask, value, witness);
            }
        };

    std::vector<ForwardLabel> forward_labels;
    std::vector<ForwardLabel> crossing_labels;
    forward_labels.reserve(std::min<std::size_t>(
        midpoint_params.max_forward_labels,
        250'000U));
    crossing_labels.reserve(std::min<std::size_t>(
        midpoint_params.max_crossing_labels,
        250'000U));
    forward_labels.push_back(ForwardLabel{});
    output.forward_generated_labels = 1U;
    std::deque<std::size_t> forward_frontier{0U};
    output.max_forward_frontier_size = 1U;
    std::unordered_map<
        std::array<std::uint64_t, 2>,
        std::vector<std::size_t>,
        InlineTaskMaskHash
    > forward_buckets;
    std::unordered_map<
        std::array<std::uint64_t, 2>,
        std::vector<std::size_t>,
        InlineTaskMaskHash
    > crossing_buckets;
    forward_buckets[{}].push_back(0U);

    auto accept_forward_like =
        [&](ForwardLabel candidate,
            std::vector<ForwardLabel>* labels,
            auto* buckets,
            std::size_t max_labels,
            std::size_t* dominated_count)
            -> std::optional<std::size_t> {
            auto& bucket = (*buckets)[candidate.task_mask];
            for (const auto existing_index : bucket) {
                if (
                    existing_index >= labels->size() ||
                    !(*labels)[existing_index].active
                ) {
                    continue;
                }
                const auto& existing = (*labels)[existing_index];
                if (
                    existing.current_time <=
                        candidate.current_time + kEpsilon &&
                    existing.partial_reduced_cost <=
                        candidate.partial_reduced_cost + kEpsilon
                ) {
                    ++(*dominated_count);
                    return std::nullopt;
                }
            }
            for (const auto existing_index : bucket) {
                if (
                    existing_index >= labels->size() ||
                    !(*labels)[existing_index].active
                ) {
                    continue;
                }
                auto& existing = (*labels)[existing_index];
                if (
                    candidate.current_time <=
                        existing.current_time + kEpsilon &&
                    candidate.partial_reduced_cost <=
                        existing.partial_reduced_cost + kEpsilon
                ) {
                    existing.active = false;
                }
            }
            if (labels->size() >= max_labels) {
                return std::nullopt;
            }
            const auto index = labels->size();
            labels->push_back(std::move(candidate));
            bucket.push_back(index);
            return index;
        };

    bool forward_limit = false;
    bool crossing_limit = false;
    bool extension_limit = false;
    bool timeout = false;
    while (!forward_frontier.empty()) {
        if (
            output.forward_processed_labels % 256U == 0U &&
            elapsed() >= midpoint_params.timeout_seconds
        ) {
            timeout = true;
            break;
        }
        const auto label_index = forward_frontier.front();
        forward_frontier.pop_front();
        if (
            label_index >= forward_labels.size() ||
            !forward_labels[label_index].active
        ) {
            continue;
        }
        const auto current = forward_labels[label_index];
        ++output.forward_processed_labels;
        for (
            std::size_t sortie_index = 0U;
            sortie_index < sorties.size();
            ++sortie_index
        ) {
            const auto& sortie = sorties[sortie_index];
            if (
                output.extension_checks >=
                midpoint_params.max_extension_checks
            ) {
                extension_limit = true;
                break;
            }
            ++output.extension_checks;
            if (
                !masks_disjoint(
                    current.task_mask,
                    sortie.task_mask)
            ) {
                continue;
            }
            const auto next_mask = mask_union(
                current.task_mask,
                sortie.task_mask);
            if (!different_branch_feasible(model, next_mask)) {
                continue;
            }
            const double departure = std::max(
                current.current_time,
                sortie.release_time);
            if (
                departure >
                sortie.latest_departure + kEpsilon
            ) {
                continue;
            }
            const double next_time =
                departure + sortie.duration;
            const double next_objective =
                current.partial_reduced_cost +
                sortie_objective_at(sortie, departure);
            const auto next_task_count =
                static_cast<std::uint16_t>(
                    current.task_count +
                    std::popcount(sortie.task_mask[0]) +
                    std::popcount(sortie.task_mask[1]));
            ForwardLabel candidate{
                .task_mask = next_mask,
                .current_time = next_time,
                .partial_reduced_cost = next_objective,
                .parent_label_index = label_index,
                .sortie_index = sortie_index,
                .task_count = next_task_count,
                .active = true,
            };
            if (
                next_time <= output.split_time + kEpsilon
            ) {
                const auto accepted = accept_forward_like(
                    candidate,
                    &forward_labels,
                    &forward_buckets,
                    midpoint_params.max_forward_labels,
                    &output.forward_dominated_labels);
                if (accepted.has_value()) {
                    ++output.forward_generated_labels;
                    forward_frontier.push_back(*accepted);
                    output.max_forward_frontier_size = std::max(
                        output.max_forward_frontier_size,
                        forward_frontier.size());
                    record_terminal(
                        next_mask,
                        next_objective,
                        {
                            .kind = TerminalWitnessKind::Forward,
                            .prefix_label_index = *accepted,
                            .suffix_label_index = 0U,
                        });
                } else if (
                    forward_labels.size() >=
                    midpoint_params.max_forward_labels
                ) {
                    forward_limit = true;
                    break;
                }
            }
            if (
                next_time >= output.split_time - kEpsilon
            ) {
                const auto accepted = accept_forward_like(
                    std::move(candidate),
                    &crossing_labels,
                    &crossing_buckets,
                    midpoint_params.max_crossing_labels,
                    &output.crossing_dominated_labels);
                if (accepted.has_value()) {
                    ++output.crossing_generated_labels;
                    record_terminal(
                        next_mask,
                        next_objective,
                        {
                            .kind = TerminalWitnessKind::Crossing,
                            .prefix_label_index = *accepted,
                            .suffix_label_index = 0U,
                        });
                } else if (
                    crossing_labels.size() >=
                    midpoint_params.max_crossing_labels
                ) {
                    crossing_limit = true;
                    break;
                }
            }
        }
        if (
            forward_limit ||
            crossing_limit ||
            extension_limit
        ) {
            break;
        }
    }
    output.forward_exhaustive =
        !forward_limit &&
        !extension_limit &&
        !timeout &&
        forward_frontier.empty();
    output.crossing_exhaustive =
        output.forward_exhaustive && !crossing_limit;

    std::vector<BackwardLabel> backward_labels;
    backward_labels.reserve(std::min<std::size_t>(
        midpoint_params.max_backward_labels,
        250'000U));
    backward_labels.push_back({
        .task_mask = {},
        .latest_input_time = model.horizon,
        .objective_base = 0.0,
        .objective_hinges = {},
        .task_count = 0U,
        .active = true,
    });
    output.backward_generated_labels = 1U;
    std::deque<std::size_t> backward_frontier{0U};
    output.max_backward_frontier_size = 1U;
    std::unordered_map<
        std::array<std::uint64_t, 2>,
        std::vector<std::size_t>,
        InlineTaskMaskHash
    > backward_buckets;
    backward_buckets[{}].push_back(0U);

    auto backward_dominates =
        [&](const BackwardLabel& lhs,
            const BackwardLabel& rhs) {
            if (
                lhs.latest_input_time + kEpsilon <
                rhs.latest_input_time
            ) {
                return false;
            }
            std::vector<double> points{
                output.split_time,
                rhs.latest_input_time,
            };
            for (const auto& term : lhs.objective_hinges) {
                if (
                    term.threshold >= output.split_time &&
                    term.threshold <=
                        rhs.latest_input_time
                ) {
                    points.push_back(term.threshold);
                }
            }
            for (const auto& term : rhs.objective_hinges) {
                if (
                    term.threshold >= output.split_time &&
                    term.threshold <=
                        rhs.latest_input_time
                ) {
                    points.push_back(term.threshold);
                }
            }
            std::ranges::sort(points);
            for (const auto point : points) {
                if (
                    evaluate_backward(lhs, point) >
                    evaluate_backward(rhs, point) + kEpsilon
                ) {
                    return false;
                }
            }
            return true;
        };
    auto combine_hinges =
        [](std::vector<HingeTerm> values) {
            std::ranges::sort(
                values,
                {},
                &HingeTerm::threshold);
            std::vector<HingeTerm> combined;
            for (const auto& term : values) {
                if (std::abs(term.coefficient) <= kEpsilon) {
                    continue;
                }
                if (
                    !combined.empty() &&
                    std::abs(
                        combined.back().threshold -
                        term.threshold
                    ) <= kEpsilon
                ) {
                    combined.back().coefficient +=
                        term.coefficient;
                } else {
                    combined.push_back(term);
                }
            }
            return combined;
        };

    bool backward_limit = timeout || extension_limit;
    while (!backward_frontier.empty() && !backward_limit) {
        if (
            output.backward_processed_labels % 128U == 0U &&
            elapsed() >= midpoint_params.timeout_seconds
        ) {
            timeout = true;
            break;
        }
        const auto label_index = backward_frontier.front();
        backward_frontier.pop_front();
        if (
            label_index >= backward_labels.size() ||
            !backward_labels[label_index].active
        ) {
            continue;
        }
        const auto current = backward_labels[label_index];
        ++output.backward_processed_labels;
        for (
            std::size_t sortie_index = 0U;
            sortie_index < sorties.size();
            ++sortie_index
        ) {
            const auto& sortie = sorties[sortie_index];
            if (
                output.extension_checks >=
                midpoint_params.max_extension_checks
            ) {
                extension_limit = true;
                break;
            }
            ++output.extension_checks;
            if (
                !masks_disjoint(
                    sortie.task_mask,
                    current.task_mask)
            ) {
                continue;
            }
            const auto next_mask = mask_union(
                sortie.task_mask,
                current.task_mask);
            if (!different_branch_feasible(model, next_mask)) {
                continue;
            }
            const double latest_input = std::min(
                sortie.latest_departure,
                current.latest_input_time - sortie.duration);
            if (
                sortie.release_time >
                    latest_input + kEpsilon ||
                latest_input <
                    output.split_time - kEpsilon
            ) {
                continue;
            }
            std::vector<HingeTerm> hinges;
            hinges.reserve(
                current.objective_hinges.size() + 1U);
            const double sortie_hinge_coefficient =
                model.completion_coefficient *
                sortie.science_weight;
            hinges.push_back({
                .threshold = sortie.release_time,
                .coefficient = sortie_hinge_coefficient,
            });
            double current_hinge_weight = 0.0;
            for (const auto& term : current.objective_hinges) {
                current_hinge_weight += term.coefficient;
                hinges.push_back({
                    .threshold = std::max(
                        sortie.release_time,
                        term.threshold - sortie.duration),
                    .coefficient = term.coefficient,
                });
            }
            const double sortie_fixed_objective =
                model.cost_coefficient *
                    sortie.raw_operating_cost +
                model.risk_coefficient * sortie.raw_risk +
                model.completion_coefficient *
                    sortie.weighted_completion_offset -
                sortie.task_dual_reward;
            BackwardLabel candidate{
                .task_mask = next_mask,
                .latest_input_time = latest_input,
                .objective_base =
                    sortie_fixed_objective +
                    current.objective_base +
                    current_hinge_weight * sortie.duration,
                .objective_hinges =
                    combine_hinges(std::move(hinges)),
                .next_label_index = label_index,
                .sortie_index = sortie_index,
                .task_count =
                    static_cast<std::uint16_t>(
                        current.task_count +
                        std::popcount(sortie.task_mask[0]) +
                        std::popcount(sortie.task_mask[1])),
                .active = true,
            };
            auto& bucket = backward_buckets[next_mask];
            bool dominated = false;
            for (const auto existing_index : bucket) {
                if (
                    existing_index >= backward_labels.size() ||
                    !backward_labels[existing_index].active
                ) {
                    continue;
                }
                if (
                    backward_dominates(
                        backward_labels[existing_index],
                        candidate)
                ) {
                    dominated = true;
                    break;
                }
            }
            if (dominated) {
                ++output.backward_dominated_labels;
                continue;
            }
            for (const auto existing_index : bucket) {
                if (
                    existing_index >= backward_labels.size() ||
                    !backward_labels[existing_index].active
                ) {
                    continue;
                }
                if (
                    backward_dominates(
                        candidate,
                        backward_labels[existing_index])
                ) {
                    backward_labels[existing_index].active = false;
                }
            }
            if (
                backward_labels.size() >=
                midpoint_params.max_backward_labels
            ) {
                backward_limit = true;
                break;
            }
            const auto next_index = backward_labels.size();
            backward_labels.push_back(std::move(candidate));
            bucket.push_back(next_index);
            backward_frontier.push_back(next_index);
            ++output.backward_generated_labels;
            output.max_backward_frontier_size = std::max(
                output.max_backward_frontier_size,
                backward_frontier.size());
        }
        if (extension_limit) {
            break;
        }
    }
    output.backward_exhaustive =
        !backward_limit &&
        !extension_limit &&
        !timeout &&
        backward_frontier.empty();
    output.active_forward_labels = static_cast<std::size_t>(
        std::count_if(
            forward_labels.begin(),
            forward_labels.end(),
            [](const ForwardLabel& label) {
                return label.active;
            }));
    output.active_backward_labels = static_cast<std::size_t>(
        std::count_if(
            std::next(backward_labels.begin()),
            backward_labels.end(),
            [](const BackwardLabel& label) {
                return label.active;
            }));
    output.active_crossing_labels = static_cast<std::size_t>(
        std::count_if(
            crossing_labels.begin(),
            crossing_labels.end(),
            [](const ForwardLabel& label) {
                return label.active;
            }));
    output.unindexed_active_join_pairs =
        output.active_crossing_labels *
        output.active_backward_labels;
    std::vector<std::size_t> active_backward_indices;
    active_backward_indices.reserve(
        output.active_backward_labels);
    for (
        std::size_t backward_index = 1U;
        backward_index < backward_labels.size();
        ++backward_index
    ) {
        if (backward_labels[backward_index].active) {
            active_backward_indices.push_back(backward_index);
        }
    }
    std::stable_sort(
        active_backward_indices.begin(),
        active_backward_indices.end(),
        [&backward_labels](
            const std::size_t lhs,
            const std::size_t rhs
        ) {
            return backward_labels[lhs].latest_input_time >
                backward_labels[rhs].latest_input_time;
        });
    for (const auto& crossing : crossing_labels) {
        if (!crossing.active) {
            continue;
        }
        const auto compatible_end = std::partition_point(
            active_backward_indices.begin(),
            active_backward_indices.end(),
            [&backward_labels, &crossing](
                const std::size_t backward_index
            ) {
                return crossing.current_time <=
                    backward_labels[backward_index]
                            .latest_input_time +
                        kEpsilon;
            });
        output.time_index_candidate_join_pairs +=
            static_cast<std::size_t>(
                std::distance(
                    active_backward_indices.begin(),
                    compatible_end));
    }
    output.time_index_pruned_join_pairs =
        output.unindexed_active_join_pairs -
        output.time_index_candidate_join_pairs;

    bool join_limit = false;
    if (
        output.crossing_exhaustive ||
        !crossing_labels.empty()
    ) {
        for (
            std::size_t crossing_index = 0U;
            crossing_index < crossing_labels.size() &&
            !join_limit;
            ++crossing_index
        ) {
            const auto& crossing =
                crossing_labels[crossing_index];
            if (!crossing.active) {
                continue;
            }
            const auto compatible_end = std::partition_point(
                active_backward_indices.begin(),
                active_backward_indices.end(),
                [&backward_labels, &crossing](
                    const std::size_t backward_index
                ) {
                    return crossing.current_time <=
                        backward_labels[backward_index]
                                .latest_input_time +
                            kEpsilon;
                });
            for (
                auto backward_it = active_backward_indices.begin();
                backward_it != compatible_end;
                ++backward_it
            ) {
                const auto backward_index = *backward_it;
                const auto& suffix =
                    backward_labels[backward_index];
                if (
                    output.join_checks >=
                    midpoint_params.max_join_checks
                ) {
                    join_limit = true;
                    break;
                }
                ++output.join_checks;
                if (
                    !masks_disjoint(
                        crossing.task_mask,
                        suffix.task_mask)
                ) {
                    continue;
                }
                ++output.disjoint_join_checks;
                ++output.time_compatible_joins;
                const auto full_mask = mask_union(
                    crossing.task_mask,
                    suffix.task_mask);
                if (!branch_feasible(model, full_mask)) {
                    continue;
                }
                record_terminal(
                    full_mask,
                    crossing.partial_reduced_cost +
                        evaluate_backward(
                            suffix,
                            crossing.current_time),
                    {
                        .kind = TerminalWitnessKind::Joined,
                        .prefix_label_index = crossing_index,
                        .suffix_label_index = backward_index,
                    });
                if (
                    output.join_checks % 4096U == 0U &&
                    elapsed() >= midpoint_params.timeout_seconds
                ) {
                    timeout = true;
                    join_limit = true;
                    break;
                }
            }
        }
    }
    output.join_exhaustive =
        !join_limit &&
        !timeout &&
        output.crossing_exhaustive &&
        output.backward_exhaustive;
    output.search_exhaustive =
        output.forward_exhaustive &&
        output.backward_exhaustive &&
        output.crossing_exhaustive &&
        output.join_exhaustive;
    if (output.search_exhaustive) {
        output.status =
            "MIDPOINT_MEET_COMPLETE_DIAGNOSTIC_ONLY";
    } else if (timeout) {
        output.status = "MIDPOINT_MEET_TIMEOUT";
    } else if (
        forward_limit ||
        backward_limit ||
        crossing_limit
    ) {
        output.status = "MIDPOINT_MEET_LABEL_LIMIT";
    } else if (extension_limit) {
        output.status = "MIDPOINT_MEET_EXTENSION_LIMIT";
    } else {
        output.status = "MIDPOINT_MEET_JOIN_LIMIT";
    }
    auto append_forward_prefix =
        [&](std::vector<SortiePath>* route_sorties,
            std::size_t label_index) {
            std::vector<std::size_t> reverse_sortie_indices;
            std::size_t guard = 0U;
            while (
                label_index <
                forward_labels.size()
            ) {
                const auto& label = forward_labels[label_index];
                if (
                    label.sortie_index ==
                    std::numeric_limits<std::size_t>::max()
                ) {
                    break;
                }
                reverse_sortie_indices.push_back(
                    label.sortie_index);
                label_index = label.parent_label_index;
                if (++guard > forward_labels.size()) {
                    throw std::logic_error(
                        "bidirectional forward witness contains "
                        "a predecessor cycle");
                }
            }
            std::ranges::reverse(reverse_sortie_indices);
            for (const auto sortie_index : reverse_sortie_indices) {
                route_sorties->push_back(
                    sorties.at(sortie_index).skeleton);
            }
        };
    auto reconstruct_witness =
        [&](const NegativeWitness& row) {
            Route route;
            route.reduced_cost = row.reduced_cost;
            if (
                row.witness.kind ==
                TerminalWitnessKind::Forward
            ) {
                append_forward_prefix(
                    &route.sorties,
                    row.witness.prefix_label_index);
            } else {
                const auto& crossing = crossing_labels.at(
                    row.witness.prefix_label_index);
                append_forward_prefix(
                    &route.sorties,
                    crossing.parent_label_index);
                route.sorties.push_back(
                    sorties.at(crossing.sortie_index).skeleton);
            }
            if (
                row.witness.kind ==
                TerminalWitnessKind::Joined
            ) {
                auto suffix_index =
                    row.witness.suffix_label_index;
                std::size_t guard = 0U;
                while (suffix_index != 0U) {
                    const auto& suffix =
                        backward_labels.at(suffix_index);
                    route.sorties.push_back(
                        sorties.at(suffix.sortie_index).skeleton);
                    suffix_index = suffix.next_label_index;
                    if (++guard > backward_labels.size()) {
                        throw std::logic_error(
                            "bidirectional backward witness "
                            "contains a successor cycle");
                    }
                }
            }
            return route;
        };
    std::vector<NegativeWitness> ordered_witnesses;
    ordered_witnesses.reserve(negative_witnesses.size());
    for (const auto& [_, witness] : negative_witnesses) {
        ordered_witnesses.push_back(witness);
    }
    std::ranges::sort(
        ordered_witnesses,
        [](const NegativeWitness& lhs,
           const NegativeWitness& rhs) {
            if (lhs.reduced_cost != rhs.reduced_cost) {
                return lhs.reduced_cost < rhs.reduced_cost;
            }
            return lhs.task_mask < rhs.task_mask;
        });
    output.negative_routes.reserve(ordered_witnesses.size());
    for (const auto& witness : ordered_witnesses) {
        output.negative_routes.push_back(
            reconstruct_witness(witness));
    }
    output.wall_time_seconds = elapsed();
    return output;
}

}  // namespace lunar_spprc
