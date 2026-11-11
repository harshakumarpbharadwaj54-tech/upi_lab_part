from decimal import Decimal


def transfer(balance, amount, idempotency_key, saved_results):
    value = Decimal(str(amount))

    if value <= 0:
        return "rejected", balance

    # Bug: it never checks whether this key already succeeded.
    new_balance = balance - value
    result = ("accepted", new_balance, idempotency_key)
    saved_results[idempotency_key] = result
    return result