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
    def __init__(self, balances: dict[str, Decimal], transfer_limit: Decimal):
        self.balances = balances.copy()
        self.transfer_limit = transfer_limit
        self.results = {}
        self.lock = Lock()

    def transfer(
        self,
        account_id: str,
        payee_id: str,
        amount,
        idempotency_key: str,
    ) -> TransferResult:
        current_balance = self.balances.get(account_id, Decimal("0"))

        if not isinstance(idempotency_key, str) or not idempotency_key.strip():
            return TransferResult("rejected", "Idempotency key is required", current_balance)

        try:
            value = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return TransferResult("rejected", "Amount must be numeric", current_balance)

        if not value.is_finite() or value <= 0:
            return TransferResult("rejected", "Amount must be positive", current_balance)

        if value > self.transfer_limit:
            return TransferResult("rejected", "Amount exceeds transfer limit", current_balance)

        if account_id not in self.balances:
            return TransferResult("rejected", "Source account not found", Decimal("0"))

        if not payee_id or payee_id == account_id:
            return TransferResult("rejected", "A different valid payee is required", current_balance)

        request = (account_id, payee_id, value)

        with self.lock:
            previous = self.results.get(idempotency_key)

            if previous:
                old_request, old_result = previous

                if old_request != request:
                    return TransferResult(
                        "conflict",
                        "Idempotency key was used for a different transfer",
                        self.balances[account_id],
                    )

                # Same key and same request: return the stored result.
                # No second debit occurs.
                return old_result

            current_balance = self.balances[account_id]

            if value > current_balance:
                return TransferResult("rejected", "Insufficient funds", current_balance)

            new_balance = current_balance - value
            result = TransferResult(
                "accepted",
                "Transfer accepted",
                new_balance,
                reference=f"UPI-{idempotency_key}",
            )

            self.balances[account_id] = new_balance
            self.results[idempotency_key] = (request, result)
            return result


if __name__ == "__main__":
    service = TransferService(
        balances={"A100": Decimal("500.00")},
        transfer_limit=Decimal("200.00"),
    )

    first = service.transfer("A100", "B200", "75.00", "retry-001")
    retry = service.transfer("A100", "B200", "75.00", "retry-001")

    print("First request:", first)
    print("Retry:", retry)
    print("Final balance:", service.balances["A100"])