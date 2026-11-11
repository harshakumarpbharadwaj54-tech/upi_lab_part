from decimal import Decimal, InvalidOperation


def parse_amount(value) -> Decimal:
    if isinstance(value, (bool, float)):
        raise ValueError("Amount must not be a bool or float")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Amount must be numeric") from error
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Amount must be finite and positive")
    return amount


def validate_transfer(
    account_id: str,
    payee_id: str,
    amount,
    balances: dict[str, Decimal],
    transfer_limit,
) -> Decimal:
    if not isinstance(account_id, str) or account_id not in balances:
        raise ValueError("Source account not found")
    if not isinstance(payee_id, str) or not payee_id.strip():
        raise ValueError("A valid payee is required")
    if any(character.isspace() for character in payee_id):
        raise ValueError("Payee cannot contain whitespace")
    if payee_id == account_id:
        raise ValueError("Payee cannot be the source account")

    value = parse_amount(amount)
    limit = parse_amount(transfer_limit)
    if value > limit:
        raise ValueError("Amount exceeds transfer limit")

    balance_value = balances[account_id]
    if isinstance(balance_value, (bool, float)):
        raise ValueError("Account balance must not be a bool or float")
    try:
        balance = (
            balance_value
            if isinstance(balance_value, Decimal)
            else Decimal(str(balance_value))
        )
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Account balance must be numeric") from error
    if not balance.is_finite() or balance < 0:
        raise ValueError("Account balance must be finite and non-negative")
    if value > balance:
        raise ValueError("Insufficient funds")

    return value


def request_fingerprint(
    account_id: str,
    payee_id: str,
    amount: Decimal,
) -> tuple[str, str, Decimal]:
    if not isinstance(account_id, str) or not isinstance(payee_id, str):
        raise ValueError("Account and payee IDs must be strings")
    return account_id, payee_id, parse_amount(amount).normalize()