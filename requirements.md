# Transfer Validation Requirements

- R1: Accept only finite, positive amounts at or below the configured per-transfer limit.
- R2: Require a known source account and a valid payee different from the source.
- R3: Reject transfers when the available balance is insufficient.
- R4: An identical retry with the same idempotency key must not debit twice.
- R5: Reusing a key for different transfer details must return a conflict.
