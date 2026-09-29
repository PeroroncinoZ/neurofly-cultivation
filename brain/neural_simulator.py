"""Simplified connectome-based activity propagation, not a biological simulation.

Each step uses the previous activations to compute a synapse-weighted mean for
each target, then multiplies it by (1 - decay). Neurons with no incoming edges
retain their previous activity subject to decay. External inputs are held at
their assigned values until cleared. All connections transmit positive activity;
no neurotransmitter effects, membrane voltages, or spike timing are inferred.
"""

import math


def create_activation_state(graph):
    """Create zero activity for every neuron and an empty external-input map."""
    return {
        "activations": {root_id: 0.0 for root_id in graph["nodes"]},
        "external_inputs": {},
    }


def set_external_activation(state, root_ids, activation):
    """Hold selected neurons at a value in [0, 1], including between steps.

    Pass an iterable of integer root IDs. Call again to change the input value.
    """
    value = float(activation)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("external activation must be between 0 and 1")
    root_ids = list(root_ids)
    # Validate all IDs before changing any activity.
    for root_id in root_ids:
        if root_id not in state["activations"]:
            raise KeyError(f"Unknown neuron root ID: {root_id}")
    for root_id in root_ids:
        state["external_inputs"][root_id] = value
        state["activations"][root_id] = value


def clear_external_activation(state):
    """Release all held inputs; their current activity remains for the next step."""
    state["external_inputs"].clear()


def advance_network(graph, state, decay=0.05):
    """Advance one synchronous step in place and return the updated state.

    For neuron j with incoming edges:
        mean_j = sum(weight_ij * activity_i) / sum(weight_ij)
        next_j = clamp((1 - decay) * mean_j, 0, 1)
    With no incoming weight, use activity_j instead of mean_j.
    Held external inputs override next_j and are not decayed.
    """
    if not math.isfinite(decay) or not 0.0 <= decay <= 1.0:
        raise ValueError("decay must be between 0 and 1")

    previous = state["activations"]
    weighted_activity = {root_id: 0.0 for root_id in graph["nodes"]}
    incoming_weight = {root_id: 0.0 for root_id in graph["nodes"]}
    for edge in graph["edges"]:
        source = edge["pre_root_id"]
        target = edge["post_root_id"]
        weight = edge["weight"]  # neural_graph sets this to synapse_count.
        weighted_activity[target] += weight * previous[source]
        incoming_weight[target] += weight

    # Build a separate result so activity travels only one edge per step.
    updated = {}
    for root_id in graph["nodes"]:
        if incoming_weight[root_id] > 0:
            activity = weighted_activity[root_id] / incoming_weight[root_id]
        else:
            activity = previous[root_id]
        updated[root_id] = max(0.0, min(1.0, (1.0 - decay) * activity))

    updated.update(state["external_inputs"])
    state["activations"] = updated
    return state


def get_activation(state, root_id):
    """Return a neuron's activity; unknown root IDs raise KeyError."""
    return state["activations"][root_id]


def get_most_active_neurons(state, count=10):
    """Return (root_id, activation) pairs, highest first; ties use root ID."""
    if not isinstance(count, int) or count < 0:
        raise ValueError("count must be a nonnegative integer")
    ranked = sorted(
        state["activations"].items(),
        key=lambda item: (-item[1], item[0]),
    )
    return ranked[:count]
