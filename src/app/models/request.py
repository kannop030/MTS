from pydantic import BaseModel
from typing import Literal


class ProcessOptions(BaseModel):
    language: str = "ja"
    mode: Literal["transcribe_only", "extract_only", "full"] = "full"
