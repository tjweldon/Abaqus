import uuid
from enum import IntEnum


class AccountType(IntEnum):
    DEBIT = 0
    CREDIT = 1

    def __str__(self) -> str:
        return ['DR', 'CR'][self.value]


class AccountId:
    def __init__(self, a_type: AccountType, name: str):
        self.a_type = a_type
        self.name = name
        self.id = uuid.uuid1()

