#include "lunar_spprc/native_pricer.hpp"

#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
#include "lunar_spprc/bidirectional_feasibility.hpp"
#endif

#include <algorithm>
#include <bit>
#include <cmath>
#include <limits>
#include <string>
#include <unordered_map>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace {

py::dict route_payload(const lunar_spprc::Route& route);

double optional_double(const py::dict& payload, const char* key, double fallback) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        return fallback;
    }
    const auto value = payload[name];
    return value.is_none() ? fallback : py::cast<double>(value);
}

std::size_t optional_size_t(
    const py::dict& payload,
    const char* key,
    std::size_t fallback
) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        return fallback;
    }
    const auto value = payload[name];
    return value.is_none() ? fallback : py::cast<std::size_t>(value);
}

bool optional_bool(
    const py::dict& payload,
    const char* key,
    bool fallback
) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        return fallback;
    }
    const auto value = payload[name];
    return value.is_none() ? fallback : py::cast<bool>(value);
}

std::string optional_string(
    const py::dict& payload,
    const char* key,
    std::string fallback
) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        return fallback;
    }
    const auto value = payload[name];
    return value.is_none() ? fallback : py::cast<std::string>(value);
}

std::vector<double> frontier_double_vector(
    const py::dict& payload,
    const char* key,
    std::size_t expected
) {
    const auto values = py::cast<std::vector<double>>(payload[py::str(key)]);
    if (values.size() != expected ||
        std::ranges::any_of(values, [](double value) {
            return !std::isfinite(value);
        })) {
        throw py::value_error(
            std::string("invalid frontier vector: ") + key);
    }
    return values;
}

lunar_spprc::FrontierGatBundle parse_frontier_gat_bundle(
    const py::dict& row
) {
    lunar_spprc::FrontierGatBundle bundle;
    bundle.schema_version = py::cast<std::string>(row["schema_version"]);
    bundle.graph_schema_version =
        py::cast<std::string>(row["graph_schema_version"]);
    bundle.feature_schema_version =
        py::cast<std::string>(row["feature_schema_version"]);
    bundle.bundle_sha256 = optional_string(row, "bundle_sha256", "");
    const auto names = py::cast<py::dict>(row["feature_names"]);
    bundle.node_feature_names =
        py::cast<std::vector<std::string>>(names["node"]);
    bundle.edge_feature_names =
        py::cast<std::vector<std::string>>(names["edge"]);
    bundle.context_feature_names =
        py::cast<std::vector<std::string>>(names["context"]);
    const auto normalization = py::cast<py::dict>(row["normalization"]);
    const auto node = py::cast<py::dict>(normalization["node"]);
    const auto edge = py::cast<py::dict>(normalization["edge"]);
    const auto context = py::cast<py::dict>(normalization["context"]);
    bundle.node_mean = frontier_double_vector(
        node, "mean", lunar_spprc::kFrontierNodeFeatureCount);
    bundle.node_scale = frontier_double_vector(
        node, "scale", lunar_spprc::kFrontierNodeFeatureCount);
    bundle.node_min = frontier_double_vector(
        node, "minimum", lunar_spprc::kFrontierNodeFeatureCount);
    bundle.node_max = frontier_double_vector(
        node, "maximum", lunar_spprc::kFrontierNodeFeatureCount);
    bundle.edge_mean = frontier_double_vector(
        edge, "mean", lunar_spprc::kFrontierEdgeFeatureCount);
    bundle.edge_scale = frontier_double_vector(
        edge, "scale", lunar_spprc::kFrontierEdgeFeatureCount);
    bundle.edge_min = frontier_double_vector(
        edge, "minimum", lunar_spprc::kFrontierEdgeFeatureCount);
    bundle.edge_max = frontier_double_vector(
        edge, "maximum", lunar_spprc::kFrontierEdgeFeatureCount);
    bundle.context_mean = frontier_double_vector(
        context, "mean", lunar_spprc::kFrontierContextFeatureCount);
    bundle.context_scale = frontier_double_vector(
        context, "scale", lunar_spprc::kFrontierContextFeatureCount);
    bundle.context_min = frontier_double_vector(
        context, "minimum", lunar_spprc::kFrontierContextFeatureCount);
    bundle.context_max = frontier_double_vector(
        context, "maximum", lunar_spprc::kFrontierContextFeatureCount);
    const auto calibration = py::cast<py::dict>(row["calibration"]);
    auto parse_calibration = [](const py::dict& source) {
        lunar_spprc::FrontierProbabilityCalibration result;
        const auto kind = py::cast<std::string>(source["kind"]);
        if (kind == "constant") {
            result.constant = true;
            result.probability = py::cast<double>(source["probability"]);
        } else if (kind == "platt") {
            result.a = py::cast<double>(source["a"]);
            result.b = py::cast<double>(source["b"]);
        } else {
            throw py::value_error("unsupported frontier probability calibration");
        }
        return result;
    };
    bundle.benefit_calibration = parse_calibration(
        py::cast<py::dict>(calibration["benefit"]));
    bundle.adverse_calibration = parse_calibration(
        py::cast<py::dict>(calibration["adverse"]));
    bundle.gain_scale = py::cast<double>(calibration["gain_scale"]);
    const auto thresholds = py::cast<py::dict>(row["thresholds"]);
    bundle.minimum_benefit_probability =
        py::cast<double>(thresholds["minimum_benefit_probability"]);
    bundle.maximum_adverse_probability =
        py::cast<double>(thresholds["maximum_adverse_probability"]);
    bundle.minimum_expected_gain =
        py::cast<double>(thresholds["minimum_expected_gain"]);
    bundle.adverse_penalty = py::cast<double>(thresholds["adverse_penalty"]);
    bundle.maximum_disagreement =
        py::cast<double>(thresholds["maximum_disagreement"]);
    bundle.layer_norm_epsilon =
        optional_double(row, "layer_norm_epsilon", 1.0e-5);
    for (const auto item : py::cast<py::list>(row["models"])) {
        const auto model_row = py::cast<py::dict>(item);
        lunar_spprc::FrontierGatSeedModel model;
        model.seed = py::cast<std::uint64_t>(model_row["seed"]);
        const auto tensors = py::cast<py::dict>(model_row["tensors"]);
        for (const auto tensor_item : tensors) {
            const auto name = py::cast<std::string>(tensor_item.first);
            const auto tensor_row = py::cast<py::dict>(tensor_item.second);
            lunar_spprc::FrontierDenseTensor tensor;
            tensor.shape =
                py::cast<std::vector<std::size_t>>(tensor_row["shape"]);
            tensor.values =
                py::cast<std::vector<double>>(tensor_row["values"]);
            model.tensors.emplace(name, std::move(tensor));
        }
        bundle.models.push_back(std::move(model));
    }
    return bundle;
}

lunar_spprc::TemporalGatBundle parse_temporal_gat_bundle(
    const py::dict& row
) {
    lunar_spprc::TemporalGatBundle bundle;
    bundle.schema_version = py::cast<std::string>(row["schema_version"]);
    bundle.graph_schema_version =
        py::cast<std::string>(row["graph_schema_version"]);
    bundle.feature_schema_version =
        py::cast<std::string>(row["feature_schema_version"]);
    bundle.bundle_sha256 = optional_string(row, "bundle_sha256", "");
    bundle.controller_kind = optional_string(
        row, "controller_kind", "temporal_gat");
    const auto names = py::cast<py::dict>(row["feature_names"]);
    bundle.cell_node_feature_names =
        py::cast<std::vector<std::string>>(names["cell_node"]);
    bundle.cell_edge_feature_names =
        py::cast<std::vector<std::string>>(names["cell_edge"]);
    bundle.node_feature_names =
        py::cast<std::vector<std::string>>(names["node"]);
    bundle.edge_feature_names =
        py::cast<std::vector<std::string>>(names["edge"]);
    bundle.counter_feature_names =
        py::cast<std::vector<std::string>>(names["counter"]);
    bundle.context_feature_names =
        py::cast<std::vector<std::string>>(names["context"]);
    const auto normalization = py::cast<py::dict>(row["normalization"]);
    auto group = [&](const char* name, std::size_t width) {
        const auto source = py::cast<py::dict>(normalization[py::str(name)]);
        lunar_spprc::TemporalNormalizationGroup value;
        value.mean = frontier_double_vector(source, "mean", width);
        value.scale = frontier_double_vector(source, "scale", width);
        value.minimum = frontier_double_vector(source, "minimum", width);
        value.maximum = frontier_double_vector(source, "maximum", width);
        return value;
    };
    bundle.cell_node = group(
        "cell_node", lunar_spprc::kFrontierNodeFeatureCount);
    bundle.cell_edge = group(
        "cell_edge", lunar_spprc::kFrontierEdgeFeatureCount);
    bundle.node = group(
        "node", lunar_spprc::kTemporalGatNodeFeatureCount);
    bundle.edge = group(
        "edge", lunar_spprc::kTemporalGatEdgeFeatureCount);
    bundle.counter = group(
        "counter", lunar_spprc::kTemporalGatCounterFeatureCount);
    bundle.context = group(
        "context", lunar_spprc::kFrontierContextFeatureCount);
    auto parse_calibration = [](const py::dict& source) {
        lunar_spprc::FrontierProbabilityCalibration result;
        const auto kind = py::cast<std::string>(source["kind"]);
        if (kind == "constant") {
            result.constant = true;
            result.probability = py::cast<double>(source["probability"]);
        } else if (kind == "platt") {
            result.a = py::cast<double>(source["a"]);
            result.b = py::cast<double>(source["b"]);
        } else {
            throw py::value_error("unsupported Temporal-GAT calibration");
        }
        return result;
    };
    const auto calibration = py::cast<py::dict>(row["calibration"]);
    bundle.benefit_calibration = parse_calibration(
        py::cast<py::dict>(calibration["benefit"]));
    bundle.adverse_calibration = parse_calibration(
        py::cast<py::dict>(calibration["adverse"]));
    bundle.gain_scale = py::cast<double>(calibration["gain_scale"]);
    const auto thresholds = py::cast<py::dict>(row["thresholds"]);
    bundle.minimum_benefit_probability =
        py::cast<double>(thresholds["minimum_benefit_probability"]);
    bundle.maximum_adverse_probability =
        py::cast<double>(thresholds["maximum_adverse_probability"]);
    bundle.minimum_expected_gain =
        py::cast<double>(thresholds["minimum_expected_gain"]);
    bundle.adverse_penalty = py::cast<double>(thresholds["adverse_penalty"]);
    bundle.maximum_disagreement =
        py::cast<double>(thresholds["maximum_disagreement"]);
    bundle.selected_scale = py::cast<std::size_t>(row["selected_scale"]);
    bundle.layer_norm_epsilon =
        optional_double(row, "layer_norm_epsilon", 1.0e-5);
    for (const auto item : py::cast<py::list>(row["models"])) {
        const auto model_row = py::cast<py::dict>(item);
        lunar_spprc::FrontierGatSeedModel model;
        model.seed = py::cast<std::uint64_t>(model_row["seed"]);
        for (const auto tensor_item :
             py::cast<py::dict>(model_row["tensors"])) {
            const auto name = py::cast<std::string>(tensor_item.first);
            const auto tensor_row = py::cast<py::dict>(tensor_item.second);
            lunar_spprc::FrontierDenseTensor tensor;
            tensor.shape =
                py::cast<std::vector<std::size_t>>(tensor_row["shape"]);
            tensor.values =
                py::cast<std::vector<double>>(tensor_row["values"]);
            model.tensors.emplace(name, std::move(tensor));
        }
        bundle.models.push_back(std::move(model));
    }
    return bundle;
}

lunar_spprc::FrontierProbeTelemetry parse_frontier_graph(
    const py::dict& row
) {
    lunar_spprc::FrontierProbeTelemetry graph;
    for (const auto item : py::cast<py::list>(row["node_features"])) {
        const auto values = py::cast<std::vector<double>>(item);
        if (values.size() != lunar_spprc::kFrontierNodeFeatureCount) {
            throw py::value_error("frontier node feature shape mismatch");
        }
        std::array<double, lunar_spprc::kFrontierNodeFeatureCount> feature{};
        std::copy(values.begin(), values.end(), feature.begin());
        graph.node_features.push_back(feature);
    }
    if (graph.node_features.size() != lunar_spprc::kFrontierNodeCount) {
        throw py::value_error("frontier graph must contain 64 nodes");
    }
    for (const auto item : py::cast<py::list>(row["edges"])) {
        const auto edge_row = py::cast<py::dict>(item);
        lunar_spprc::FrontierGraphEdge edge;
        edge.source = py::cast<std::size_t>(edge_row["source"]);
        edge.target = py::cast<std::size_t>(edge_row["target"]);
        const auto values =
            py::cast<std::vector<double>>(edge_row["features"]);
        if (values.size() != lunar_spprc::kFrontierEdgeFeatureCount) {
            throw py::value_error("frontier edge feature shape mismatch");
        }
        std::copy(values.begin(), values.end(), edge.features.begin());
        graph.edges.push_back(edge);
    }
    const auto context =
        py::cast<std::vector<double>>(row["context_features"]);
    if (context.size() != lunar_spprc::kFrontierContextFeatureCount) {
        throw py::value_error("frontier context feature shape mismatch");
    }
    std::copy(
        context.begin(), context.end(), graph.context_features.begin());
    return graph;
}

