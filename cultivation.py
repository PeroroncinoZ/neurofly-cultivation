"""One-way cultivation progression from cumulative Qi; no gameplay stat effects."""

STAGES = ('Mortal', 'Qi Condensation', 'Foundation Establishment', 'Golden Core')
# Total Qi needed to enter each stage, not costs deducted on breakthrough.
QI_THRESHOLDS = (0, 5, 15, 35)


class Cultivation:
    def __init__(self, thresholds=None):
        self.thresholds = tuple(QI_THRESHOLDS if thresholds is None else thresholds)
        if (len(self.thresholds) != len(STAGES)
                or any(type(value) is not int or value < 0 for value in self.thresholds)
                or self.thresholds[0] != 0
                or any(a >= b for a, b in zip(self.thresholds, self.thresholds[1:]))):
            raise ValueError('Provide four increasing integer Qi thresholds starting at zero')
        self.stage_index = 0
        self.qi = 0

    @property
    def stage(self):
        return STAGES[self.stage_index]

    @property
    def next_stage_qi(self):
        """Total Qi required for the next stage, or None at Golden Core."""
        if self.stage_index == len(STAGES) - 1:
            return None
        return self.thresholds[self.stage_index + 1]

    def update(self, total_qi):
        """Observe the fly's existing Qi total; never award or spend Qi."""
        if type(total_qi) is not int or total_qi < 0:
            raise ValueError('total_qi must be a nonnegative integer')
        self.qi = total_qi
        while self.next_stage_qi is not None and total_qi >= self.next_stage_qi:
            self.stage_index += 1
        return self.stage

    def display_lines(self):
        requirement = self.next_stage_qi
        return [
            f'Cultivation: {self.stage}',
            f'Qi: {self.qi}',
            'Max stage' if requirement is None else
            f'Next stage: {requirement} total Qi ({max(0, requirement - self.qi)} more)',
        ]
