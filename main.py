from __future__ import annotations
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from datetime import datetime, timedelta
from functools import reduce
from typing import Optional

import pandas as pd
from dateutil import parser

from accounts.accounts import AccountType, AccountId
from accounts.transactions import EntryType, Entry, Transaction
from histories.history import History
from histories.aggregation import Aggregation
from histories.prediction import Prediction


class MyAccounts:
    __accounts = {}

    @classmethod
    def get(cls, account_name, a_type) -> AccountId:
        if cls.__accounts.get(account_name, None) is None:
            cls.__accounts[account_name] = AccountId(a_type, account_name)

        return cls.__accounts[account_name]

    @classmethod
    def current(cls) -> AccountId:
        return cls.get('CURRENT', AccountType.DEBIT)

    @classmethod
    def gsl(cls):
        return cls.get('GSL', AccountType.DEBIT)

    @classmethod
    def income_tax(cls):
        return cls.get('PAYE', AccountType.CREDIT)

    @classmethod
    def ni(cls):
        return cls.get('NI', AccountType.CREDIT)

    @classmethod
    def expense(cls):
        return cls.get('LIABILITIES_INTEREST', AccountType.DEBIT)

    @classmethod
    def student_loan(cls):
        return cls.get('SLC', AccountType.CREDIT)




def get_bank_payments():
    bank_payments_converters = {'date': parser.parse, 'payment': to_pence}
    payments = pd.read_csv('input/bank_payments_in.csv', converters = bank_payments_converters)
    current_acct = MyAccounts.current()
    gsl = MyAccounts.gsl()

    transactions = History([])
    for index, row in payments.iterrows():
        payment_in_pence = row['payment']
        entries = [
            Entry(EntryType.DEBIT, payment_in_pence, current_acct),
            Entry(EntryType.CREDIT, payment_in_pence, gsl),
        ]
        transactions.include(Transaction(row['date'], entries))

    return transactions


def get_reported_payments():
    reported_payment_converters = {
        'Date': parser.parse,
        'Taxable Income': to_pence,
        'Income Tax paid': to_pence,
        'NI': to_pence,
        'Implied Net': to_pence,
    }

    transactions = History([])
    r_payments = pd.read_csv('input/reported_earnings.csv', converters = reported_payment_converters)
    for index, row in r_payments.iterrows():
        entries = [
            Entry(EntryType.CREDIT, row['Taxable Income'], MyAccounts.gsl()),
            Entry(EntryType.DEBIT, row['Implied Net'], MyAccounts.current()),
            Entry(EntryType.DEBIT, row['Income Tax paid'], MyAccounts.income_tax()),
            Entry(EntryType.DEBIT, row['NI'], MyAccounts.ni()),
        ]
        transactions.include(Transaction(row['Date'], entries))

    return transactions

def get_loan_transactions():
    converters = {
        'Date': parser.parse,
        'Name': str,
        'Credit': to_pence,
        'Debit': to_pence,
    }
    transactions = History([])
    loan_statement = pd.read_csv('input/student_loan_repayment.csv', converters = converters)
    for index, statement_entry in loan_statement.iterrows():
        entries = []
        interest = statement_entry['Credit']
        if interest:
            entries = get_loan_interest_entries(interest)
        repayment = statement_entry['Debit']
        if repayment:
            entries = [
                Entry(EntryType.DEBIT, repayment, MyAccounts.student_loan()),
                Entry(EntryType.CREDIT, repayment, MyAccounts.gsl())
            ]
            
        if entries:
            transactions.include(Transaction(statement_entry['Date'], entries))

    return transactions


def get_loan_interest_entries(interest):
    return [
        Entry(EntryType.CREDIT, interest, MyAccounts.student_loan()),
        Entry(EntryType.DEBIT, interest, MyAccounts.expense())
    ]


def get_loan_repayment_entries(repayment):
    return [
        Entry(EntryType.CREDIT, repayment, MyAccounts.student_loan()),
        Entry(EntryType.DEBIT, repayment, MyAccounts.expense())
    ]


def to_pence(pounds) -> Optional[int]:
    return int(round(float(pounds) * 100)) if pounds else 0