py::tuple frontier_gat_forward_payload(
    const py::dict& bundle_payload,
    const py::dict& graph_payload,
    std::size_t seed_index
) {
    const auto bundle = parse_frontier_gat_bundle(bundle_payload);
    if (seed_index >= bundle.models.size()) {
        throw py::index_error("frontier GAT seed index out of range");
    }
    const auto graph = parse_frontier_graph(graph_payload);
    const auto output = lunar_spprc::evaluate_frontier_gat_seed(
        bundle.models[seed_index], bundle, graph);
    return py::make_tuple(output[0], output[1], output[2]);
}

lunar_spprc::FrontierProbeSnapshot parse_temporal_cell_graph(
    const py::dict& row
) {
    const auto graph = parse_frontier_graph(row);
    lunar_spprc::FrontierProbeSnapshot snapshot;
    snapshot.graph_built = true;
    snapshot.node_features = graph.node_features;
    snapshot.edges = graph.edges;
    snapshot.context_features = graph.context_features;
    snapshot.frontier_size = graph.frontier_size;
    return snapshot;
}

lunar_spprc::TemporalPortableGraph parse_temporal_portable_graph(
    const py::dict& row
) {
    lunar_spprc::TemporalPortableGraph graph;
    for (const auto item : py::cast<py::list>(row["node_features"])) {
        const auto values = py::cast<std::vector<double>>(item);
        if (values.size() != lunar_spprc::kTemporalGatNodeFeatureCount) {
            throw py::value_error("Temporal-GAT node feature shape mismatch");
        }
        std::array<double, lunar_spprc::kTemporalGatNodeFeatureCount> feature{};
        std::copy(values.begin(), values.end(), feature.begin());
        graph.node_features.push_back(feature);
    }
    for (const auto item : py::cast<py::list>(row["edges"])) {
        const auto edge_row = py::cast<py::dict>(item);
        lunar_spprc::TemporalGraphEdge edge;
        edge.source = py::cast<std::size_t>(edge_row["source"]);
        edge.target = py::cast<std::size_t>(edge_row["target"]);
        const auto values =
            py::cast<std::vector<double>>(edge_row["features"]);
        if (values.size() != lunar_spprc::kTemporalGatEdgeFeatureCount) {
            throw py::value_error("Temporal-GAT edge feature shape mismatch");
        }
        std::copy(values.begin(), values.end(), edge.features.begin());
        graph.edges.push_back(edge);
    }
    if (row.contains("creation_sequence_ids")) {
        graph.creation_sequence_ids =
            py::cast<std::vector<std::uint64_t>>(row["creation_sequence_ids"]);
    } else {
        graph.creation_sequence_ids.assign(
            graph.node_features.size(),
            std::numeric_limits<std::uint64_t>::max());
    }
    if (graph.creation_sequence_ids.size() != graph.node_features.size()) {
        throw py::value_error("Temporal-GAT creation-ID shape mismatch");
    }
    return graph;
}

py::tuple temporal_gat_forward_payload(
    const py::dict& bundle_payload,
    const py::dict& graph_payload,
    std::size_t seed_index
) {
    const auto bundle = parse_temporal_gat_bundle(bundle_payload);
    if (seed_index >= bundle.models.size()) {
        throw py::index_error("Temporal-GAT seed index out of range");
    }
    const auto cell_t0 = parse_temporal_cell_graph(
        py::cast<py::dict>(graph_payload["cell_t0"]));
    const auto cell_tk = parse_temporal_cell_graph(
        py::cast<py::dict>(graph_payload["cell_tk"]));
    const auto temporal_t0 = parse_temporal_portable_graph(
        py::cast<py::dict>(graph_payload["graph_t0"]));
    const auto temporal_tk = parse_temporal_portable_graph(
        py::cast<py::dict>(graph_payload["graph_tk"]));
    const auto counter_values = py::cast<std::vector<double>>(
        graph_payload["counter_features"]);
    const auto context_values = py::cast<std::vector<double>>(
        graph_payload["context_features"]);
    if (counter_values.size() != lunar_spprc::kTemporalGatCounterFeatureCount ||
        context_values.size() != lunar_spprc::kFrontierContextFeatureCount) {
        throw py::value_error("Temporal-GAT counter/context shape mismatch");
    }
    std::array<double, lunar_spprc::kTemporalGatCounterFeatureCount> counters{};
    std::array<double, lunar_spprc::kFrontierContextFeatureCount> context{};
    std::copy(counter_values.begin(), counter_values.end(), counters.begin());
    std::copy(context_values.begin(), context_values.end(), context.begin());
    const auto scale = py::cast<std::size_t>(graph_payload["scale"]);
    const auto output = lunar_spprc::evaluate_temporal_gat_seed(
        bundle.models[seed_index], bundle, cell_t0, cell_tk,
        temporal_t0, temporal_tk, counters, context, scale);
    return py::make_tuple(output[0], output[1], output[2]);
}

py::list temporal_gat_forward_ensemble_payload(
    const py::dict& bundle_payload,
    const py::dict& graph_payload
) {
    const auto bundle = parse_temporal_gat_bundle(bundle_payload);
    const auto cell_t0 = parse_temporal_cell_graph(
        py::cast<py::dict>(graph_payload["cell_t0"]));
    const auto cell_tk = parse_temporal_cell_graph(
        py::cast<py::dict>(graph_payload["cell_tk"]));
    const auto temporal_t0 = parse_temporal_portable_graph(
        py::cast<py::dict>(graph_payload["graph_t0"]));
    const auto temporal_tk = parse_temporal_portable_graph(
        py::cast<py::dict>(graph_payload["graph_tk"]));
    const auto counter_values = py::cast<std::vector<double>>(
        graph_payload["counter_features"]);
    const auto context_values = py::cast<std::vector<double>>(
        graph_payload["context_features"]);
    if (counter_values.size() != lunar_spprc::kTemporalGatCounterFeatureCount ||
        context_values.size() != lunar_spprc::kFrontierContextFeatureCount) {
        throw py::value_error("Temporal-GAT counter/context shape mismatch");
    }
    std::array<double, lunar_spprc::kTemporalGatCounterFeatureCount> counters{};
    std::array<double, lunar_spprc::kFrontierContextFeatureCount> context{};
    std::copy(counter_values.begin(), counter_values.end(), counters.begin());
    std::copy(context_values.begin(), context_values.end(), context.begin());
    const auto scale = py::cast<std::size_t>(graph_payload["scale"]);
    py::list result;
    for (const auto& model : bundle.models) {
        const auto output = lunar_spprc::evaluate_temporal_gat_seed(
            model, bundle, cell_t0, cell_tk, temporal_t0, temporal_tk,
            counters, context, scale);
        result.append(py::make_tuple(output[0], output[1], output[2]));
    }
    return result;
}

py::list temporal_gat_forward_batch_payload(
    const py::dict& bundle_payload,
    const py::list& graph_payloads
) {
    const auto bundle = parse_temporal_gat_bundle(bundle_payload);
    py::list rows;
    for (const auto item : graph_payloads) {
        const auto payload = py::cast<py::dict>(item);
        const auto cell_t0 = parse_temporal_cell_graph(
            py::cast<py::dict>(payload["cell_t0"]));
        const auto cell_tk = parse_temporal_cell_graph(
            py::cast<py::dict>(payload["cell_tk"]));
        const auto temporal_t0 = parse_temporal_portable_graph(
            py::cast<py::dict>(payload["graph_t0"]));
        const auto temporal_tk = parse_temporal_portable_graph(
            py::cast<py::dict>(payload["graph_tk"]));
        const auto counter_values = py::cast<std::vector<double>>(
            payload["counter_features"]);
        const auto context_values = py::cast<std::vector<double>>(
            payload["context_features"]);
        if (counter_values.size() != lunar_spprc::kTemporalGatCounterFeatureCount ||
            context_values.size() != lunar_spprc::kFrontierContextFeatureCount) {
            throw py::value_error("Temporal-GAT counter/context shape mismatch");
        }
        std::array<double, lunar_spprc::kTemporalGatCounterFeatureCount> counters{};
        std::array<double, lunar_spprc::kFrontierContextFeatureCount> context{};
        std::copy(counter_values.begin(), counter_values.end(), counters.begin());
        std::copy(context_values.begin(), context_values.end(), context.begin());
        const auto scale = py::cast<std::size_t>(payload["scale"]);
        const auto started = std::chrono::steady_clock::now();
        py::list outputs;
        std::vector<std::array<double, 3>> raw_outputs;
        raw_outputs.reserve(bundle.models.size());
        for (const auto& model : bundle.models) {
            const auto output = lunar_spprc::evaluate_temporal_gat_seed(
                model, bundle, cell_t0, cell_tk, temporal_t0, temporal_tk,
                counters, context, scale);
            raw_outputs.push_back(output);
            outputs.append(py::make_tuple(output[0], output[1], output[2]));
        }
        const auto decision = lunar_spprc::decide_temporal_gat_outputs(
            bundle, raw_outputs);
        py::dict row;
        row["outputs"] = std::move(outputs);
        row["action"] = decision.continue_qd1
            ? "CONTINUE_QD1" : "MIGRATE_BACK_TO_Q0";
        row["p_benefit"] = decision.p_benefit;
        row["positive_gain"] = decision.positive_gain;
        row["p_adverse"] = decision.p_adverse;
        row["expected_gain"] = decision.expected_gain;
        row["risk_score"] = decision.risk_score;
        row["disagreement"] = decision.disagreement;
        row["inference_ms"] = std::chrono::duration<double, std::milli>(
            std::chrono::steady_clock::now() - started).count();
        rows.append(std::move(row));
    }
    return rows;
}

lunar_spprc::FrontierGatSeedModel parse_portable_seed(
    const py::dict& row
) {
    lunar_spprc::FrontierGatSeedModel model;
    model.seed = py::cast<std::uint64_t>(row["seed"]);
    const auto tensors = py::cast<py::dict>(row["tensors"]);
    for (const auto item : tensors) {
        const auto name = py::cast<std::string>(item.first);
        const auto tensor_row = py::cast<py::dict>(item.second);
        lunar_spprc::FrontierDenseTensor tensor;
        tensor.shape =
            py::cast<std::vector<std::size_t>>(tensor_row["shape"]);
        tensor.values =
            py::cast<std::vector<double>>(tensor_row["values"]);
        model.tensors.emplace(name, std::move(tensor));
    }
    return model;
}

lunar_spprc::CounterfactualPortableBundle parse_counterfactual_bundle(
    const py::dict& row
) {
    lunar_spprc::CounterfactualPortableBundle bundle;
    bundle.schema_version = py::cast<std::string>(row["schema_version"]);
    bundle.layer_norm_epsilon = optional_double(
        row, "layer_norm_epsilon", 1.0e-5);
    const auto normalization = py::cast<py::dict>(row["normalization"]);
    auto group = [&](const char* name, std::size_t size) {
        const auto values = py::cast<py::dict>(normalization[py::str(name)]);
        return std::pair{
            frontier_double_vector(values, "mean", size),
            frontier_double_vector(values, "scale", size),
        };
    };
    auto [node_mean, node_scale] = group(
        "node", lunar_spprc::kCounterfactualPortableNodeFeatureCount);
    auto [edge_mean, edge_scale] = group(
        "edge", lunar_spprc::kCounterfactualPortableEdgeFeatureCount);
    auto [context_mean, context_scale] = group(
        "context", lunar_spprc::kFrontierContextFeatureCount);
    auto [counter_mean, counter_scale] = group(
        "counter", lunar_spprc::kCounterfactualCounterFeatureCount);
    bundle.node_mean = std::move(node_mean);
    bundle.node_scale = std::move(node_scale);
    bundle.edge_mean = std::move(edge_mean);
    bundle.edge_scale = std::move(edge_scale);
    bundle.context_mean = std::move(context_mean);
    bundle.context_scale = std::move(context_scale);
    bundle.counter_mean = std::move(counter_mean);
    bundle.counter_scale = std::move(counter_scale);
    for (const auto item : py::cast<py::list>(row["models"])) {
        bundle.models.push_back(
            parse_portable_seed(py::cast<py::dict>(item)));
    }
    return bundle;
}

lunar_spprc::CounterfactualPortableGraph parse_counterfactual_graph(
    const py::dict& row
) {
    lunar_spprc::CounterfactualPortableGraph graph;
    graph.node_features = py::cast<std::vector<std::vector<double>>>(
        row["node_features"]);
    const auto edge_index = py::cast<std::vector<std::vector<std::size_t>>>(
        row["edge_index"]);
    const auto edge_features =
        py::cast<std::vector<std::vector<double>>>(row["edge_features"]);
    if (edge_index.size() != 2U ||
        edge_index[0].size() != edge_features.size() ||
        edge_index[1].size() != edge_features.size()) {
        throw py::value_error("counterfactual edge-index shape mismatch");
    }
    graph.edges.reserve(edge_features.size());
    for (std::size_t index = 0; index < edge_features.size(); ++index) {
        if (edge_features[index].size() !=
            lunar_spprc::kCounterfactualPortableEdgeFeatureCount) {
            throw py::value_error(
                "counterfactual edge-feature shape mismatch");
        }
        lunar_spprc::FrontierGraphEdge edge;
        edge.source = edge_index[0][index];
        edge.target = edge_index[1][index];
        std::copy(
            edge_features[index].begin(), edge_features[index].end(),
            edge.features.begin());
        graph.edges.push_back(edge);
    }
    const auto context = py::cast<std::vector<double>>(
        row["context_features"]);
    if (context.size() != lunar_spprc::kFrontierContextFeatureCount) {
        throw py::value_error("counterfactual context shape mismatch");
    }
    std::copy(
        context.begin(), context.end(), graph.context_features.begin());
    return graph;
}

