from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.models import ProjectBrief, ProjectPlan, Task


class ProjectState(TypedDict, total=False):
    brief: ProjectBrief
    plan: ProjectPlan


def create_project_plan(brief: ProjectBrief) -> ProjectPlan:
    tasks = [
        Task(
            title="Define project requirements",
            description=f"Clarify the requirements for: {brief.goal}",
            priority="high",
            estimated_hours=2.0,
        ),
        Task(
            title="Create project structure",
            description="Set up the folders, files, and development environment.",
            priority="high",
            estimated_hours=2.0,
        ),
        Task(
            title="Build the first working version",
            description=f"Create an initial version of {brief.name}.",
            priority="high",
            estimated_hours=4.0,
            dependencies=["Create project structure"],
        ),
        Task(
            title="Test and review",
            description="Run tests and review the project against its goal.",
            priority="medium",
            estimated_hours=2.0,
            dependencies=["Build the first working version"],
        ),
    ]

    return ProjectPlan(
        project_name=brief.name,
        summary=f"Initial plan for {brief.description}",
        milestones=[
            "Requirements defined",
            "Project structure created",
            "First working version completed",
            "Testing and review completed",
        ],
        tasks=tasks,
        risks=[
            "Requirements may change during development",
            "Tasks may take longer than estimated",
            "Technical issues may require additional research",
        ],
    )


def planning_node(state: ProjectState) -> ProjectState:
    brief = state["brief"]
    plan = create_project_plan(brief)

    return {"plan": plan}


def build_workflow():
    graph = StateGraph(ProjectState)

    graph.add_node("planning", planning_node)

    graph.add_edge(START, "planning")
    graph.add_edge("planning", END)

    return graph.compile()