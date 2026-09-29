"""Bridge game odor to simplified connectome activity, without motor output.

This is a demonstration input mapping, not a calibrated biological odor model.
Left/right odor samples drive ORN_DM1 neurons with matching metadata sides.
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
        self.left_odor_input = 0.0
        self.right_odor_input = 0.0
        neurons = self.graph["nodes"].values()
        self.input_ids = [
            neuron["root_id"] for neuron in neurons
            if "ORN_DM1" in (neuron.get("cell_type") or "")
        ]
        if not self.input_ids:
            raise ValueError("The graph has no ORN_DM1 input neurons")
        self.input_ids_by_side = {}
        for side in ("left", "right"):
            self.input_ids_by_side[side] = [
                root_id for root_id in self.input_ids
                if self.graph["nodes"][root_id].get("side") == side
            ]
            if not self.input_ids_by_side[side]:
                raise ValueError(f"The graph has no {side} ORN_DM1 neurons")
        if sum(map(len, self.input_ids_by_side.values())) != len(self.input_ids):
            raise ValueError("All ORN_DM1 inputs must have left or right side metadata")

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

        self.dna02_ids = {
            "left": 720575940629327659,
            "right": 720575940604737708,
        }
        for side, root_id in self.dna02_ids.items():
            neuron = self.graph["nodes"].get(root_id)
            if (neuron is None or neuron.get("side") != side
                    or "DNa02" not in (neuron.get("cell_type") or "")):
                raise ValueError(f"Expected {side} DNa02 root ID {root_id}")

        self.debug_ids = {}
        for cell_type in ("APL", "MBON32"):
            for side in ("left", "right"):
                matches = [
                    neuron["root_id"] for neuron in neurons
                    if cell_type in (neuron.get("cell_type") or "")
                    and neuron.get("side") == side
                ]
                if len(matches) != 1:
                    raise ValueError(f"Expected one {side} {cell_type}; found {len(matches)}")
                self.debug_ids[f"{cell_type.lower()}_{side}"] = matches[0]

    def update(self, left_odor, right_odor):
        """Apply bilateral odor samples and advance one discrete network step."""
        if not math.isfinite(left_odor) or not math.isfinite(right_odor):
            raise ValueError("odor measurements must be finite")
        self.left_odor_input = max(0.0, min(1.0, float(left_odor)))
        self.right_odor_input = max(0.0, min(1.0, float(right_odor)))
        self.odor_input = (self.left_odor_input + self.right_odor_input) / 2
        # Reassign even zero, so losing the scent removes the previous drive.
        set_external_activation(self.state, self.input_ids_by_side["left"], self.left_odor_input)
        set_external_activation(self.state, self.input_ids_by_side["right"], self.right_odor_input)
        advance_network(self.graph, self.state)

    def _average_activation(self, root_ids):
        return sum(get_activation(self.state, root_id) for root_id in root_ids) / len(root_ids)

    def get_debug_values(self):
        """Return post-step activity summaries, with no movement decisions."""
        return {
            "odor_input": self.odor_input,
            "left_odor_input": self.left_odor_input,
            "right_odor_input": self.right_odor_input,
            "left_orn_average": self._average_activation(self.input_ids_by_side["left"]),
            "right_orn_average": self._average_activation(self.input_ids_by_side["right"]),
            "orn_dm1_average": self._average_activation(self.input_ids),
            "dm1_lpn_left": get_activation(self.state, self.dm1_lpn_ids["left"]),
            "dm1_lpn_right": get_activation(self.state, self.dm1_lpn_ids["right"]),
            **{key: get_activation(self.state, root_id)
               for key, root_id in self.debug_ids.items()},
            "dna02_left": get_activation(self.state, self.dna02_ids["left"]),
            "dna02_right": get_activation(self.state, self.dna02_ids["right"]),
            "dna02_difference": (
                get_activation(self.state, self.dna02_ids["right"])
                - get_activation(self.state, self.dna02_ids["left"])
            ),
        }
