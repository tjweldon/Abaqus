from __future__ import annotations
from datetime import datetime
from enum import IntEnum
from functools import reduce
from typing import List

from accounts.accounts import AccountId
from histories.event import Event


class EntryType(IntEnum):
    DEBIT = 0
    CREDIT = 1

    def __str__(self) -> str:
        return ['DR', 'CR'][self.value]


class Entry:
    def __init__(self, e_type: EntryType, amount_pence: int, account_id: AccountId):
        self.amount_pence = round(amount_pence)
        self.e_type = e_type
        self.account_id = account_id

    def __int__(self):
        return self.amount_pence * (-1) ** (int(self.e_type))

    def __add__(self, other):
        return int(self) + int(other)

    def to_gbp(self) -> float:
        return  round(float(int(self))/100.0, 2)



class Transaction(Event):
    def __init__(self, dt: datetime, entries: List[Entry]):
        self.entries = entries
        super().__init__(dt)
        Transaction.validate(self)

    @staticmethod
    def validate(transaction: Transaction) -> None:
        errors = []

        if len(transaction.entries) < 2:
            errors.append('Less than two entries were supplied')

        total = reduce(lambda x, y: x + y, map(int, transaction.entries))
        if total != 0:
            errors.append(
                'The entries do not balance, total discrepancy in pence: {}.'.format(total)
            )

        if errors:
            raise ValueError(' '.join(errors))

    def get_entries_by_account(self, account_id: AccountId) -> List[Entry]:
        return list(filter(lambda x: x.account_id.id == account_id.id, self.entries))
