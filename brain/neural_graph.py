"""Build a directed graph of the local FlyWire subset, without neural dynamics.

The graph is a dictionary with two entries:
    nodes: maps integer root IDs to their complete neuron metadata.
    edges: a list of connection dictionaries, each with a synapse-count weight.

Keeping edges in a list preserves separate records between the same neurons
(for example, connections recorded in different neuropils).
"""

from pathlib import Path

from brain.flywire_data import (
    filter_connections_by_synapse_count,
    get_internal_connections,
    load_connections,
    load_neurons,
)


DATA_DIR = Path(__file__).resolve().parent / "data"
MINIMUM_SYNAPSES = 5


def build_neural_graph(
    neuron_path=DATA_DIR / "neurofly_neurons_v3.csv",
    connection_path=DATA_DIR / "neurofly_connections_v3.csv",
):
    """Load all selected neurons and internal connections with >= 5 synapses."""
    neurons = load_neurons(neuron_path)
    connections = load_connections(connection_path)
    internal = get_internal_connections(neurons, connections)
    strong = filter_connections_by_synapse_count(internal, MINIMUM_SYNAPSES)

    # Retain neurons even when they have no surviving connections.
    nodes = {neuron["root_id"]: neuron.copy() for neuron in neurons}
    edges = []
    for connection in strong:
        edge = connection.copy()
        edge["weight"] = connection["synapse_count"]
        edges.append(edge)

    return {"nodes": nodes, "edges": edges}


def get_node_count(graph):
    """Return the number of neurons, including isolated neurons."""
    return len(graph["nodes"])


def get_edge_count(graph):
    """Return the number of connection records, including parallel edges."""
    return len(graph["edges"])


def get_outgoing_neighbors(graph, root_id):
    """Return sorted, unique target IDs; return [] if there are none."""
    return sorted({
        edge["post_root_id"] for edge in graph["edges"]
        if edge["pre_root_id"] == root_id
    })


def get_incoming_neighbors(graph, root_id):
    """Return sorted, unique source IDs; return [] if there are none."""
    return sorted({
        edge["pre_root_id"] for edge in graph["edges"]
        if edge["post_root_id"] == root_id
    })


def get_neuron_by_root_id(graph, root_id):
    """Return neuron metadata for an integer root ID, or None if absent."""
    return graph["nodes"].get(root_id)
