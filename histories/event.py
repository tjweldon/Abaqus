from __future__ import annotations
import uuid
from copy import copy
from datetime import datetime


class Event:
    def __init__(self, dt: datetime):
        self.date = copy(dt)
        self.id = uuid.uuid1()

    @classmethod
    def from_datetime(cls, dt: datetime):
        return cls(dt)

    def __ge__(self, other: Event):
        return self.date >= other.date

    def __gt__(self, other):
        return self.date > other.date

    def __le__(self, other):
        return self.date <= other.date

    def __lt__(self, other):
        return self.date < other.date