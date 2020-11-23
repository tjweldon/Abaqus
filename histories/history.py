from __future__ import annotations
from datetime import datetime
from typing import List

from histories.event import Event


class History:
    def __init__(self, events: List[Event]):
        self.events = events

    def get_chronological(self) -> List[Event]:
        events_ = [event for event in self.events]
        events_.sort(key = lambda e: e.date)

        return events_

    def combine(self, other: History) -> History:
        self.events = self.events + other.events
        self.events = self.get_chronological()

        return self

    def include(self, event: Event) -> History:
        self.events.append(event)
        self.events = self.get_chronological()

        return self

    def events_since(self, date: datetime, inclusive = False) -> History:
        filters = [
            lambda x: x.date > date,
            lambda x: x.date >= date
        ]
        subsequent_events = list(filter(filters[inclusive], self.events))

        return History(subsequent_events)

    def events_before(self, date: datetime, inclusive = True) -> History:
        filters = [
            lambda x: x.date < date,
            lambda x: x.date <= date
        ]
        preceding_events = list(filter(filters[inclusive], self.events))

        return History(preceding_events)