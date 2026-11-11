from decimal import Decimal

from l3_1.transfer_fixed import transfer



def test_first_transfer_debits_once():
    saved = {}
    status, balance, key = transfer(Decimal("500"), "75", "retry-1", saved)
    assert status == "accepted"
    assert balance == Decimal("425")


def test_identical_retry_does_not_debit_again():
    saved = {}
    first = transfer(Decimal("500"), "75", "retry-1", saved)
    retry = transfer(first[1], "75", "retry-1", saved)
    assert retry == first
    assert retry[1] == Decimal("425")


def test_changed_amount_with_same_key_conflicts():
    saved = {}
    first = transfer(Decimal("500"), "75", "retry-1", saved)
    conflict = transfer(first[1], "25", "retry-1", saved)
    assert conflict[0] == "conflict"
    assert conflict[1] == Decimal("425")


def test_invalid_amount_is_rejected_without_debit():
    saved = {}
    result = transfer(Decimal("500"), "0", "retry-2", saved)
    assert result[0] == "rejected"
    assert result[1] == Decimal("500")