py::tuple counterfactual_gat_forward_payload(
    const py::dict& bundle_payload,
    const py::dict& triplet_payload,
    std::size_t seed_index
) {
    const auto bundle = parse_counterfactual_bundle(bundle_payload);
    if (seed_index >= bundle.models.size()) {
        throw py::index_error("counterfactual GAT seed index out of range");
    }
    lunar_spprc::CounterfactualPortableTriplet triplet;
    triplet.base = parse_counterfactual_graph(
        py::cast<py::dict>(triplet_payload["base"]));
    triplet.q0 = parse_counterfactual_graph(
        py::cast<py::dict>(triplet_payload["q0"]));
    triplet.qd1 = parse_counterfactual_graph(
        py::cast<py::dict>(triplet_payload["qd1"]));
    const auto counters = py::cast<std::vector<double>>(
        triplet_payload["counter_deltas"]);
    if (counters.size() !=
        lunar_spprc::kCounterfactualCounterFeatureCount) {
        throw py::value_error("counterfactual counter shape mismatch");
    }
    std::copy(
        counters.begin(), counters.end(), triplet.counter_features.begin());
    const auto output = lunar_spprc::evaluate_counterfactual_gat_seed(
        bundle.models[seed_index], bundle, triplet);
    return py::make_tuple(output[0], output[1], output[2]);
}

lunar_spprc::Model parse_model(const py::dict& payload) {
    lunar_spprc::Model model;
    model.instance_id = py::cast<std::string>(payload["instance_id"]);
    model.structure_hash = py::cast<std::string>(payload["instance_hash"]);
    model.guidance_task_arc_enabled =
        py::cast<bool>(payload["guidance_task_arc_enabled"]);
    model.guidance_label_state_enabled = optional_bool(
        payload, "guidance_label_state_enabled", false);
    if (payload.contains("guidance_label_state_coefficients")) {
        const auto coefficients = py::cast<std::vector<double>>(
            payload["guidance_label_state_coefficients"]);
        if (coefficients.size() != lunar_spprc::kLabelStateFeatureCount) {
            throw py::value_error(
                "guidance_label_state_coefficients must contain exactly " +
                std::to_string(lunar_spprc::kLabelStateFeatureCount) +
                " values");
        }
        std::copy(
            coefficients.begin(),
            coefficients.end(),
            model.guidance_label_state_coefficients.begin());
    } else if (model.guidance_label_state_enabled) {
        throw py::value_error(
            "guidance_label_state_coefficients is required when "
            "guidance_label_state_enabled=true");
    }
    for (const auto item : py::cast<py::list>(payload["tasks"])) {
        const auto row = py::cast<py::dict>(item);
        model.tasks.push_back({
            .id = py::cast<std::string>(row["id"]),
            .index = py::cast<std::size_t>(row["index"]),
            .science_weight = py::cast<double>(row["science_weight"]),
            .demand = py::cast<double>(row["demand"]),
            .service_time = py::cast<double>(row["service_time"]),
            .service_energy = py::cast<double>(row["service_energy"]),
            .service_cost = py::cast<double>(row["service_cost"]),
            .ready_time = py::cast<double>(row["ready_time"]),
            .due_time = py::cast<double>(row["due_time"]),
            .local_shadow_score = py::cast<double>(row["local_shadow_score"]),
            .local_thermal_risk = py::cast<double>(row["local_thermal_risk"]),
            .dual = py::cast<double>(row["dual"]),
            .guidance_priority =
                model.guidance_task_arc_enabled
                    ? py::cast<double>(row["guidance_priority"])
                    : 0.0,
        });
    }
    for (const auto item : py::cast<py::list>(payload["arcs"])) {
        const auto row = py::cast<py::dict>(item);
        model.arcs.push_back({
            .source = py::cast<std::string>(row["source"]),
            .target = py::cast<std::string>(row["target"]),
            .path_type = py::cast<std::string>(row["path_type"]),
            .travel_time = py::cast<double>(row["travel_time"]),
            .energy = py::cast<double>(row["energy"]),
            .risk = py::cast<double>(row["risk"]),
            .distance = py::cast<double>(row["distance"]),
            .shadow = py::cast<double>(row["shadow"]),
            .guidance_priority =
                model.guidance_task_arc_enabled
                    ? py::cast<double>(row["guidance_priority"])
                    : 0.0,
        });
    }
    std::unordered_map<std::string, std::size_t> task_index_by_id;
    for (const auto& task : model.tasks) {
        task_index_by_id.emplace(task.id, task.index);
    }
    for (const auto item : py::cast<py::list>(payload["branch_decisions"])) {
        const auto row = py::cast<py::dict>(item);
        const auto task_a = py::cast<std::string>(row["task_a"]);
        const auto task_b = py::cast<std::string>(row["task_b"]);
        const auto sense = py::cast<std::string>(row["sense"]);
        if (sense != "same_journey" && sense != "different_journey") {
            throw std::invalid_argument("unsupported Ryan-Foster branch sense");
        }
        const auto a_it = task_index_by_id.find(task_a);
        const auto b_it = task_index_by_id.find(task_b);
        model.branch_decisions.push_back({
            .task_a = a_it == task_index_by_id.end() ? 0U : a_it->second,
            .task_b = b_it == task_index_by_id.end() ? 0U : b_it->second,
            .task_a_exists = a_it != task_index_by_id.end(),
            .task_b_exists = b_it != task_index_by_id.end(),
            .sense = sense == "same_journey"
                         ? lunar_spprc::BranchSense::SameJourney
                         : lunar_spprc::BranchSense::DifferentJourney,
        });
    }
    const auto cut_rows = py::cast<py::list>(payload["cuts"]);
    if (cut_rows.size() > 16U) {
        throw std::invalid_argument("native active cut count exceeds 16");
    }
    std::size_t cut_state_bit_offset = 0;
    for (const auto item : cut_rows) {
        const auto row = py::cast<py::dict>(item);
        const auto cut_type = py::cast<std::string>(row["cut_type"]);
        if (cut_type != "subset_row") {
            throw std::invalid_argument("native live-cut v1 supports subset_row only");
        }
        lunar_spprc::CutDefinition cut;
        cut.id = py::cast<std::string>(row["cut_id"]);
        cut.kind = lunar_spprc::CutKind::SubsetRow;
        cut.divisor = py::cast<std::size_t>(row["divisor"]);
        if (cut.divisor != 2U) {
            throw std::invalid_argument("native live-cut v1 supports divisor 2 only");
        }
        cut.dual = py::cast<double>(row["dual"]);
        cut.task_mask.assign((model.tasks.size() + 63U) / 64U, 0U);
        const auto cut_tasks = py::cast<py::list>(row["tasks"]);
        if (cut_tasks.size() != 3U && cut_tasks.size() != 5U) {
            throw std::invalid_argument("native live-cut v1 supports SRI-3 and SRI-5 only");
        }
        cut.state_bit_offset = static_cast<std::uint8_t>(cut_state_bit_offset);
        cut.state_bit_width =
            static_cast<std::uint8_t>(cut_tasks.size() == 3U ? 2U : 3U);
        cut.max_overlap = static_cast<std::uint8_t>(cut_tasks.size());
        cut_state_bit_offset += cut.state_bit_width;
        if (cut_state_bit_offset > 64U) {
            throw std::invalid_argument("native packed cut state exceeds 64 bits");
        }
        for (const auto task_value : cut_tasks) {
            const auto task_id = py::cast<std::string>(task_value);
            const auto found = task_index_by_id.find(task_id);
            if (found == task_index_by_id.end()) {
                throw std::invalid_argument("native cut references an unknown task");
            }
            cut.task_mask[found->second / 64U] |=
                (std::uint64_t{1} << (found->second % 64U));
        }
        std::size_t unique_cut_tasks = 0;
        for (const auto word : cut.task_mask) {
            unique_cut_tasks += std::popcount(word);
        }
        if (unique_cut_tasks != cut_tasks.size()) {
            throw std::invalid_argument("native cut task list contains duplicates");
        }
        model.cuts.push_back(std::move(cut));
    }
    model.max_tasks_per_trip = py::cast<std::size_t>(payload["max_tasks_per_trip"]);
    model.capacity = py::cast<double>(payload["capacity"]);
    model.energy_limit = py::cast<double>(payload["energy_limit"]);
    model.horizon = py::cast<double>(payload["horizon"]);
    model.dock_overhead = py::cast<double>(payload["dock_overhead"]);
    model.recharge_power = py::cast<double>(payload["recharge_power"]);
    model.shadow_limit = py::cast<double>(payload["shadow_limit"]);
    model.cost_coefficient = py::cast<double>(payload["weight_cost"]) /
                             py::cast<double>(payload["reference_cost"]);
    model.risk_coefficient = py::cast<double>(payload["weight_risk"]) /
                             py::cast<double>(payload["reference_risk"]);
    model.completion_coefficient = py::cast<double>(payload["weight_completion"]) /
                                   py::cast<double>(payload["reference_completion"]);
    model.fleet_dual = py::cast<double>(payload["fleet_dual"]);
    return model;
}

#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
std::vector<lunar_spprc::SortiePath> parse_sortie_paths(
    const py::dict& payload,
    const char* key
) {
    const auto name = py::str(key);
    if (!payload.contains(name)) {
        throw py::key_error(
            std::string("missing bidirectional route half: ") + key);
    }
    std::vector<lunar_spprc::SortiePath> result;
    for (const auto item : py::cast<py::list>(payload[name])) {
        const auto row = py::cast<py::dict>(item);
        result.push_back({
            .tasks =
                py::cast<std::vector<std::string>>(row["tasks"]),
            .path_types =
                py::cast<std::vector<std::string>>(row["path_types"]),
        });
    }
    return result;
}

py::dict bidirectional_feasibility_payload(const py::dict& payload) {
    const auto output = lunar_spprc::audit_bidirectional_depot_join(
        parse_model(payload),
        parse_sortie_paths(payload, "forward_sorties"),
        parse_sortie_paths(payload, "backward_sorties"));
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_feasibility_probe.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_depot_meet_max_plus_v1";
    result["status"] = output.status;
    result["feasible"] = output.feasible;
    result["task_sets_disjoint"] = output.task_sets_disjoint;
    result["suffix_boundary_feasible"] =
        output.suffix_boundary_feasible;
    result["branch_feasible"] = output.branch_feasible;
    result["static_objective_finite"] =
        output.static_objective_finite;
    result["can_certify_no_negative"] = false;
    result["certificate_scope"] =
        "DIAGNOSTIC_BIDIRECTIONAL_FEASIBILITY_ONLY";
    result["prefix_end_time"] = output.prefix_end_time;
    result["suffix_latest_input_time"] =
        output.suffix_latest_input_time;
    result["journey_end_time"] = output.journey_end_time;
    result["raw_operating_cost"] = output.raw_operating_cost;
    result["raw_risk"] = output.raw_risk;
    result["raw_weighted_completion"] =
        output.raw_weighted_completion;
    result["task_dual_reward"] = output.task_dual_reward;
    result["cut_dual_reward"] = output.cut_dual_reward;
    result["true_reduced_cost"] = output.true_reduced_cost;
    result["task_count"] = output.task_count;
    result["sortie_count"] = output.sortie_count;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}

py::dict bidirectional_backward_frontier_payload(
    const py::dict& payload
) {
    lunar_spprc::BidirectionalBackwardProbeParams params;
    params.max_partial_states = optional_size_t(
        payload,
        "bidirectional_max_partial_states",
        params.max_partial_states);
    params.max_completed_sorties = optional_size_t(
        payload,
        "bidirectional_max_completed_sorties",
        params.max_completed_sorties);
    params.timeout_seconds = optional_double(
        payload,
        "bidirectional_wall_time_limit_sec",
        params.timeout_seconds);
    const auto output =
        lunar_spprc::probe_bidirectional_backward_frontier(
            parse_model(payload),
            params);
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_backward_frontier_probe.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_depot_meet_max_plus_v1";
    result["scope"] =
        "REVERSE_SORTIE_SEED_FRONTIER_DIAGNOSTIC_ONLY";
    result["status"] = output.status;
    result["search_exhaustive"] = output.search_exhaustive;
    result["frontier_empty"] = output.frontier_empty;
    result["can_certify_no_negative"] = false;
    result["processed_partial_states"] =
        output.processed_partial_states;
    result["generated_partial_states"] =
        output.generated_partial_states;
    result["resource_pruned_partial_states"] =
        output.resource_pruned_partial_states;
    result["duplicate_task_pruned_extensions"] =
        output.duplicate_task_pruned_extensions;
    result["completed_sortie_candidates"] =
        output.completed_sortie_candidates;
    result["feasible_backward_sortie_seeds"] =
        output.feasible_backward_sortie_seeds;
    result["infeasible_completed_sorties"] =
        output.infeasible_completed_sorties;
    result["max_frontier_size"] = output.max_frontier_size;
    result["wall_time_seconds"] = output.wall_time_seconds;
    result["partial_states_by_task_depth"] =
        output.partial_states_by_task_depth;
    result["feasible_sorties_by_task_depth"] =
        output.feasible_sorties_by_task_depth;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}

