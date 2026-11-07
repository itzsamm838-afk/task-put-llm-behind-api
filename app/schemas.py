from enum import Enum
from pydantic import BaseModel, Field, field_validator

class Architecture(str, Enum):
    transformer = "transformer"
    convolutional = "convolutional"
    recurrent = "recurrent"
    hybrid = "hybrid"
    other = "other"

class Task(str, Enum):
    emotion_recognition = "emotion_recognition"
    other = "other"

class ExtractRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be blank")
        return value.strip()

class StudyExtraction(BaseModel):
    task: Task
    architecture_family: Architecture
    dataset: str = Field(max_length=120)
    evaluation_metrics: list[str] = Field(max_length=8)
    reported_performance: str = Field(max_length=240)
    evidence_summary: str = Field(min_length=1, max_length=300)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool
