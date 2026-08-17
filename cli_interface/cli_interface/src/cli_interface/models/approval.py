from dataclasses import dataclass, asdict
from typing import Dict, Any, Literal, Optional
from uuid import UUID


@dataclass
class Approval:
    def __init__(
            self,
            id_: UUID,
            type_: Literal["file", "directory", "command"],
            user: Optional[str],
            path: Optional[str],
            command: Optional[str],
            created_at: float,
            approved: Optional[bool] = None
    ):
        self.id_ = id_
        self.type_ = type_
        self.user = user
        self.path = path
        self.command = command
        self.created_at = created_at
        self.approved = approved

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            id_=data.get("id_") or data.get("id"),
            type_=data.get("type_") or data.get("type"),
            user=data.get("user"),
            path=data.get("path"),
            command=data.get("command"),
            created_at=data.get("created_at"),
            approved=data.get("approved")
        )

    def to_dict(self):
        # TODO: If possible handle the id_ to str(UUID)
        pre_dict = asdict(self)
        id_ = pre_dict["id_"]
        id_ = str(id_)
        pre_dict["id_"] = id_
