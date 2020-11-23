from datetime import datetime
from functools import reduce
from typing import Callable, TypeVar

from histories.event import Event
from histories.history import History


_T = TypeVar('_T')

class Aggregation:
    def __init__(self, accumulator: _T, apply: Callable[[_T, Event], _T]) -> None:
        self._accumulator = accumulator
        self._apply = apply

    def apply_to(self, history: History) -> _T:
        chronological_events = [self._accumulator] + history.get_chronological()
        value = reduce(self._apply, chronological_events) if history.get_chronological() else self._accumulator
        return value

    def apply_from(self, date: datetime, history: History) -> _T:
        return self.apply_to(history.events_since(date))

    def apply_up_to(self, date: datetime, history: History) -> _T:
        return self.apply_to(history.events_before(date))

    def apply_in_interval(self, start: datetime, end: datetime, history: History) -> _T:
        return self.apply_to(history.events_since(start).events_before(end))