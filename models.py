from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class Seniority(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    UNKNOWN = "unknown"


class MappingMethod(str, Enum):
    RAG = "rag"
    EXACT_MATCH = "exact_match"
    UNRESOLVED = "unresolved"

class RetrievedCandidate(BaseModel):
    occupation_title: str
    job_title: str

    distance: float = Field(ge=0)


class RetrievalResult(BaseModel):
    raw_title: str
    candidates: list[RetrievedCandidate] = Field(
        default_factory=list
    )

class HarmonizationResult(BaseModel):
    canonical_title: str | None = None

    seniority: Seniority = Seniority.UNKNOWN

    confidence: float = Field(
        ge=0,
        le=1
    )

    mapping_method: MappingMethod

    reasoning: str | None = None

class SkillInput(BaseModel):
    raw_skill: str = Field(min_length=1)

class RetrievedSkillCandidate(BaseModel):
    preferred_label: str

    distance: float = Field(ge=0)


class SkillRetrievalResult(BaseModel):
    raw_skill: str

    candidates: list[RetrievedSkillCandidate] = Field(
        default_factory=list
    )

class SkillHarmonizationResult(BaseModel):
    raw_skill: str

    canonical_skill: str | None = None

    confidence: float = Field(
        ge=0,
        le=1
    )

    mapping_method: MappingMethod

class JobPosting(BaseModel):
    job_id: str

    raw_title: str
    canonical_title: str | None = None

    seniority: Seniority = Seniority.UNKNOWN

    skills: list[SkillHarmonizationResult] = Field(
        default_factory=list
    )