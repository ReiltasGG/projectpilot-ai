from app.models import ProjectBrief, ProjectPlan, Task


def test_project_brief_creation():
    project = ProjectBrief(
        name="ProjectPilot AI",
        description="An AI project management assistant",
        goal="Turn project ideas into organized plans",
    )

    assert project.name == "ProjectPilot AI"
    assert project.goal == "Turn project ideas into organized plans"


def test_task_defaults():
    task = Task(
        title="Create project structure",
        description="Set up the initial application files",
    )

    assert task.priority == "medium"
    assert task.estimated_hours == 1.0


def test_project_plan_creation():
    plan = ProjectPlan(
        project_name="ProjectPilot AI",
        summary="Initial project plan",
    )

    assert plan.project_name == "ProjectPilot AI"
    assert plan.tasks == []