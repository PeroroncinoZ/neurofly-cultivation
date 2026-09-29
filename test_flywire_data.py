from pathlib import Path

from brain.flywire_data import (
    load_neurons,
    load_connections,
    get_internal_connections,
    filter_connections_by_synapse_count,
)

DATA_DIR = Path("brain/data")

neurons = load_neurons(DATA_DIR / "neurofly_neurons.csv")
connections = load_connections(DATA_DIR / "neurofly_connections.csv")

internal = get_internal_connections(neurons, connections)
strong = filter_connections_by_synapse_count(internal, 5)

print("Neurons loaded:", len(neurons))
print("Connections loaded:", len(connections))
print("Internal connections:", len(internal))
print("Internal connections with >= 5 synapses:", len(strong))