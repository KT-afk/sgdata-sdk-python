"""Base response model for all SGData SDK responses."""

from typing import Any, Dict
from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """Base class for all SDK response models.

    All response models expose the original parsed JSON via `.raw`
    as an escape hatch to the underlying dict.
    """

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)

    raw: Dict[str, Any]
