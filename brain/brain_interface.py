"""Bridge game odor to simplified connectome activity, without motor output.

This is a demonstration input mapping, not a calibrated biological odor model.
The same scalar odor input drives every selected ORN_DM1 neuron on both sides.
"""

import math

from brain.neural_graph import build_neural_graph
from brain.neural_simulator import (
    advance_network,
    create_activation_state,
    get_activation,
    set_external_activation,
)


class BrainInterface:
    def __init__(self, graph=None):
        self.graph = build_neural_graph() if graph is None else graph
        self.state = create_activation_state(self.graph)
        self.odor_input = 0.0
        neurons = self.graph["nodes"].values()
        self.input_ids = [
            neuron["root_id"] for neuron in neurons
            if "ORN_DM1" in (neuron.get("cell_type") or "")
        ]
        if not self.input_ids:
            raise ValueError("The graph has no ORN_DM1 input neurons")

        self.dm1_lpn_ids = {}
        for side in ("left", "right"):
            matches = [
                neuron["root_id"] for neuron in neurons
                if "DM1_lPN" in (neuron.get("cell_type") or "")
                and neuron.get("side") == side
            ]
            if len(matches) != 1:
                raise ValueError(f"Expected one {side} DM1_lPN; found {len(matches)}")
            self.dm1_lpn_ids[side] = matches[0]

        # Select only the LH-labeled cell types in this exported subset.
        # This includes LHPD5c1 records whose class field is blank.
        self.lateral_horn_ids = [
            neuron["root_id"] for neuron in neurons
            if "LH" in (neuron.get("cell_type") or "")
        ]
        if not self.lateral_horn_ids:
            raise ValueError("The graph has no LH-labeled cell types")
        self.output_ids = {}
        for side in ("left", "right"):
            self.output_ids[side] = [
                root_id for root_id in self.lateral_horn_ids
                if self.graph["nodes"][root_id].get("side") == side
            ]
            if not self.output_ids[side]:
                raise ValueError(f"The graph has no {side} LH output neurons")

    def update(self, odor_strength):
        """Apply this frame's odor and advance one discrete network step."""
        if not math.isfinite(odor_strength):
            raise ValueError("odor_strength must be finite")
        self.odor_input = max(0.0, min(1.0, float(odor_strength)))
        # Reassign even zero, so losing the scent removes the previous drive.
        set_external_activation(self.state, self.input_ids, self.odor_input)
        advance_network(self.graph, self.state)

    def _average_activation(self, root_ids):
        return sum(get_activation(self.state, root_id) for root_id in root_ids) / len(root_ids)

    def get_debug_values(self):
        """Return post-step activity summaries, with no movement decisions."""
        return {
            "odor_input": self.odor_input,
            "orn_dm1_average": self._average_activation(self.input_ids),
            "dm1_lpn_left": get_activation(self.state, self.dm1_lpn_ids["left"]),
            "dm1_lpn_right": get_activation(self.state, self.dm1_lpn_ids["right"]),
            "lateral_horn_average": self._average_activation(self.lateral_horn_ids),
            "left_output": self._average_activation(self.output_ids["left"]),
            "right_output": self._average_activation(self.output_ids["right"]),
        }
