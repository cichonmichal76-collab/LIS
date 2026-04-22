from __future__ import annotations

from fastapi import HTTPException, status


def raise_not_implemented(scope: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            f"{scope} is wired only at the contract layer. "
            "Persistence, state transitions, and audit hooks are the next implementation step."
        ),
    )