py::dict bidirectional_task_meet_frontier_payload(
    const py::dict& payload
) {
    lunar_spprc::BidirectionalTaskMeetProbeParams params;
    params.max_partial_states_per_direction = optional_size_t(
        payload,
        "bidirectional_max_partial_states_per_direction",
        params.max_partial_states_per_direction);
    params.max_join_checks = optional_size_t(
        payload,
        "bidirectional_max_join_checks",
        params.max_join_checks);
    params.timeout_seconds = optional_double(
        payload,
        "bidirectional_wall_time_limit_sec",
        params.timeout_seconds);
    const auto output =
        lunar_spprc::probe_bidirectional_task_meet_frontier(
            parse_model(payload),
            params);
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_task_meet_frontier_probe.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_task_meet_max_plus_v1";
    result["scope"] =
        "TASK_LEVEL_SORTIE_MEET_DIAGNOSTIC_ONLY";
    result["status"] = output.status;
    result["forward_generation_exhaustive"] =
        output.forward_generation_exhaustive;
    result["backward_generation_exhaustive"] =
        output.backward_generation_exhaustive;
    result["join_exhaustive"] = output.join_exhaustive;
    result["can_certify_no_negative"] = false;
    result["forward_generated_states"] =
        output.forward_generated_states;
    result["backward_generated_states"] =
        output.backward_generated_states;
    result["forward_resource_pruned_states"] =
        output.forward_resource_pruned_states;
    result["backward_resource_pruned_states"] =
        output.backward_resource_pruned_states;
    result["forward_duplicate_task_pruned_extensions"] =
        output.forward_duplicate_task_pruned_extensions;
    result["backward_duplicate_task_pruned_extensions"] =
        output.backward_duplicate_task_pruned_extensions;
    result["join_pair_checks"] = output.join_pair_checks;
    result["disjoint_join_pairs"] =
        output.disjoint_join_pairs;
    result["resource_compatible_join_pairs"] =
        output.resource_compatible_join_pairs;
    result["feasible_joined_sorties"] =
        output.feasible_joined_sorties;
    result["infeasible_joined_sorties"] =
        output.infeasible_joined_sorties;
    result["distinct_task_set_count"] =
        output.distinct_task_set_count;
    result["task_set_duplicate_sortie_count"] =
        output.task_set_duplicate_sortie_count;
    result["nondominated_sortie_count"] =
        output.nondominated_sortie_count;
    result["dominated_sortie_count"] =
        output.dominated_sortie_count;
    result["max_variants_per_task_set"] =
        output.max_variants_per_task_set;
    result["sortie_dominance_candidate_checks"] =
        output.sortie_dominance_candidate_checks;
    result["wall_time_seconds"] = output.wall_time_seconds;
    result["forward_states_by_task_depth"] =
        output.forward_states_by_task_depth;
    result["backward_states_by_task_depth"] =
        output.backward_states_by_task_depth;
    result["feasible_joined_sorties_by_task_count"] =
        output.feasible_joined_sorties_by_task_count;
    result["nondominated_sorties_by_task_count"] =
        output.nondominated_sorties_by_task_count;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}

py::dict bidirectional_journey_frontier_payload(
    const py::dict& payload
) {
    lunar_spprc::BidirectionalTaskMeetProbeParams sortie_params;
    sortie_params.max_partial_states_per_direction = optional_size_t(
        payload,
        "bidirectional_max_partial_states_per_direction",
        sortie_params.max_partial_states_per_direction);
    sortie_params.max_join_checks = optional_size_t(
        payload,
        "bidirectional_max_join_checks",
        sortie_params.max_join_checks);
    sortie_params.timeout_seconds = optional_double(
        payload,
        "bidirectional_sortie_wall_time_limit_sec",
        sortie_params.timeout_seconds);
    lunar_spprc::BidirectionalJourneyProbeParams journey_params;
    journey_params.max_labels = optional_size_t(
        payload,
        "bidirectional_max_journey_labels",
        journey_params.max_labels);
    journey_params.max_extension_checks = optional_size_t(
        payload,
        "bidirectional_max_journey_extension_checks",
        journey_params.max_extension_checks);
    journey_params.negative_route_target = optional_size_t(
        payload,
        "bidirectional_negative_route_target",
        journey_params.negative_route_target);
    journey_params.negative_epsilon = optional_double(
        payload,
        "negative_eps",
        journey_params.negative_epsilon);
    journey_params.timeout_seconds = optional_double(
        payload,
        "bidirectional_journey_wall_time_limit_sec",
        journey_params.timeout_seconds);
    journey_params.immediate_subset_dominance_enabled =
        optional_bool(
            payload,
            "bidirectional_immediate_subset_dominance_enabled",
            journey_params.immediate_subset_dominance_enabled);
    const auto output =
        lunar_spprc::probe_bidirectional_journey_frontier(
            parse_model(payload),
            sortie_params,
            journey_params);
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_journey_frontier_probe.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_task_meet_journey_label_v1";
    result["scope"] =
        "FROZEN_DUAL_JOURNEY_FRONTIER_DIAGNOSTIC_ONLY";
    result["status"] = output.status;
    result["search_exhaustive"] = output.search_exhaustive;
    result["frontier_empty"] = output.frontier_empty;
    result["can_certify_no_negative"] = false;
    result["sortie_pool_size"] = output.sortie_pool_size;
    result["generated_labels"] = output.generated_labels;
    result["processed_labels"] = output.processed_labels;
    result["dominated_labels"] = output.dominated_labels;
    result["subset_dominance_candidate_checks"] =
        output.subset_dominance_candidate_checks;
    result["subset_dominated_labels"] =
        output.subset_dominated_labels;
    result["removed_existing_labels"] =
        output.removed_existing_labels;
    result["extension_checks"] = output.extension_checks;
    result["task_overlap_rejected_extensions"] =
        output.task_overlap_rejected_extensions;
    result["branch_rejected_extensions"] =
        output.branch_rejected_extensions;
    result["time_rejected_extensions"] =
        output.time_rejected_extensions;
    result["accepted_extensions"] =
        output.accepted_extensions;
    result["negative_terminal_label_count"] =
        output.negative_terminal_label_count;
    result["max_frontier_size"] = output.max_frontier_size;
    result["best_true_reduced_cost"] =
        std::isfinite(output.best_true_reduced_cost)
            ? py::cast(output.best_true_reduced_cost)
            : py::none();
    result["first_negative_wall_time_seconds"] =
        std::isfinite(output.first_negative_wall_time_seconds)
            ? py::cast(output.first_negative_wall_time_seconds)
            : py::none();
    result["negative_target_wall_time_seconds"] =
        std::isfinite(output.negative_target_wall_time_seconds)
            ? py::cast(output.negative_target_wall_time_seconds)
            : py::none();
    result["wall_time_seconds"] = output.wall_time_seconds;
    result["accepted_labels_by_task_count"] =
        output.accepted_labels_by_task_count;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}

py::dict bidirectional_midpoint_meet_payload(
    const py::dict& payload
) {
    lunar_spprc::BidirectionalTaskMeetProbeParams sortie_params;
    sortie_params.max_partial_states_per_direction = optional_size_t(
        payload,
        "bidirectional_max_partial_states_per_direction",
        sortie_params.max_partial_states_per_direction);
    sortie_params.max_join_checks = optional_size_t(
        payload,
        "bidirectional_max_join_checks",
        sortie_params.max_join_checks);
    sortie_params.timeout_seconds = optional_double(
        payload,
        "bidirectional_sortie_wall_time_limit_sec",
        sortie_params.timeout_seconds);
    lunar_spprc::BidirectionalMidpointProbeParams midpoint_params;
    midpoint_params.max_forward_labels = optional_size_t(
        payload,
        "bidirectional_midpoint_max_forward_labels",
        midpoint_params.max_forward_labels);
    midpoint_params.max_backward_labels = optional_size_t(
        payload,
        "bidirectional_midpoint_max_backward_labels",
        midpoint_params.max_backward_labels);
    midpoint_params.max_crossing_labels = optional_size_t(
        payload,
        "bidirectional_midpoint_max_crossing_labels",
        midpoint_params.max_crossing_labels);
    midpoint_params.max_extension_checks = optional_size_t(
        payload,
        "bidirectional_midpoint_max_extension_checks",
        midpoint_params.max_extension_checks);
    midpoint_params.max_join_checks = optional_size_t(
        payload,
        "bidirectional_midpoint_max_join_checks",
        midpoint_params.max_join_checks);
    midpoint_params.max_returned_negative_routes = optional_size_t(
        payload,
        "bidirectional_midpoint_max_returned_negative_routes",
        midpoint_params.max_returned_negative_routes);
    midpoint_params.split_fraction = optional_double(
        payload,
        "bidirectional_midpoint_split_fraction",
        midpoint_params.split_fraction);
    midpoint_params.negative_epsilon = optional_double(
        payload,
        "negative_eps",
        midpoint_params.negative_epsilon);
    midpoint_params.timeout_seconds = optional_double(
        payload,
        "bidirectional_midpoint_wall_time_limit_sec",
        midpoint_params.timeout_seconds);
    const auto output =
        lunar_spprc::probe_bidirectional_midpoint_journey_meet(
            parse_model(payload),
            sortie_params,
            midpoint_params);
    py::dict result;
    result["schema_version"] =
        "lunar_spprc.bidirectional_midpoint_journey_meet.v1";
    result["policy_id"] =
        "p0v4_frozen_dual_depot_midpoint_meet_v1";
    result["scope"] =
        "JOURNEY_LEVEL_FORWARD_BACKWARD_MEET_DIAGNOSTIC_ONLY";
    result["status"] = output.status;
    result["forward_exhaustive"] = output.forward_exhaustive;
    result["backward_exhaustive"] =
        output.backward_exhaustive;
    result["crossing_exhaustive"] =
        output.crossing_exhaustive;
    result["join_exhaustive"] = output.join_exhaustive;
    result["search_exhaustive"] = output.search_exhaustive;
    result["can_certify_no_negative"] = false;
    result["sortie_pool_size"] = output.sortie_pool_size;
    result["forward_generated_labels"] =
        output.forward_generated_labels;
    result["forward_processed_labels"] =
        output.forward_processed_labels;
    result["backward_generated_labels"] =
        output.backward_generated_labels;
    result["backward_processed_labels"] =
        output.backward_processed_labels;
    result["crossing_generated_labels"] =
        output.crossing_generated_labels;
    result["crossing_dominated_labels"] =
        output.crossing_dominated_labels;
    result["forward_dominated_labels"] =
        output.forward_dominated_labels;
    result["backward_dominated_labels"] =
        output.backward_dominated_labels;
    result["active_forward_labels"] =
        output.active_forward_labels;
    result["active_backward_labels"] =
        output.active_backward_labels;
    result["active_crossing_labels"] =
        output.active_crossing_labels;
    result["unindexed_active_join_pairs"] =
        output.unindexed_active_join_pairs;
    result["time_index_candidate_join_pairs"] =
        output.time_index_candidate_join_pairs;
    result["time_index_pruned_join_pairs"] =
        output.time_index_pruned_join_pairs;
    result["extension_checks"] = output.extension_checks;
    result["join_checks"] = output.join_checks;
    result["disjoint_join_checks"] =
        output.disjoint_join_checks;
    result["time_compatible_joins"] =
        output.time_compatible_joins;
    result["terminal_route_count"] =
        output.terminal_route_count;
    result["negative_terminal_route_count"] =
        output.negative_terminal_route_count;
    py::list routes;
    for (const auto& route : output.negative_routes) {
        routes.append(route_payload(route));
    }
    result["routes"] = std::move(routes);
    result["returned_negative_route_count"] =
        output.negative_routes.size();
    result["max_forward_frontier_size"] =
        output.max_forward_frontier_size;
    result["max_backward_frontier_size"] =
        output.max_backward_frontier_size;
    result["split_time"] = output.split_time;
    result["best_true_reduced_cost"] =
        std::isfinite(output.best_true_reduced_cost)
            ? py::cast(output.best_true_reduced_cost)
            : py::none();
    result["first_negative_wall_time_seconds"] =
        std::isfinite(output.first_negative_wall_time_seconds)
            ? py::cast(output.first_negative_wall_time_seconds)
            : py::none();
    result["wall_time_seconds"] = output.wall_time_seconds;
    result["build_info"] = lunar_spprc::build_info();
    return result;
}
#endif

