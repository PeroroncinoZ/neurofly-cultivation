"""Load local FlyWire CSV exports without downloading data or controlling the fly."""

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
    # Require root_id and preserve every other metadata column as text.
    neurons = []
    seen_ids = set()
    for line, row in _read_rows(path, ("root_id",)):
        # Convert directly to int, never float, to preserve large IDs exactly.
        try:
            root_id = int(row["root_id"])
        except ValueError:
            raise ValueError(f"{path}, line {line}: root_id must be an integer") from None
        if root_id in seen_ids:
            raise ValueError(f"{path}, line {line}: duplicate root_id {root_id}")
        seen_ids.add(root_id)
        row["root_id"] = root_id
        neurons.append(row)
    return neurons


def load_connections(path):
    """Read five connection columns in their export order, without a header."""
    columns = ("pre_root_id", "post_root_id", "neuropil", "synapse_count", "nt_type")
    export_header = ("From", "To", "Neuropil", "Synapses", "Neuro Transmitter")
    connections = []
    first_row = True
    with open(path, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        for values in reader:
            if not values:
                continue
            values = [value.strip() for value in values]
            # Also accept the known header present in the current local file.
            if first_row:
                first_row = False
                if tuple(values) in (export_header, columns):
                    continue
            line = reader.line_num
            if len(values) != len(columns):
                raise ValueError(f"{path}, line {line}: expected five CSV fields")
            row = dict(zip(columns, values))
            for column in ("pre_root_id", "post_root_id", "synapse_count"):
                try:
                    row[column] = int(row[column])
                except ValueError:
                    raise ValueError(
                        f"{path}, line {line}: {column} must be an integer"
                    ) from None
            if row["synapse_count"] < 0:
                raise ValueError(f"{path}, line {line}: synapse_count must not be negative")
            connections.append(row)
    return connections


def get_internal_connections(neurons, connections):
    """Return connections whose two endpoints are in the loaded neurons."""
    neuron_ids = {neuron["root_id"] for neuron in neurons}
    return [
        connection for connection in connections
        if connection["pre_root_id"] in neuron_ids
        and connection["post_root_id"] in neuron_ids
    ]


def filter_connections_by_synapse_count(connections, minimum):
    """Return connections with at least minimum synapses."""
    return [
        connection for connection in connections
        if connection["synapse_count"] >= minimum
    ]


def get_neuron_by_root_id(neurons, root_id):
    """Return metadata for an integer root ID, or None if it is absent."""
    for neuron in neurons:
        if neuron["root_id"] == root_id:
            return neuron
    return None
