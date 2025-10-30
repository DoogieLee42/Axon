from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = {"DX", "ACT", "DRG"}


class MasterItemRow(BaseModel):
    code: str
    name: str
    category: str
    price: Optional[int] = None
    unit: Optional[str] = None
    raw_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("code", mode="before")
    @classmethod
    def strip_code(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        upper = str(value or "").upper()
        if upper not in VALID_CATEGORIES:
            raise ValueError(f"Unsupported category '{value}'. Expected one of {sorted(VALID_CATEGORIES)}")
        return upper

    @field_validator("unit", mode="before")
    @classmethod
    def normalize_unit(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None