lunar_spprc::SolveParams parse_params(const py::dict& payload) {
    lunar_spprc::SolveParams params;
    params.exact_proof = py::cast<std::string>(payload["mode"]) == "exact_proof";
    params.harvest_target = py::cast<std::size_t>(payload["harvest_target"]);
    params.exact_negative_escape_enabled = optional_bool(
        payload, "exact_negative_escape_enabled", false);
    params.exact_admission_batch_size = optional_size_t(
        payload, "exact_admission_batch_size", params.harvest_target);
    params.exact_raw_negative_pool_size = optional_size_t(
        payload,
        "exact_raw_negative_pool_size",
        params.exact_admission_batch_size * 4U);
    params.exact_negative_escape_policy_id = optional_string(
        payload,
        "exact_negative_escape_policy_id",
        "diverse_raw_4x_then_p0v4_selector_v1");
    params.harvest_max_processed_labels = optional_size_t(
        payload, "harvest_max_processed_labels", 0U);
    params.timeout_seconds = optional_double(payload, "wall_time_limit_sec",
                                             std::numeric_limits<double>::infinity());
    params.max_memory_gb = py::cast<double>(payload["memory_limit_gb"]);
    params.negative_epsilon = py::cast<double>(payload["negative_eps"]);
    params.dominance_epsilon = py::cast<double>(payload["dominance_eps"]);
    params.resource_epsilon = py::cast<double>(payload["resource_eps"]);
    params.graph_cache_entries = py::cast<std::size_t>(payload["graph_cache_entries"]);
    params.completion_bound_enabled = py::cast<bool>(payload["completion_bound_enabled"]);
    params.subset_dominance_enabled = py::cast<bool>(payload["subset_dominance_enabled"]);
    params.proof_queue_potential_trace_enabled =
        optional_bool(payload, "proof_queue_potential_trace_enabled", false);
    params.proof_queue_label_trace_enabled =
        optional_bool(payload, "proof_queue_label_trace_enabled", false);
    params.proof_queue_label_trace_max_rows = optional_size_t(
        payload, "proof_queue_label_trace_max_rows", 50000U);
    const auto label_trace_sampling_mode = optional_string(
        payload, "proof_queue_label_trace_sampling_mode", "prefix_v1");
    if (label_trace_sampling_mode == "prefix_v1") {
        params.proof_queue_label_trace_sampling_mode =
            lunar_spprc::LabelTraceSamplingMode::PrefixV1;
    } else if (label_trace_sampling_mode == "qgr1_stratified_reservoir_v1") {
        params.proof_queue_label_trace_sampling_mode =
            lunar_spprc::LabelTraceSamplingMode::QGR1StratifiedReservoirV1;
    } else {
        throw py::value_error(
            "unsupported proof_queue_label_trace_sampling_mode: " +
            label_trace_sampling_mode);
    }
    params.proof_queue_label_trace_seed = optional_size_t(
        payload, "proof_queue_label_trace_seed", 0U);
    params.proof_queue_preference_cap_per_family = optional_size_t(
        payload, "proof_queue_preference_cap_per_family", 12500U);
    params.proof_queue_surface_reservoir_count = optional_size_t(
        payload, "proof_queue_surface_reservoir_count", 3125U);
    params.proof_queue_surface_labels_per_bucket = optional_size_t(
        payload, "proof_queue_surface_labels_per_bucket", 8U);
    params.proof_queue_witness_route_cap = optional_size_t(
        payload, "proof_queue_witness_route_cap", 512U);
    params.proof_queue_witness_ancestor_cap = optional_size_t(
        payload, "proof_queue_witness_ancestor_cap", 25000U);
    params.proof_queue_guidance_bucket_width =
        optional_double(payload, "proof_queue_guidance_bucket_width", 0.01);
    params.dssr_enabled =
        optional_bool(payload, "dssr_enabled", false);
    params.dssr_policy_version = py::cast<std::string>(
        payload["dssr_policy_version"]);
    params.dssr_negative_batch_target = optional_size_t(
        payload, "dssr_negative_batch_target", 16U);
    params.dssr_pressure_refinement_enabled = optional_bool(
        payload, "dssr_pressure_refinement_enabled", false);
    params.dssr_pressure_max_bucket_size = optional_size_t(
        payload, "dssr_pressure_max_bucket_size", 8192U);
    params.dssr_pressure_max_candidate_checks = optional_size_t(
        payload,
        "dssr_pressure_max_candidate_checks",
        200000000U);
    params.ng_dssr_initial_neighborhood_size = optional_size_t(
        payload, "ng_dssr_initial_neighborhood_size", 10U);
    const auto proof_queue_policy =
        py::cast<std::string>(payload["proof_queue_policy_id"]);
    if (proof_queue_policy == "Q0") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::Q0PartialCost;
    } else if (proof_queue_policy == "QC0") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QC0CachedPartialCost;
    } else if (proof_queue_policy == "QD1") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QD1DeeperFirst;
    } else if (proof_queue_policy == "QB1") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QB1OptimisticCompletion;
    } else if (proof_queue_policy == "QG1") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QG1GuidancePotential;
    } else if (proof_queue_policy == "QG2") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QG2LabelStatePotential;
    } else if (proof_queue_policy == "QGR1") {
        params.proof_queue_policy =
            lunar_spprc::ProofQueuePolicy::QGR1DepthResidualGAT;
    } else {
        throw py::value_error(
            "unsupported proof_queue_policy_id: " + proof_queue_policy);
    }
    const auto frontier_probe_mode = optional_string(
        payload, "proof_queue_frontier_probe_mode", "disabled");
    if (frontier_probe_mode == "disabled") {
        params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::Disabled;
    } else if (frontier_probe_mode == "collect_force_q0") {
        params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::CollectForceQ0;
    } else if (frontier_probe_mode == "force_qd1") {
        params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::ForceQD1;
    } else if (frontier_probe_mode == "learned") {
        params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::Learned;
    } else if (frontier_probe_mode == "collect_trial") {
        params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::CollectTrial;
    } else if (frontier_probe_mode == "force_trial_continue") {
        params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::ForceTrialContinue;
    } else if (frontier_probe_mode == "force_trial_revert") {
        params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::ForceTrialRevert;
    } else if (frontier_probe_mode == "learned_after_trial") {
        params.frontier_probe.mode =
            lunar_spprc::FrontierProbeMode::LearnedAfterTrial;
    } else {
        throw py::value_error(
            "unsupported proof_queue_frontier_probe_mode: " +
            frontier_probe_mode);
    }
    params.frontier_probe.processed_label_boundary = optional_size_t(
        payload, "proof_queue_frontier_probe_boundary", 4096U);
    params.frontier_probe.trial_pop_budget = optional_size_t(
        payload, "proof_queue_frontier_trial_pop_budget", 0U);
    params.frontier_probe.problem_scale = optional_size_t(
        payload, "proof_queue_frontier_problem_scale", 0U);
    params.frontier_probe.pricing_lifecycle = optional_string(
        payload, "proof_queue_frontier_pricing_lifecycle", "unbound");
    params.frontier_probe.require_root_cg = optional_bool(
        payload, "proof_queue_frontier_require_root_cg", true);
    params.frontier_probe.fail_closed_on_ood = optional_bool(
        payload, "proof_queue_frontier_fail_closed_on_ood", true);
    params.frontier_probe.manifest_sha256 = optional_string(
        payload, "proof_queue_frontier_manifest_sha256", "");
    params.frontier_probe.bundle_file_sha256 = optional_string(
        payload, "proof_queue_frontier_bundle_sha256", "");
    if (params.frontier_probe.processed_label_boundary == 0U) {
        throw py::value_error(
            "proof_queue_frontier_probe_boundary must be positive");
    }
    if (payload.contains("proof_queue_frontier_observation_boundaries")) {
        params.frontier_probe.observation_boundaries =
            py::cast<std::vector<std::size_t>>(
                payload["proof_queue_frontier_observation_boundaries"]);
        if (!params.frontier_probe.observation_boundaries.empty() &&
            (params.frontier_probe.observation_boundaries.front() == 0U ||
             !std::ranges::is_sorted(
                 params.frontier_probe.observation_boundaries) ||
             std::ranges::adjacent_find(
                 params.frontier_probe.observation_boundaries) !=
                 params.frontier_probe.observation_boundaries.end() ||
             params.frontier_probe.observation_boundaries.back() >
                 params.frontier_probe.processed_label_boundary)) {
            throw py::value_error(
                "proof_queue_frontier_observation_boundaries must be "
                "strictly increasing, positive, and not exceed the decision boundary");
        }
    }
    if (params.frontier_probe.mode ==
            lunar_spprc::FrontierProbeMode::Disabled &&
        !params.frontier_probe.observation_boundaries.empty()) {
        throw py::value_error(
            "frontier observation boundaries require an enabled frontier probe");
    }
    if (params.frontier_probe.mode !=
            lunar_spprc::FrontierProbeMode::Disabled &&
        params.proof_queue_policy !=
            lunar_spprc::ProofQueuePolicy::Q0PartialCost) {
        throw py::value_error(
            "frontier probe requires literal Q0 initial policy");
    }
    if (payload.contains("proof_queue_frontier_context_features")) {
        const auto values = py::cast<std::vector<double>>(
            payload["proof_queue_frontier_context_features"]);
        if (values.size() != lunar_spprc::kFrontierContextFeatureCount ||
            std::ranges::any_of(values, [](double value) {
                return !std::isfinite(value);
            })) {
            throw py::value_error(
                "proof_queue_frontier_context_features must contain 28 finite values");
        }
        std::copy(
            values.begin(), values.end(),
            params.frontier_probe.context_features.begin());
    }
    if (params.frontier_probe.mode ==
        lunar_spprc::FrontierProbeMode::Learned) {
        if (!payload.contains("proof_queue_frontier_gat_bundle")) {
            throw py::value_error(
                "learned frontier probe requires a portable GAT bundle");
        }
        params.frontier_probe.bundle = parse_frontier_gat_bundle(
            py::cast<py::dict>(payload["proof_queue_frontier_gat_bundle"]));
    }
    if (params.frontier_probe.mode ==
        lunar_spprc::FrontierProbeMode::LearnedAfterTrial) {
        if (!payload.contains("proof_queue_frontier_gat_bundle")) {
            throw py::value_error(
                "learned temporal trial requires a v2 portable bundle");
        }
        params.frontier_probe.temporal_bundle = parse_temporal_gat_bundle(
            py::cast<py::dict>(payload["proof_queue_frontier_gat_bundle"]));
    }
    const auto counterfactual_mode = optional_string(
        payload, "proof_queue_counterfactual_prefix_mode", "disabled");
    if (counterfactual_mode == "disabled") {
        params.counterfactual_prefix.mode =
            lunar_spprc::CounterfactualPrefixMode::Disabled;
    } else if (counterfactual_mode == "counterfactual_q0_prefix") {
        params.counterfactual_prefix.mode =
            lunar_spprc::CounterfactualPrefixMode::Q0Prefix;
    } else if (counterfactual_mode == "counterfactual_qd1_prefix") {
        params.counterfactual_prefix.mode =
            lunar_spprc::CounterfactualPrefixMode::QD1Prefix;
    } else {
        throw py::value_error(
            "unsupported proof_queue_counterfactual_prefix_mode: " +
            counterfactual_mode);
    }
    params.counterfactual_prefix.processed_label_boundary = optional_size_t(
        payload, "proof_queue_counterfactual_prefix_boundary", 4096U);
    params.counterfactual_prefix.maximum_rollout_budget = optional_size_t(
        payload, "proof_queue_counterfactual_max_rollout_budget", 2048U);
    params.counterfactual_prefix.label_sample_cap = optional_size_t(
        payload, "proof_queue_counterfactual_label_sample_cap", 256U);
    params.counterfactual_prefix.sampling_seed = optional_size_t(
        payload, "proof_queue_counterfactual_sampling_seed", 0U);
    params.counterfactual_prefix.telemetry_only = optional_bool(
        payload, "proof_queue_counterfactual_telemetry_only", true);
    params.counterfactual_prefix.public_routes_forbidden = optional_bool(
        payload, "proof_queue_counterfactual_public_routes_forbidden", true);
    params.counterfactual_prefix.certificate_forbidden = optional_bool(
        payload, "proof_queue_counterfactual_certificate_forbidden", true);
    if (payload.contains("proof_queue_counterfactual_rollout_checkpoints")) {
        const auto checkpoints = py::cast<std::vector<std::size_t>>(
            payload["proof_queue_counterfactual_rollout_checkpoints"]);
        if (checkpoints.size() !=
            lunar_spprc::kCounterfactualPrefixCheckpointCount) {
            throw py::value_error(
                "counterfactual rollout checkpoints must contain 3 values");
        }
        std::copy(
            checkpoints.begin(), checkpoints.end(),
            params.counterfactual_prefix.rollout_checkpoints.begin());
    }
    params.counterfactual_prefix.context_features =
        params.frontier_probe.context_features;
    if (params.counterfactual_prefix.mode !=
        lunar_spprc::CounterfactualPrefixMode::Disabled) {
        if (params.frontier_probe.mode !=
                lunar_spprc::FrontierProbeMode::Disabled ||
            params.proof_queue_policy !=
                lunar_spprc::ProofQueuePolicy::Q0PartialCost ||
            !params.exact_proof) {
            throw py::value_error(
                "counterfactual prefix requires exact literal Q0 with V7 probe disabled");
        }
    }
    return params;
}

py::dict route_payload(const lunar_spprc::Route& route) {
    py::list sorties;
    for (const auto& sortie : route.sorties) {
        py::dict row;
        row["tasks"] = sortie.tasks;
        row["path_types"] = sortie.path_types;
        sorties.append(std::move(row));
    }
    py::dict payload;
    payload["reduced_cost"] = route.reduced_cost;
    payload["arc_ids"] = route.arc_ids;
    payload["sorties"] = std::move(sorties);
    return payload;
}

