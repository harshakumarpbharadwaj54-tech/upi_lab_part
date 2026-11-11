from decimal import Decimal, InvalidOperation


def transfer(balance, amount, idempotency_key, saved_results):
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        return "rejected", balance

    if not value.is_finite() or value <= 0:
        return "rejected", balance

    previous = saved_results.get(idempotency_key)
    if previous is not None:
        saved_amount, result = previous
        if saved_amount != value:
            return "conflict", balance
        return result

    result = ("accepted", balance - value, idempotency_key)
    saved_results[idempotency_key] = (value, result)
    return result
