from brain.neural_graph import (
    build_neural_graph,
    get_node_count,
    get_edge_count,
    get_outgoing_neighbors,
    get_incoming_neighbors,
    get_neuron_by_root_id,
)

graph = build_neural_graph()

print("Nodes:", get_node_count(graph))
print("Edges:", get_edge_count(graph))

test_id = 720575940630770042

neuron = get_neuron_by_root_id(graph, test_id)

print("\nTest neuron:")
print(neuron)

print("\nOutgoing neighbors:")
print(get_outgoing_neighbors(graph, test_id))

print("\nIncoming neighbors:")
print(get_incoming_neighbors(graph, test_id))