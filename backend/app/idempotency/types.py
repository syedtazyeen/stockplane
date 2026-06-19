from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.idempotency_record import IdempotencyRecord


@dataclass(frozen=True, slots=True)
class IdempotencyBeginResult:
    """Outcome of reserving or replaying an idempotent request."""

    record: "IdempotencyRecord | None" = None
    replay_status: int | None = None
    replay_body: dict[str, Any] | None = None

    @property
    def is_replay(self) -> bool:
        return self.replay_body is not None
