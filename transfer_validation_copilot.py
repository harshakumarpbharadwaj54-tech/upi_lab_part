from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from threading import Lock


@dataclass(frozen=True)
class TransferResult:
    status: str
    message: str
    balance: Decimal
    reference: str | None = None


class TransferService:
    def __init__(
        self,
        balances: dict[str, Decimal],
        transfer_limit: Decimal,
    ) -> None:
        self.balances = {
            account_id: self._to_decimal(balance, "Account balance")
            for account_id, balance in balances.items()
        }
        self.transfer_limit = self._to_decimal(transfer_limit, "Transfer limit")
        if self.transfer_limit <= 0:
            raise ValueError("Transfer limit must be positive")
        if any(balance < 0 for balance in self.balances.values()):
            raise ValueError("Account balances cannot be negative")

        self.results: dict[str, tuple[tuple, TransferResult]] = {}
        self.lock = Lock()

    @staticmethod
    def _to_decimal(value, label: str) -> Decimal:
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as error:
            raise ValueError(f"{label} must be numeric") from error
        if not result.is_finite():
            raise ValueError(f"{label} must be finite")
        return result

    @staticmethod
    def _request_value(value) -> tuple:
        if isinstance(value, str):
            return ("str", value)
        return (type(value).__name__, repr(value))

    @classmethod
    def _request_fingerprint(cls, account_id, payee_id, amount) -> tuple:
        try:
            parsed_amount = Decimal(str(amount))
            if parsed_amount.is_finite():
                amount_value = ("amount", parsed_amount)
            else:
                amount_value = ("invalid_amount", type(amount).__name__, repr(amount))
        except (InvalidOperation, ValueError, TypeError):
            amount_value = ("invalid_amount", type(amount).__name__, repr(amount))
        return (
            cls._request_value(account_id),
            cls._request_value(payee_id),
            amount_value,
        )

    def _balance_for(self, account_id) -> Decimal:
        if isinstance(account_id, str):
            return self.balances.get(account_id, Decimal("0"))
        return Decimal("0")

    def transfer(
        self,
        account_id: str,
        payee_id: str,
        amount,
        idempotency_key: str,
    ) -> TransferResult:
        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            balance = self._balance_for(account_id)
            return TransferResult("rejected", "Idempotency key is required", balance)

        key = idempotency_key.strip()
        fingerprint = self._request_fingerprint(account_id, payee_id, amount)

        with self.lock:
            previous = self.results.get(key)
            if previous is not None:
                previous_fingerprint, previous_result = previous
                if previous_fingerprint == fingerprint:
                    return previous_result
                return TransferResult(
                    "conflict",
                    "Idempotency key was used for a different transfer",
                    self._balance_for(account_id),
                )

            current_balance = self._balance_for(account_id)

            if not isinstance(account_id, str) or account_id not in self.balances:
                result = TransferResult(
                    "rejected", "Source account not found", Decimal("0")
                )
            elif not isinstance(payee_id, str) or not payee_id.strip():
                result = TransferResult(
                    "rejected", "A valid payee is required", current_balance
                )
            elif any(character.isspace() for character in payee_id):
                result = TransferResult(
                    "rejected", "Payee cannot contain whitespace", current_balance
                )
            elif payee_id == account_id:
                result = TransferResult(
                    "rejected", "Payee cannot be the source account", current_balance
                )
            else:
                try:
                    value = self._to_decimal(amount, "Amount")
                except ValueError:
                    result = TransferResult(
                        "rejected", "Amount must be numeric and finite", current_balance
                    )
                else:
                    if value <= 0:
                        result = TransferResult(
                            "rejected", "Amount must be positive", current_balance
                        )
                    elif value > self.transfer_limit:
                        result = TransferResult(
                            "rejected",
                            "Amount exceeds transfer limit",
                            current_balance,
                        )
                    elif value > current_balance:
                        result = TransferResult(
                            "rejected", "Insufficient funds", current_balance
                        )
                    else:
                        new_balance = current_balance - value
                        result = TransferResult(
                            "accepted",
                            "Transfer accepted",
                            new_balance,
                            reference=f"UPI-{key}",
                        )
                        self.balances[account_id] = new_balance

            self.results[key] = (fingerprint, result)
            return result


if __name__ == "__main__":
    service = TransferService(
        balances={"A100": Decimal("500.00")},
        transfer_limit=Decimal("200.00"),
    )

    first = service.transfer("A100", "B200", "75.00", "retry-001")
    retry = service.transfer("A100", "B200", "75.00", "retry-001")

    print("=== Copilot UPI Transfer Validation Demo ===")
    print(f"Initial balance: {Decimal('500.00')}")
    print(
        f"Transfer result: {first.status.upper()} | "
        f"{first.message} | Balance: {first.balance} | "
        f"Reference: {first.reference}"
    )
    print(
        f"Identical retry: {retry.status.upper()} | "
        f"Same result returned: {retry == first}"
    )
    print(f"Final balance (debited once): {service.balances['A100']}")