from pydantic import BaseModel


class ProcessOptions(BaseModel):
    language: str = "ja"
    enable_ocr: bool = False
    enable_minutes: bool = False
