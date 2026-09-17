from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectBrief(BaseModel):
    name: str
    description: str
    goal: str
    deadline: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)


class Task(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    estimated_hours: float = 1.0
    dependencies: List[str] = Field(default_factory=list)


class ProjectPlan(BaseModel):
    project_name: str
    summary: str
    milestones: List[str] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class RiskAnalysis(BaseModel):
    risks: List[str] = Field(default_factory=list)


class PlanReview(BaseModel):
    approved: bool = False
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)