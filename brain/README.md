# Connectome data loading

This package prepares NeuroFly to read a **local, filtered subset** of FlyWire
FAFB v783 data exported from Codex. It does not download data, include biological
records, or connect to the current game controller.

## Expected CSV schema

These are **project-defined column names**, not a claim about the exact headers
of a Codex export. Inspect your export and explicitly rename corresponding
columns before loading. Do not fill missing biological annotations with guesses.

`neurons.csv` has one row per neuron:

| Column | Required | Meaning |
| --- | --- | --- |
| `neuron_id` | Yes | Neuron identifier, kept as a string |
| `cell_type` | No | Cell type supplied by the export |
| `annotations` | No | Annotation text supplied by the export |
| `neurotransmitter_type` | No | Transmitter label supplied by the export |

`connections.csv` has one row per directed connection record:

| Column | Required | Meaning |
| --- | --- | --- |
| `presynaptic_neuron_id` | Yes | Source neuron identifier |
| `postsynaptic_neuron_id` | Yes | Target neuron identifier |
| `synapse_count` | Yes | Nonnegative integer synapse count |
| `neurotransmitter_type` | No | Transmitter label, if supplied for the record |

Use UTF-8 CSV files with a header row. Quote fields containing commas, such as
annotation text. Optional columns may be absent or blank; the loader returns
`None` for missing values. Annotations remain text without interpretation.
Extra columns are ignored. IDs are never converted to floating-point numbers.

## Usage

Run from the project root with paths to your own prepared files:

```python
from brain.flywire_data import load_connections, load_neurons

neurons = load_neurons("data/neurons.csv")
connections = load_connections("data/connections.csv")
```

Both functions return lists of dictionaries and use only Python's standard
library. They load the supplied subset into memory. A header-only file returns
an empty list. Missing required headers or values, malformed rows, duplicate
neuron IDs, and invalid synapse counts raise `ValueError`. File access errors
propagate normally.

Connection records are preserved individually, without merging duplicates or
checking whether endpoints appear in the neuron file. The loaders do not infer
transmitters, cell types, or neural dynamics from synapse counts.

Keep the original export and a note of its version, source, filters, and any
column renaming alongside your prepared files. The CSV schema alone cannot
verify that the data came from v783.

`__init__.py` marks this directory as a package. `flywire_data.py` owns parsing
and basic validation. Nothing is imported by the simulation yet.
