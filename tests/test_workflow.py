from app import workflow
from app.models import (
    PlanReview,
    ProjectBrief,
    ProjectPlan,
    RiskAnalysis,
    Task,
)


class FakeWorkflowModel:
    """
    Fake model for testing the workflow without Ollama.

    It returns predictable Pydantic models based on the requested
    structured output type.
    """

    def __init__(self, review_results=None):
        self.review_results = review_results or [
            PlanReview(
                approved=True,
                issues=[],
                recommendations=[],
            )
        ]
        self.review_index = 0
        self.invoke_count = 0

    def with_structured_output(self, output_model):
        self.output_model = output_model
        return self

    def invoke(self, prompt):
        self.invoke_count += 1

        if self.output_model is ProjectPlan:
            return ProjectPlan(
                project_name="Test Project",
                summary="A complete test project plan.",
                milestones=[
                    "Define requirements",
                    "Design solution",
                    "Build core features",
                    "Test the system",
                    "Document and deliver",
                ],
                tasks=[
                    Task(
                        title="Define requirements",
                        description="Document project requirements.",
                        priority="high",
                        estimated_hours=3.0,
                        dependencies=[],
                    ),
                    Task(
                        title="Design solution",
                        description="Create the technical design.",
                        priority="high",
                        estimated_hours=4.0,
                        dependencies=["Define requirements"],
                    ),
                    Task(
                        title="Build core features",
                        description="Implement the main functionality.",
                        priority="high",
                        estimated_hours=12.0,
                        dependencies=["Design solution"],
                    ),
                    Task(
                        title="Test the system",
                        description="Test the main workflows.",
                        priority="high",
                        estimated_hours=5.0,
                        dependencies=["Build core features"],
                    ),
                    Task(
                        title="Document and deliver",
                        description="Write documentation and prepare delivery.",
                        priority="medium",
                        estimated_hours=3.0,
                        dependencies=["Test the system"],
                    ),
                ],
                risks=[
                    "The project may take longer than expected.",
                    "Technical issues may delay implementation.",
                    "Testing may reveal additional work.",
                ],
            )

        if self.output_model is RiskAnalysis:
            return RiskAnalysis(
                risks=[
                    "The deadline may be difficult to meet.",
                    "Technical implementation may take longer than expected.",
                    "Testing may identify additional defects.",
                ]
            )

        if self.output_model is PlanReview:
            review = self.review_results[self.review_index]

            if self.review_index < len(self.review_results) - 1:
                self.review_index += 1

            return review

        raise AssertionError(
            f"Unexpected structured output model: {self.output_model}"
        )


def create_test_brief():
    return ProjectBrief(
        name="Test Project",
        description="A project used to test the workflow.",
        goal="Verify that the workflow behaves correctly.",
        deadline="2 weeks",
        constraints=["Use a small team"],
    )


def test_workflow_finishes_when_plan_is_approved(monkeypatch):
    """
    The workflow should finish when the reviewer approves the plan.
    """

    fake_model = FakeWorkflowModel()

    monkeypatch.setattr(workflow, "llm", fake_model)

    app = workflow.build_workflow()

    result = app.invoke(
        {
            "brief": create_test_brief(),
        }
    )

    assert "plan" in result
    assert "review" in result

    assert result["plan"].project_name == "Test Project"
    assert len(result["plan"].milestones) >= 5
    assert len(result["plan"].tasks) >= 5
    assert len(result["plan"].risks) >= 3

    assert result["review"].approved is True
    assert result.get("revision_count", 0) == 0


def test_workflow_revises_rejected_plan(monkeypatch):
    """
    The workflow should perform a revision when the first review
    rejects the plan, then finish after the second review approves it.
    """

    fake_model = FakeWorkflowModel(
        review_results=[
            PlanReview(
                approved=False,
                issues=["The schedule needs more detail."],
                recommendations=[
                    "Add clearer task sequencing.",
                ],
            ),
            PlanReview(
                approved=True,
                issues=[],
                recommendations=[],
            ),
        ]
    )

    monkeypatch.setattr(workflow, "llm", fake_model)

    app = workflow.build_workflow()

    result = app.invoke(
        {
            "brief": create_test_brief(),
        }
    )

    assert "plan" in result
    assert "review" in result

    assert result["review"].approved is True
    assert result["revision_count"] == 1
    assert fake_model.review_index == 1


def test_plan_is_incomplete_detects_missing_information():
    """
    The completeness helper should detect missing plan information.
    """

    incomplete_plan = ProjectPlan(
        project_name="",
        summary="",
        milestones=[],
        tasks=[],
        risks=[],
    )

    complete_plan = ProjectPlan(
        project_name="Complete Project",
        summary="A complete project.",
        milestones=["Milestone 1"],
        tasks=[
            Task(
                title="Task 1",
                description="Complete task 1.",
            )
        ],
        risks=["A project risk."],
    )

    assert workflow.plan_is_incomplete(incomplete_plan) is True
    assert workflow.plan_is_incomplete(complete_plan) is False