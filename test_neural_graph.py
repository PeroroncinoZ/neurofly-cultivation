from brain.neural_graph import build_neural_graph, get_node_count, get_edge_count

graph = build_neural_graph()

print("Nodes:", get_node_count(graph))
print("Edges:", get_edge_count(graph))

paths = [
    # Left DM1 pathway -> right DNa02
    (720575940630770042, 720575940624547622, "DM1_L -> APL_L"),
    (720575940624547622, 720575940609959637, "APL_L -> MBON32_L"),
    (720575940609959637, 720575940604737708, "MBON32_L -> DNa02_R"),

    # Right DM1 pathway -> left DNa02
    (720575940619071005, 720575940613583001, "DM1_R -> APL_R"),
    (720575940613583001, 720575940638526278, "APL_R -> MBON32_R"),
    (720575940638526278, 720575940629327659, "MBON32_R -> DNa02_L"),
]

print("\nSteering pathway connections:")

for pre_id, post_id, label in paths:
    matches = [
        edge for edge in graph["edges"]
        if edge["pre_root_id"] == pre_id
        and edge["post_root_id"] == post_id
    ]

    if matches:
        total_synapses = sum(edge["synapse_count"] for edge in matches)
        print(f"{label}: FOUND ({total_synapses} synapses)")
    else:
        print(f"{label}: NOT FOUND")