from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Optional

from histories.aggregation import Aggregation, _T
from histories.history import History

class Prediction:
    def __init__(self, aggregation: Aggregation) -> None:
        self._aggregation = aggregation

    def minus(
        self,
        predicted_value: _T,
        history: History,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> _T:
        if start and end and start >= end:
            raise ValueError

        if start and end:
            discrepancy = predicted_value - self._aggregation.apply_in_interval(start, end, history)
        elif start:
            discrepancy = predicted_value - self._aggregation.apply_from(start, history)
        elif end:
            discrepancy = predicted_value - self._aggregation.apply_up_to(end, history)
        else:
            discrepancy = predicted_value - self._aggregation.apply_to(history)

        return discrepancy