py::dict solve_payload(const py::dict& payload) {
    const auto params = parse_params(payload);
    const auto output = lunar_spprc::solve(parse_model(payload), params);
    py::list routes;
    for (const auto& route : output.routes) {
        routes.append(route_payload(route));
    }
    py::dict telemetry;
    telemetry["processed_labels"] = output.telemetry.processed_labels;
    telemetry["extended_labels"] = output.telemetry.extended_labels;
    telemetry["dominated_labels"] = output.telemetry.dominated_labels;
    telemetry["dominance_candidate_checks"] = output.telemetry.dominance_candidate_checks;
    telemetry["max_visited_bucket_size"] = output.telemetry.max_visited_bucket_size;
    telemetry["solution_count"] = output.telemetry.solution_count;
    telemetry["negative_escape_enabled"] =
        output.telemetry.negative_escape_enabled;
    telemetry["negative_escape_triggered"] =
        output.telemetry.negative_escape_triggered;
    telemetry["exact_admission_batch_size"] =
        output.telemetry.exact_admission_batch_size;
    telemetry["exact_raw_negative_pool_size"] =
        output.telemetry.exact_raw_negative_pool_size;
    telemetry["raw_unique_negative_count"] =
        output.telemetry.raw_unique_negative_count;
    telemetry["negative_escape_policy_id"] =
        output.telemetry.negative_escape_policy_id;
    telemetry["negative_escape_termination_reason"] =
        output.telemetry.negative_escape_termination_reason;
    telemetry["memory_pressure_triggered"] = output.telemetry.memory_pressure_triggered;
    telemetry["graph_cache_hit"] = output.telemetry.graph_cache_hit;
    telemetry["graph_cache_size"] = output.telemetry.graph_cache_size;
    telemetry["graph_cache_build_count"] = output.telemetry.graph_cache_build_count;
    telemetry["graph_cache_hit_count"] = output.telemetry.graph_cache_hit_count;
    telemetry["completion_bound_evaluated_labels"] =
        output.telemetry.completion_bound_evaluated_labels;
    telemetry["completion_bound_pruned_labels"] =
        output.telemetry.completion_bound_pruned_labels;
    telemetry["completion_bound_enabled"] =
        output.telemetry.completion_bound_evaluated_labels > 0;
    telemetry["subset_dominance_key_lookups"] =
        output.telemetry.subset_dominance_key_lookups;
    telemetry["subset_dominance_nonempty_buckets"] =
        output.telemetry.subset_dominance_nonempty_buckets;
    telemetry["subset_dominance_summary_skipped_buckets"] =
        output.telemetry.subset_dominance_summary_skipped_buckets;
    telemetry["subset_dominance_candidate_checks"] =
        output.telemetry.subset_dominance_candidate_checks;
    telemetry["subset_dominance_rejected_labels"] =
        output.telemetry.subset_dominance_rejected_labels;
    telemetry["extension_wall_time_seconds"] = output.telemetry.extension_wall_time_seconds;
    telemetry["dominance_wall_time_seconds"] = output.telemetry.dominance_wall_time_seconds;
    telemetry["wall_time_seconds"] = output.telemetry.wall_time_seconds;
    const auto& frontier = output.telemetry.frontier_probe;
    py::dict frontier_payload;
    frontier_payload["schema_version"] =
        "lunar_spprc.frontier_probe_telemetry.v2";
    frontier_payload["enabled"] = frontier.enabled;
    frontier_payload["reached"] = frontier.reached;
    frontier_payload["graph_built"] = frontier.graph_built;
    frontier_payload["model_called"] = frontier.model_called;
    frontier_payload["switched_to_qd1"] = frontier.switched_to_qd1;
    frontier_payload["trial_started"] = frontier.trial_started;
    frontier_payload["trial_completed"] = frontier.trial_completed;
    frontier_payload["migrated_back_to_q0"] =
        frontier.migrated_back_to_q0;
    frontier_payload["inference_ood"] = frontier.inference_ood;
    frontier_payload["fail_closed"] = frontier.fail_closed;
    frontier_payload["mode"] = frontier.mode;
    frontier_payload["action"] = frontier.action;
    frontier_payload["decision_reason"] = frontier.decision_reason;
    // Keep the authorization context next to the probe outcome so E2E audits
    // can prove that no learned action escaped the scale30/50 root-CG scope.
    frontier_payload["problem_scale"] = params.frontier_probe.problem_scale;
    frontier_payload["pricing_lifecycle"] =
        params.frontier_probe.pricing_lifecycle;
    frontier_payload["require_root_cg"] =
        params.frontier_probe.require_root_cg;
    frontier_payload["graph_hash"] = frontier.graph_hash;
    frontier_payload["boundary"] = frontier.boundary;
    frontier_payload["trial_pop_budget"] = frontier.trial_pop_budget;
    frontier_payload["trial_pops"] = frontier.trial_pops;
    frontier_payload["frontier_size"] = frontier.frontier_size;
    frontier_payload["nonempty_node_count"] = frontier.nonempty_node_count;
    frontier_payload["edge_count"] = frontier.edge_count;
    frontier_payload["frontier_before_migration"] =
        frontier.frontier_before_migration;
    frontier_payload["drained_count"] = frontier.drained_count;
    frontier_payload["migrated_count"] = frontier.migrated_count;
    frontier_payload["duplicate_count"] = frontier.duplicate_count;
    frontier_payload["creation_hash_before"] = frontier.creation_hash_before;
    frontier_payload["creation_hash_after"] = frontier.creation_hash_after;
    frontier_payload["reverse_frontier_before_migration"] =
        frontier.reverse_frontier_before_migration;
    frontier_payload["reverse_staged_count"] =
        frontier.reverse_staged_count;
    frontier_payload["reverse_migrated_count"] =
        frontier.reverse_migrated_count;
    frontier_payload["reverse_duplicate_count"] =
        frontier.reverse_duplicate_count;
    frontier_payload["reverse_creation_hash_before"] =
        frontier.reverse_creation_hash_before;
    frontier_payload["reverse_creation_hash_after"] =
        frontier.reverse_creation_hash_after;
    frontier_payload["q0_post_probe_pops"] = frontier.q0_post_probe_pops;
    frontier_payload["qd1_post_probe_pops"] = frontier.qd1_post_probe_pops;
    frontier_payload["graph_build_wall_seconds"] =
        frontier.graph_build_wall_seconds;
    frontier_payload["temporal_graph_build_wall_seconds"] =
        frontier.temporal_graph_build_wall_seconds;
    frontier_payload["inference_wall_seconds"] =
        frontier.inference_wall_seconds;
    frontier_payload["migration_wall_seconds"] =
        frontier.migration_wall_seconds;
    frontier_payload["reverse_migration_wall_seconds"] =
        frontier.reverse_migration_wall_seconds;
    frontier_payload["trial_wall_seconds"] = frontier.trial_wall_seconds;
    frontier_payload["p_benefit"] = frontier.p_benefit;
    frontier_payload["positive_gain"] = frontier.positive_gain;
    frontier_payload["p_adverse"] = frontier.p_adverse;
    frontier_payload["expected_gain"] = frontier.expected_gain;
    frontier_payload["risk_score"] = frontier.risk_score;
    frontier_payload["disagreement"] = frontier.disagreement;
    frontier_payload["ood_reason"] = frontier.ood_reason;
    py::list seed_outputs;
    for (const auto& output_row : frontier.seed_outputs) {
        seed_outputs.append(py::make_tuple(
            output_row[0], output_row[1], output_row[2]));
    }
    frontier_payload["seed_outputs"] = std::move(seed_outputs);
    py::list node_features;
    for (const auto& feature_row : frontier.node_features) {
        py::list row;
        for (const double value : feature_row) {
            row.append(value);
        }
        node_features.append(std::move(row));
    }
    frontier_payload["node_features"] = std::move(node_features);
    py::list edge_rows;
    for (const auto& edge : frontier.edges) {
        py::dict row;
        row["source"] = edge.source;
        row["target"] = edge.target;
        py::list features;
        for (const double value : edge.features) {
            features.append(value);
        }
        row["features"] = std::move(features);
        edge_rows.append(std::move(row));
    }
    frontier_payload["edges"] = std::move(edge_rows);
    py::list context_features;
    for (const double value : frontier.context_features) {
        context_features.append(value);
    }
    frontier_payload["context_features"] = std::move(context_features);
    frontier_payload["observation_boundaries"] =
        frontier.observation_boundaries;
    py::list snapshot_rows;
    for (const auto& snapshot : frontier.snapshots) {
        py::dict snapshot_row;
        snapshot_row["reached"] = snapshot.reached;
        snapshot_row["graph_built"] = snapshot.graph_built;
        snapshot_row["boundary"] = snapshot.boundary;
        snapshot_row["processed_labels"] = snapshot.processed_labels;
        snapshot_row["extended_labels"] = snapshot.extended_labels;
        snapshot_row["dominated_labels"] = snapshot.dominated_labels;
        snapshot_row["dominance_candidate_checks"] =
            snapshot.dominance_candidate_checks;
        snapshot_row["subset_dominance_candidate_checks"] =
            snapshot.subset_dominance_candidate_checks;
        snapshot_row["subset_dominance_rejected_labels"] =
            snapshot.subset_dominance_rejected_labels;
        snapshot_row["max_visited_bucket_size"] =
            snapshot.max_visited_bucket_size;
        snapshot_row["negative_label_event_count"] =
            snapshot.negative_label_event_count;
        snapshot_row["best_true_reduced_cost"] =
            std::isfinite(snapshot.best_true_reduced_cost)
                ? py::cast(snapshot.best_true_reduced_cost)
                : py::none();
        snapshot_row["graph_hash"] = snapshot.graph_hash;
        snapshot_row["frontier_size"] = snapshot.frontier_size;
        snapshot_row["nonempty_node_count"] =
            snapshot.nonempty_node_count;
        snapshot_row["edge_count"] = snapshot.edge_count;
        snapshot_row["graph_build_wall_seconds"] =
            snapshot.graph_build_wall_seconds;
        py::list snapshot_nodes;
        for (const auto& feature_row : snapshot.node_features) {
            py::list row;
            for (const double value : feature_row) {
                row.append(value);
            }
            snapshot_nodes.append(std::move(row));
        }
        snapshot_row["node_features"] = std::move(snapshot_nodes);
        py::list snapshot_edges;
        for (const auto& edge : snapshot.edges) {
            py::dict row;
            row["source"] = edge.source;
            row["target"] = edge.target;
            py::list features;
            for (const double value : edge.features) {
                features.append(value);
            }
            row["features"] = std::move(features);
            snapshot_edges.append(std::move(row));
        }
        snapshot_row["edges"] = std::move(snapshot_edges);
        py::list snapshot_context;
        for (const double value : snapshot.context_features) {
            snapshot_context.append(value);
        }
        snapshot_row["context_features"] = std::move(snapshot_context);
        snapshot_rows.append(std::move(snapshot_row));
    }
    frontier_payload["snapshots"] = std::move(snapshot_rows);
    const auto counterfactual_graph_payload = [](
        const lunar_spprc::CounterfactualFrontierGraph& graph) {
        py::dict row;
        row["schema_version"] = graph.schema_version;
        row["graph_hash"] = graph.graph_hash;
        row["frontier_size"] = graph.frontier_size;
        row["sampled_label_count"] = graph.sampled_label_count;
        py::dict coverage;
        coverage["terminal"] = graph.terminal_family_count;
        coverage["q0_top"] = graph.q0_family_count;
        coverage["qd1_top"] = graph.qd1_family_count;
        coverage["deepest"] = graph.deepest_family_count;
        coverage["depth_rc"] = graph.depth_rc_family_count;
        coverage["bottom_k"] = graph.bottom_k_family_count;
        row["sample_family_new_counts"] = std::move(coverage);
        py::list nodes;
        for (const auto& node : graph.label_nodes) {
            py::dict node_row;
            node_row["creation_sequence_id"] = node.creation_sequence_id;
            node_row["parent_creation_sequence_id"] =
                node.parent_creation_sequence_id;
            node_row["last_task_index"] = node.last_task_index;
            node_row["depth_rc_cell"] = node.depth_rc_cell;
            node_row["dominance_surface_hash"] =
                node.dominance_surface_hash;
            py::list features;
            for (const auto value : node.features) {
                features.append(value);
            }
            node_row["features"] = std::move(features);
            nodes.append(std::move(node_row));
        }
        row["label_nodes"] = std::move(nodes);
        py::list edges;
        for (const auto& edge : graph.label_edges) {
            py::dict edge_row;
            edge_row["source"] = edge.source;
            edge_row["target"] = edge.target;
            py::list features;
            for (const auto value : edge.features) {
                features.append(value);
            }
            edge_row["features"] = std::move(features);
            edges.append(std::move(edge_row));
        }
        row["label_edges"] = std::move(edges);
        py::list context;
        for (const auto value : graph.context_features) {
            context.append(value);
        }
        row["context_features"] = std::move(context);
        row["build_wall_seconds"] = graph.build_wall_seconds;
        return row;
    };
    const auto frontier_snapshot_payload = [](
        const lunar_spprc::FrontierProbeSnapshot& snapshot) {
        py::dict row;
        row["reached"] = snapshot.reached;
        row["graph_built"] = snapshot.graph_built;
        row["boundary"] = snapshot.boundary;
        row["processed_labels"] = snapshot.processed_labels;
        row["extended_labels"] = snapshot.extended_labels;
        row["dominated_labels"] = snapshot.dominated_labels;
        row["dominance_candidate_checks"] =
            snapshot.dominance_candidate_checks;
        row["subset_dominance_candidate_checks"] =
            snapshot.subset_dominance_candidate_checks;
        row["subset_dominance_rejected_labels"] =
            snapshot.subset_dominance_rejected_labels;
        row["max_visited_bucket_size"] = snapshot.max_visited_bucket_size;
        row["negative_label_event_count"] =
            snapshot.negative_label_event_count;
        row["best_true_reduced_cost"] =
            std::isfinite(snapshot.best_true_reduced_cost)
                ? py::cast(snapshot.best_true_reduced_cost)
                : py::none();
        row["graph_hash"] = snapshot.graph_hash;
        row["frontier_size"] = snapshot.frontier_size;
        row["nonempty_node_count"] = snapshot.nonempty_node_count;
        row["edge_count"] = snapshot.edge_count;
        row["graph_build_wall_seconds"] =
            snapshot.graph_build_wall_seconds;
        py::list nodes;
        for (const auto& values : snapshot.node_features) {
            py::list features;
            for (const double value : values) {
                features.append(value);
            }
            nodes.append(std::move(features));
        }
        row["node_features"] = std::move(nodes);
        py::list edges;
        for (const auto& edge : snapshot.edges) {
            py::dict edge_row;
            edge_row["source"] = edge.source;
            edge_row["target"] = edge.target;
            py::list features;
            for (const double value : edge.features) {
                features.append(value);
            }
            edge_row["features"] = std::move(features);
            edges.append(std::move(edge_row));
        }
        row["edges"] = std::move(edges);
        row["context_features"] = snapshot.context_features;
        return row;
    };
    frontier_payload["trial_start_snapshot"] =
        frontier_snapshot_payload(frontier.trial_start_snapshot);
    frontier_payload["trial_end_snapshot"] =
        frontier_snapshot_payload(frontier.trial_end_snapshot);
    frontier_payload["trial_start_label_graph"] =
        counterfactual_graph_payload(frontier.trial_start_label_graph);
    frontier_payload["trial_end_label_graph"] =
        counterfactual_graph_payload(frontier.trial_end_label_graph);
    const auto temporal_graph_payload = [](
        const lunar_spprc::TemporalPortableGraph& graph) {
        py::dict row;
        row["graph_hash"] = graph.graph_hash;
        py::list nodes;
        for (const auto& values : graph.node_features) {
            py::list features;
            for (const auto value : values) {
                features.append(value);
            }
            nodes.append(std::move(features));
        }
        row["node_features"] = std::move(nodes);
        py::list edges;
        for (const auto& edge : graph.edges) {
            py::dict edge_row;
            edge_row["source"] = edge.source;
            edge_row["target"] = edge.target;
            py::list features;
            for (const auto value : edge.features) {
                features.append(value);
            }
            edge_row["features"] = std::move(features);
            edges.append(std::move(edge_row));
        }
        row["edges"] = std::move(edges);
        row["creation_sequence_ids"] = graph.creation_sequence_ids;
        row["context_features"] = graph.context_features;
        return row;
    };
    frontier_payload["trial_start_temporal_graph"] =
        temporal_graph_payload(frontier.trial_start_temporal_graph);
    frontier_payload["trial_end_temporal_graph"] =
        temporal_graph_payload(frontier.trial_end_temporal_graph);
    frontier_payload["temporal_surviving_label_count"] =
        frontier.temporal_surviving_label_count;
    frontier_payload["temporal_new_label_count"] =
        frontier.temporal_new_label_count;
    frontier_payload["temporal_extended_label_delta"] =
        frontier.temporal_extended_label_delta;
    frontier_payload["temporal_dominated_label_delta"] =
        frontier.temporal_dominated_label_delta;
    frontier_payload["temporal_survival_fraction"] =
        frontier.temporal_survival_fraction;
    frontier_payload["temporal_frontier_churn"] =
        frontier.temporal_frontier_churn;
    frontier_payload["temporal_cell_edge_count"] =
        frontier.temporal_cell_edge_count;
    frontier_payload["temporal_label_edge_count"] =
        frontier.temporal_label_edge_count;
    py::list temporal_edges;
    for (const auto& edge : frontier.temporal_edges) {
        temporal_edges.append(edge);
    }
    frontier_payload["temporal_edges"] = std::move(temporal_edges);
    frontier_payload["temporal_edge_hash"] = frontier.temporal_edge_hash;
    frontier_payload["temporal_counter_features"] =
        frontier.temporal_counter_features;
    frontier_payload["temporal_counter_hash"] =
        frontier.temporal_counter_hash;
    telemetry["proof_queue_frontier_probe"] = std::move(frontier_payload);
    const auto& counterfactual = output.telemetry.counterfactual_prefix;
    py::dict counterfactual_payload;
    counterfactual_payload["schema_version"] =
        "lunar_ice_bpc.p0v5_counterfactual_prefix_probe.v1";
    counterfactual_payload["enabled"] = counterfactual.enabled;
    counterfactual_payload["mode"] = counterfactual.mode;
    counterfactual_payload["reached_boundary"] =
        counterfactual.reached_boundary;
    counterfactual_payload["complete"] = counterfactual.complete;
    counterfactual_payload["truncated_diagnostic"] =
        counterfactual.truncated_diagnostic;
    counterfactual_payload["exact"] = counterfactual.exact;
    counterfactual_payload["public_routes_forbidden"] =
        counterfactual.public_routes_forbidden;
    counterfactual_payload["certificate_forbidden"] =
        counterfactual.certificate_forbidden;
    counterfactual_payload["routes_suppressed"] =
        counterfactual.routes_suppressed;
    counterfactual_payload["certificate_suppressed"] =
        counterfactual.certificate_suppressed;
    counterfactual_payload["switched_to_qd1"] =
        counterfactual.switched_to_qd1;
    counterfactual_payload["stop_reason"] = counterfactual.stop_reason;
    counterfactual_payload["processed_label_boundary"] =
        counterfactual.processed_label_boundary;
    counterfactual_payload["rollout_checkpoints"] =
        counterfactual.rollout_checkpoints;
    counterfactual_payload["maximum_rollout_budget"] =
        counterfactual.maximum_rollout_budget;
    counterfactual_payload["base_graph_hash"] =
        counterfactual.base_graph_hash;
    counterfactual_payload["base_processed_labels"] =
        counterfactual.base_processed_labels;
    counterfactual_payload["base_extended_labels"] =
        counterfactual.base_extended_labels;
    counterfactual_payload["base_dominated_labels"] =
        counterfactual.base_dominated_labels;
    counterfactual_payload["base_dominance_candidate_checks"] =
        counterfactual.base_dominance_candidate_checks;
    counterfactual_payload["base_subset_dominance_candidate_checks"] =
        counterfactual.base_subset_dominance_candidate_checks;
    counterfactual_payload["base_subset_dominance_rejected_labels"] =
        counterfactual.base_subset_dominance_rejected_labels;
    counterfactual_payload["base_max_visited_bucket_size"] =
        counterfactual.base_max_visited_bucket_size;
    counterfactual_payload["base_negative_label_event_count"] =
        counterfactual.base_negative_label_event_count;
    counterfactual_payload["base_best_true_reduced_cost"] =
        std::isfinite(counterfactual.base_best_true_reduced_cost)
            ? py::cast(counterfactual.base_best_true_reduced_cost)
            : py::none();
    counterfactual_payload["base_request_elapsed_wall_seconds"] =
        counterfactual.base_request_elapsed_wall_seconds;
    counterfactual_payload["base_graph_build_wall_seconds"] =
        counterfactual.base_graph_build_wall_seconds;
    counterfactual_payload["migration_wall_seconds"] =
        counterfactual.migration_wall_seconds;
    counterfactual_payload["request_elapsed_wall_seconds"] =
        counterfactual.request_elapsed_wall_seconds;
    counterfactual_payload["base_graph"] =
        counterfactual_graph_payload(counterfactual.base_graph);
    py::list endpoint_rows;
    for (const auto& endpoint : counterfactual.endpoints) {
        py::dict endpoint_row;
        endpoint_row["rollout_budget"] = endpoint.rollout_budget;
        endpoint_row["processed_labels"] = endpoint.processed_labels;
        endpoint_row["extended_labels"] = endpoint.extended_labels;
        endpoint_row["dominated_labels"] = endpoint.dominated_labels;
        endpoint_row["dominance_candidate_checks"] =
            endpoint.dominance_candidate_checks;
        endpoint_row["subset_dominance_candidate_checks"] =
            endpoint.subset_dominance_candidate_checks;
        endpoint_row["subset_dominance_rejected_labels"] =
            endpoint.subset_dominance_rejected_labels;
        endpoint_row["frontier_size"] = endpoint.frontier_size;
        endpoint_row["max_visited_bucket_size"] =
            endpoint.max_visited_bucket_size;
        endpoint_row["negative_label_event_count"] =
            endpoint.negative_label_event_count;
        endpoint_row["best_true_reduced_cost"] =
            std::isfinite(endpoint.best_true_reduced_cost)
                ? py::cast(endpoint.best_true_reduced_cost)
                : py::none();
        endpoint_row["base_label_survival_count"] =
            endpoint.base_label_survival_count;
        endpoint_row["new_label_count"] = endpoint.new_label_count;
        endpoint_row["frontier_churn"] = endpoint.frontier_churn;
        endpoint_row["request_elapsed_wall_seconds"] =
            endpoint.request_elapsed_wall_seconds;
        endpoint_row["rollout_elapsed_wall_seconds"] =
            endpoint.rollout_elapsed_wall_seconds;
        endpoint_row["graph_build_wall_seconds"] =
            endpoint.graph_build_wall_seconds;
        endpoint_row["graph"] =
            counterfactual_graph_payload(endpoint.graph);
        endpoint_rows.append(std::move(endpoint_row));
    }
    counterfactual_payload["endpoints"] = std::move(endpoint_rows);
    telemetry["proof_queue_counterfactual_prefix"] =
        std::move(counterfactual_payload);
    telemetry["proof_queue_policy_id"] =
        py::cast<std::string>(payload["proof_queue_policy_id"]);
    py::list best_reduced_cost_events;
    for (const auto& event : output.telemetry.best_reduced_cost_events) {
        py::dict row;
        row["elapsed_seconds"] = event.elapsed_seconds;
        row["extended_labels"] = event.extended_labels;
        row["solution_count"] = event.solution_count;
        row["discovered_reduced_cost"] = event.discovered_reduced_cost;
        row["best_reduced_cost"] = event.best_reduced_cost;
        best_reduced_cost_events.append(std::move(row));
    }
    telemetry["best_reduced_cost_event_schema"] =
        "lunar_spprc.best_reduced_cost_events.v1";
    telemetry["best_reduced_cost_events"] =
        std::move(best_reduced_cost_events);
    telemetry["best_reduced_cost_event_count_total"] =
        output.telemetry.best_reduced_cost_event_count_total;
    telemetry["best_reduced_cost_events_truncated"] =
        output.telemetry.best_reduced_cost_events_truncated;
    telemetry["proof_queue_potential_trace_enabled"] =
        output.telemetry.proof_queue_potential_trace_enabled;
    py::list proof_queue_potential_trace;
    const auto tasks = py::cast<py::list>(payload["tasks"]);
    for (const auto& row : output.telemetry.proof_queue_potential_trace) {
        py::dict trace_row;
        trace_row["task_index"] = row.task_index;
        trace_row["task_id"] = py::cast<py::dict>(tasks[row.task_index])["id"];
        trace_row["incoming_evaluated"] = row.incoming_evaluated;
        trace_row["incoming_rejected"] = row.incoming_rejected;
        trace_row["existing_dominator_wins"] = row.existing_dominator_wins;
        trace_row["accepted_removed_existing"] =
            row.accepted_removed_existing;
        trace_row["removed_as_existing"] = row.removed_as_existing;
        proof_queue_potential_trace.append(std::move(trace_row));
    }
    telemetry["proof_queue_potential_trace"] =
        std::move(proof_queue_potential_trace);
    telemetry["proof_queue_label_trace_enabled"] =
        output.telemetry.proof_queue_label_trace_enabled;
    telemetry["proof_queue_label_trace_truncated"] =
        output.telemetry.proof_queue_label_trace_truncated;
    telemetry["proof_queue_label_trace_incomplete"] =
        output.telemetry.proof_queue_label_trace_incomplete;
    telemetry["proof_queue_label_trace_sampling_mode"] =
        output.telemetry.proof_queue_label_trace_sampling_mode;
    telemetry["proof_queue_label_trace_seed"] =
        output.telemetry.proof_queue_label_trace_seed;
    telemetry["proof_queue_existing_preference_seen"] =
        output.telemetry.proof_queue_existing_preference_seen;
    telemetry["proof_queue_existing_preference_retained"] =
        output.telemetry.proof_queue_existing_preference_retained;
    telemetry["proof_queue_incoming_preference_seen"] =
        output.telemetry.proof_queue_incoming_preference_seen;
    telemetry["proof_queue_incoming_preference_retained"] =
        output.telemetry.proof_queue_incoming_preference_retained;
    telemetry["proof_queue_surface_seen"] =
        output.telemetry.proof_queue_surface_seen;
    telemetry["proof_queue_surface_retained"] =
        output.telemetry.proof_queue_surface_retained;
    telemetry["proof_queue_surface_label_retained"] =
        output.telemetry.proof_queue_surface_label_retained;
    telemetry["proof_queue_witness_seen"] =
        output.telemetry.proof_queue_witness_seen;
    telemetry["proof_queue_witness_retained"] =
        output.telemetry.proof_queue_witness_retained;
    telemetry["proof_queue_witness_ancestor_retained"] =
        output.telemetry.proof_queue_witness_ancestor_retained;
    telemetry["proof_queue_label_trace_final_rows"] =
        output.telemetry.proof_queue_label_trace_final_rows;
    py::list proof_queue_label_state_trace;
    for (const auto& row : output.telemetry.proof_queue_label_state_trace) {
        py::dict trace_row;
        trace_row["label_id"] = row.label_id;
        trace_row["parent_label_id"] = row.parent_label_id;
        trace_row["node_id"] = row.current_node_id;
        trace_row["task_index"] = row.last_task_index;
        trace_row["incoming_arc_index"] = row.last_model_arc_index;
        trace_row["visited_count"] = row.visited_count;
        trace_row["reduced_cost_bucket"] = row.reduced_cost_bucket;
        trace_row["partial_reduced_cost"] = row.partial_reduced_cost;
        trace_row["guidance_priority"] = row.label_state_priority;
        trace_row["terminal"] = row.can_terminate;
        py::list features;
        for (const auto value : row.features) {
            features.append(value);
        }
        trace_row["features"] = std::move(features);
        proof_queue_label_state_trace.append(std::move(trace_row));
    }
    telemetry["proof_queue_label_state_schema"] =
        "lunar_spprc.qg2_label_state.v1";
    telemetry["proof_queue_label_state_trace"] =
        std::move(proof_queue_label_state_trace);
    py::list proof_queue_label_preference_trace;
    for (const auto& row : output.telemetry.proof_queue_label_preference_trace) {
        py::dict trace_row;
        trace_row["preferred_label_id"] = row.winner_label_id;
        trace_row["other_label_id"] = row.loser_label_id;
        trace_row["kind"] =
            row.kind == lunar_spprc::LabelPreferenceKind::ExistingDominator
                ? "existing_dominator"
                : "incoming_dominator";
        proof_queue_label_preference_trace.append(std::move(trace_row));
    }
    telemetry["proof_queue_label_preference_trace"] =
        std::move(proof_queue_label_preference_trace);
    py::list proof_queue_negative_witness_trace;
    for (const auto& row : output.telemetry.proof_queue_negative_witness_trace) {
        py::dict trace_row;
        trace_row["solution_index"] = row.solution_index;
        trace_row["reduced_cost"] = row.reduced_cost;
        trace_row["elapsed_seconds"] = row.elapsed_seconds;
        trace_row["ancestor_label_ids"] = row.ancestor_label_ids;
        proof_queue_negative_witness_trace.append(std::move(trace_row));
    }
    telemetry["proof_queue_negative_witness_trace"] =
        std::move(proof_queue_negative_witness_trace);
    telemetry["proof_queue_guidance_scored_labels"] =
        output.telemetry.proof_queue_label_state_scored_count;
    telemetry["proof_queue_guidance_nonzero_labels"] =
        output.telemetry.proof_queue_guidance_nonzero_score_count;
    telemetry["proof_queue_guidance_order_decisions"] =
        output.telemetry.proof_queue_guidance_ordering_decision_count;
    telemetry["proof_queue_guidance_reordered_label_hash_count"] =
        output.telemetry.proof_queue_guidance_reordered_label_hash_count;
    telemetry["proof_queue_guidance_covered_bucket_count"] =
        output.telemetry.proof_queue_guidance_bucket_hash_count;
    telemetry["proof_queue_native_scoring_wall_time_seconds"] =
        output.telemetry.proof_queue_label_state_scoring_estimated_wall_seconds;
    telemetry["first_true_negative_wall_time_seconds"] =
        std::isfinite(output.telemetry.first_true_negative_wall_time_seconds)
            ? py::cast(output.telemetry.first_true_negative_wall_time_seconds)
            : py::none();
    telemetry["first_true_negative_processed_labels"] =
        output.telemetry.labels_processed_before_first_true_negative;
    py::list proof_queue_arc_potential_trace;
    const auto arcs = py::cast<py::list>(payload["arcs"]);
    for (const auto& row : output.telemetry.proof_queue_arc_potential_trace) {
        py::dict trace_row;
        const auto arc = py::cast<py::dict>(arcs[row.task_index]);
        trace_row["model_arc_index"] = row.task_index;
        trace_row["source"] = arc["source"];
        trace_row["target"] = arc["target"];
        trace_row["path_type"] = arc["path_type"];
        trace_row["incoming_evaluated"] = row.incoming_evaluated;
        trace_row["incoming_rejected"] = row.incoming_rejected;
        trace_row["existing_dominator_wins"] = row.existing_dominator_wins;
        trace_row["accepted_removed_existing"] =
            row.accepted_removed_existing;
        trace_row["removed_as_existing"] = row.removed_as_existing;
        proof_queue_arc_potential_trace.append(std::move(trace_row));
    }
    telemetry["proof_queue_arc_potential_trace"] =
        std::move(proof_queue_arc_potential_trace);
    telemetry["dssr_enabled"] = output.telemetry.dssr_enabled;
    telemetry["dssr_policy_version"] =
        output.telemetry.dssr_policy_version;
    telemetry["dssr_iteration_count"] =
        output.telemetry.dssr_iteration_count;
    telemetry["dssr_refinement_count"] =
        output.telemetry.dssr_refinement_count;
    telemetry["dssr_initial_critical_task_count"] =
        output.telemetry.dssr_initial_critical_task_count;
    telemetry["dssr_final_critical_task_count"] =
        output.telemetry.dssr_final_critical_task_count;
    telemetry["dssr_repeated_witness_count"] =
        output.telemetry.dssr_repeated_witness_count;
    telemetry["dssr_elementary_witness_returned"] =
        output.telemetry.dssr_elementary_witness_returned;
    telemetry["dssr_relaxation_no_negative_certificate"] =
        output.telemetry.dssr_relaxation_no_negative_certificate;
    telemetry["dssr_elementary_batch_count"] =
        output.telemetry.dssr_elementary_batch_count;
    telemetry["dssr_raw_solution_count"] =
        output.telemetry.dssr_raw_solution_count;
    telemetry["dssr_pressure_refinement_count"] =
        output.telemetry.dssr_pressure_refinement_count;
    telemetry["dssr_pressure_split_task_ids"] =
        output.telemetry.dssr_pressure_split_task_ids;
    telemetry["dssr_pressure_abandoned_iteration_count"] =
        output.telemetry.dssr_pressure_abandoned_iteration_count;
    telemetry["dssr_max_bucket_size"] =
        output.telemetry.dssr_max_bucket_size;
    telemetry["dssr_dominance_candidate_checks"] =
        output.telemetry.dssr_dominance_candidate_checks;
    telemetry["ng_dssr_enabled"] =
        output.telemetry.ng_dssr_enabled;
    telemetry["ng_dssr_initial_neighborhood_size"] =
        output.telemetry.ng_dssr_initial_neighborhood_size;
    telemetry["ng_dssr_initial_relation_count"] =
        output.telemetry.ng_dssr_initial_relation_count;
    telemetry["ng_dssr_final_relation_count"] =
        output.telemetry.ng_dssr_final_relation_count;
    telemetry["ng_dssr_relation_add_count"] =
        output.telemetry.ng_dssr_relation_add_count;
    telemetry["ng_dssr_forbidden_cycle_count"] =
        output.telemetry.ng_dssr_forbidden_cycle_count;
    telemetry["ng_dssr_full_elementary_fallback_count"] =
        output.telemetry.ng_dssr_full_elementary_fallback_count;
    py::list dssr_iteration_trace;
    for (const auto& row : output.telemetry.dssr_iteration_trace) {
        py::dict trace_row;
        trace_row["iteration"] = row.iteration;
        trace_row["critical_task_count_before"] =
            row.critical_task_count_before;
        trace_row["repeated_task_count"] = row.repeated_task_count;
        trace_row["processed_labels"] = row.processed_labels;
        trace_row["extended_labels"] = row.extended_labels;
        trace_row["dominated_labels"] = row.dominated_labels;
        trace_row["max_visited_bucket_size"] =
            row.max_visited_bucket_size;
        trace_row["wall_time_seconds"] = row.wall_time_seconds;
        trace_row["status"] = row.status;
        trace_row["search_exhaustive"] = row.search_exhaustive;
        trace_row["frontier_empty"] = row.frontier_empty;
        trace_row["labels_dropped"] = row.labels_dropped;
        trace_row["negative_witness_found"] =
            row.negative_witness_found;
        trace_row["witness_elementary"] = row.witness_elementary;
        trace_row["raw_solution_count"] = row.raw_solution_count;
        trace_row["elementary_solution_count"] =
            row.elementary_solution_count;
        trace_row["non_elementary_solution_count"] =
            row.non_elementary_solution_count;
        trace_row["pressure_refinement_triggered"] =
            row.pressure_refinement_triggered;
        trace_row["pressure_split_task_id"] =
            row.pressure_split_task_id;
        trace_row["ng_relation_count_before"] =
            row.ng_relation_count_before;
        trace_row["ng_relation_add_count"] =
            row.ng_relation_add_count;
        trace_row["ng_forbidden_cycle_count"] =
            row.ng_forbidden_cycle_count;
        dssr_iteration_trace.append(std::move(trace_row));
    }
    telemetry["dssr_iteration_trace"] =
        std::move(dssr_iteration_trace);

    py::dict result;
    result["status"] = output.status;
    result["routes"] = std::move(routes);
    result["search_exhaustive"] = output.search_exhaustive;
    result["frontier_empty"] = output.frontier_empty;
    result["labels_dropped"] = output.labels_dropped;
    result["best_found_rc"] = output.routes.empty()
                                  ? py::none()
                                  : py::cast(output.routes.front().reduced_cost);
    result["unexplored_rc_lower_bound"] = py::none();
    result["certificate_blockers"] = py::list();
    result["truncated_diagnostic"] =
        output.telemetry.counterfactual_prefix.enabled;
    result["exact"] =
        !output.telemetry.counterfactual_prefix.enabled;
    result["certificate"] = py::none();
    result["telemetry"] = std::move(telemetry);
    result["build_info"] = lunar_spprc::build_info();
    py::dict bindings;
    for (const auto* key : {
             "instance_hash",
             "config_hash",
             "engine_hash",
             "service_timing_policy_id",
             "exact_negative_escape_enabled",
             "exact_admission_batch_size",
             "exact_raw_negative_pool_size",
             "exact_negative_escape_policy_id",
             "dssr_enabled",
             "dssr_policy_version",
             "dssr_negative_batch_target",
             "dssr_pressure_refinement_enabled",
             "dssr_pressure_max_bucket_size",
             "dssr_pressure_max_candidate_checks",
             "ng_dssr_initial_neighborhood_size",
             "canonical_solve_binding_v2",
             "canonical_solve_binding_v2_schema",
             "canonical_solve_binding_v2_hash",
             "dual_binding_hash",
             "branch_context_hash",
             "objective_mode",
             "rmp_iteration_id",
             "active_cut_context_hash",
             "active_cut_count",
             "pricing_cut_context_hash",
             "pricing_cut_count",
             "cut_dual_projection_enabled",
             "cut_dual_projection_schema_version",
             "cut_lineage_hash",
             "live_cut_policy_hash",
             "cut_state_schema_version",
             "separator_policy_version",
             "negative_eps",
             "guidance_mode",
             "guidance_effective_mode",
             "guidance_binding_hash",
             "guidance_task_arc_enabled",
             "guidance_label_state_enabled",
             "guidance_label_state_schema_version",
             "proof_queue_frontier_probe_mode",
             "proof_queue_frontier_probe_boundary",
             "proof_queue_frontier_trial_pop_budget",
             "proof_queue_frontier_problem_scale",
             "proof_queue_frontier_pricing_lifecycle",
             "proof_queue_frontier_require_root_cg",
             "proof_queue_frontier_fail_closed_on_ood",
             "proof_queue_frontier_observation_boundaries",
             "proof_queue_frontier_manifest_sha256",
             "proof_queue_frontier_bundle_sha256",
             "proof_queue_counterfactual_prefix_mode",
             "proof_queue_counterfactual_prefix_boundary",
             "proof_queue_counterfactual_rollout_checkpoints",
             "proof_queue_counterfactual_label_sample_cap",
             "proof_queue_counterfactual_sampling_seed",
             "legal_task_universe_hash_before_sort",
             "legal_arc_universe_hash_before_sort",
             "guidance_native_install_sec",
         }) {
        bindings[py::str(key)] = payload[py::str(key)];
    }
    result["request_bindings"] = std::move(bindings);
    return result;
}

}  // namespace