class FinancialYears:
    def __init__(self, year_start: datetime) -> None:
        self.__ys = datetime(1, year_start.month, year_start.day)

    def year_start(self, year: int) -> datetime:
        return datetime(year, self.__ys.month, self.__ys.day)

    def year_end(self, year: int) -> datetime:
        return self.year_start(year + 1) + timedelta(days = -1)

    def contains(self, date: datetime, financial_year: int) -> bool:
        return self.year_start(financial_year) < date <= self.year_end(financial_year)

    def from_datetime(self, dt: datetime) -> int:
        best_guess = dt.year
        fucked_it = not self.contains(dt, best_guess)
        if fucked_it:
            best_guess = best_guess - 1

        return best_guess


class ChangeInBalance(Aggregation):
    @staticmethod
    def apply_function(acc: float, transaction: Transaction, filter_by_account: AccountId) -> float:
        entries = transaction.get_entries_by_account(filter_by_account)
        acc += reduce(lambda x, y: x + y, map(lambda e: e.to_gbp(), entries)) if entries else 0

        return acc

    @classmethod
    def create(cls, acct_id: AccountId):
        accumulator = 0.0
        func = lambda acc, transaction: ChangeInBalance.apply_function(acc, transaction, acct_id)

        return cls(accumulator, func)

def estimate_monthly_interest(balance_gbp: float, annual_rate_percent: float) -> float:
    annual_growth_factor = 1.0 + (annual_rate_percent/100.0)
    monthly_growth_factor = annual_growth_factor**(1.0/12.0)
    interest_amount = (monthly_growth_factor - 1.0) * balance_gbp

    return round(interest_amount, 2)

def get_slc_annual_interest_rate_percent(date: datetime) -> float:
    rate = 1.10
    if date < datetime(2017, 1, 12):
        rate = 1.25
    elif date < datetime(2018, 9, 1):
        rate = 1.50
    elif date < datetime(2020, 4, 7):
        rate = 1.75

    return rate

def get_projected_loan_history() -> History:
    student_loan_balance = ChangeInBalance.create(MyAccounts.student_loan())
    year = 2018

    first_of_months = [datetime(year + i // 12, (i % 12) + 1, 1) for i in range(0, 32)]
    loan_transactions = get_loan_transactions()
    for i, date in enumerate(first_of_months[:-1]):
        start = date
        end = first_of_months[i + 1] - timedelta(days = 1)
        balance_as_of_start = student_loan_balance.apply_up_to(start, loan_transactions)

        monthly_interest = to_pence(estimate_monthly_interest(balance_as_of_start, get_slc_annual_interest_rate_percent(end)))
        loan_transactions.include(Transaction(end, get_loan_interest_entries(monthly_interest)))

    balance_at_year_end = 30051.96
    prediction = Prediction(student_loan_balance)
    year_end = datetime(2020, 4, 1)
    implied_repayment = prediction.minus(balance_at_year_end, loan_transactions, end = year_end)
    repayment_transactions = [Transaction(datetime(year_end.year-1 + (i + year_end.month)//12 , ((year_end.month + i) % 12) + 1, year_end.day), get_loan_repayment_entries(to_pence(implied_repayment)/12)) for i in range(0,12)]
    for repayment_transaction in repayment_transactions:
        loan_transactions.include(repayment_transaction)

    return loan_transactions







def main() -> None:
    total_take_home = ChangeInBalance.create(MyAccounts.current())
    loan_repaid = ChangeInBalance.create(MyAccounts.expense())
    year = 2018

    first_of_months = [datetime(year + i // 12, (i % 12) + 1, 1) for i in range(0, 32)]
    cumulative_diff = 0.0
    rows = []
    index = []
    bank_payments = get_bank_payments()
    reported_payments = get_reported_payments()
    loan_transactions = get_projected_loan_history()

    for i, date in enumerate(first_of_months[:-1]):
        start = date
        end = first_of_months[i+1]

        payments_received = total_take_home.apply_in_interval(start, end, bank_payments)
        payments_reported = total_take_home.apply_in_interval(start, end, reported_payments)
        loan_deduction = loan_repaid.apply_in_interval(start, end, loan_transactions)

        diff = round(payments_reported - loan_deduction - payments_received, 2)
        cumulative_diff += diff

        index.append( str(date.year) + '/' + str(date.month))
        row = {
            'received': round(payments_received, 2),
            'reported': round(payments_reported, 2),
            'loan_deductions': round(loan_deduction, 2),
            'discrepancy ': round(diff, 2),
            'cumulative_discrepancy': round(cumulative_diff, 2)
        }
        rows.append(row)

    df = pd.DataFrame(rows, index = index)
    df.to_csv('income_discrepancy.csv', index_label = 'month')


if __name__ == '__main__':
    main()

    # See PyCharm help at https://www.jetbrains.com/help/pycharm/
