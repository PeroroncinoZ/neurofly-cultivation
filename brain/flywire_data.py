"""Load local, filtered connectome CSV files using the project's schema.

These loaders do not download data or control the fly. Exported column names
must match the schema below before loading; no biological values are inferred.
"""

import csv


def _read_rows(path, required_columns):
    """Read CSV rows and report missing columns or malformed records."""
    with open(path, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        headers = reader.fieldnames or []
        missing = set(required_columns) - set(headers)
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        if len(headers) != len(set(headers)):
            raise ValueError(f"{path}: duplicate column names")

        for row in reader:
            line = reader.line_num
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path}, line {line}: wrong number of CSV fields")
            row = {key: value.strip() for key, value in row.items()}
            for column in required_columns:
                if not row[column]:
                    raise ValueError(f"{path}, line {line}: empty {column}")
            yield line, row


def load_neurons(path):
    """Return neuron records from a local CSV as a list of dictionaries."""
    # Required: neuron_id.
    # Optional text: cell_type, annotations, neurotransmitter_type.
    # IDs stay strings to preserve large identifiers exactly.
    neurons = []
    seen_ids = set()
    for line, row in _read_rows(path, ("neuron_id",)):
        neuron_id = row["neuron_id"]
        if neuron_id in seen_ids:
            raise ValueError(f"{path}, line {line}: duplicate neuron_id {neuron_id}")
        seen_ids.add(neuron_id)
        neurons.append({
            "neuron_id": neuron_id,
            "cell_type": row.get("cell_type") or None,
            "annotations": row.get("annotations") or None,
            "neurotransmitter_type": row.get("neurotransmitter_type") or None,
        })
    return neurons


def load_connections(path):
    """Return directed connection records from a local CSV."""
    # Required: presynaptic_neuron_id, postsynaptic_neuron_id, synapse_count.
    # Optional: neurotransmitter_type, only if the export supplies it.
    required = ("presynaptic_neuron_id", "postsynaptic_neuron_id", "synapse_count")
    connections = []
    for line, row in _read_rows(path, required):
        try:
            count = int(row["synapse_count"])
        except ValueError:
            raise ValueError(
                f"{path}, line {line}: synapse_count must be a nonnegative integer"
            ) from None
        if count < 0:
            raise ValueError(f"{path}, line {line}: synapse_count must not be negative")
        connections.append({
            "presynaptic_neuron_id": row["presynaptic_neuron_id"],
            "postsynaptic_neuron_id": row["postsynaptic_neuron_id"],
            "synapse_count": count,
            "neurotransmitter_type": row.get("neurotransmitter_type") or None,
        })
    return connections