PYBIND11_MODULE(lunar_spprc_native, module) {
    module.doc() = "Exact-safe lunar multi-sortie SPPRC extension";
    module.def("solve", &solve_payload, py::arg("request"));
    module.def("build_info", &lunar_spprc::build_info);
    module.def(
        "frontier_gat_forward",
        &frontier_gat_forward_payload,
        py::arg("bundle"),
        py::arg("graph"),
        py::arg("seed_index") = 0U);
    module.def(
        "counterfactual_gat_forward",
        &counterfactual_gat_forward_payload,
        py::arg("bundle"),
        py::arg("triplet"),
        py::arg("seed_index") = 0U);
    module.def(
        "temporal_gat_forward",
        &temporal_gat_forward_payload,
        py::arg("bundle"),
        py::arg("temporal_graph"),
        py::arg("seed_index") = 0U);
    module.def(
        "temporal_gat_forward_ensemble",
        &temporal_gat_forward_ensemble_payload,
        py::arg("bundle"),
        py::arg("temporal_graph"));
    module.def(
        "temporal_gat_forward_batch_ensemble",
        &temporal_gat_forward_batch_payload,
        py::arg("bundle"),
        py::arg("temporal_graphs"));
#if LUNAR_SPPRC_ENABLE_BIDIRECTIONAL_FEASIBILITY
    module.def(
        "bidirectional_feasibility_probe",
        &bidirectional_feasibility_payload,
        py::arg("request"));
    module.def(
        "bidirectional_backward_frontier_probe",
        &bidirectional_backward_frontier_payload,
        py::arg("request"));
    module.def(
        "bidirectional_task_meet_frontier_probe",
        &bidirectional_task_meet_frontier_payload,
        py::arg("request"));
    module.def(
        "bidirectional_journey_frontier_probe",
        &bidirectional_journey_frontier_payload,
        py::arg("request"));
    module.def(
        "bidirectional_midpoint_journey_meet",
        &bidirectional_midpoint_meet_payload,
        py::arg("request"));
#endif
}
