from pathlib import Path

from brain.flywire_data import load_neurons, load_connections

DATA_DIR = Path("brain/data")

neurons = load_neurons(DATA_DIR / "neurofly_neurons.csv")
connections = load_connections(DATA_DIR / "neurofly_connections.csv")

print("Neurons loaded:", len(neurons))
print("Connections loaded:", len(connections))

print("Neuron data type:", type(neurons))
print("Connection data type:", type(connections))