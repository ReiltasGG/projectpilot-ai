from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from app.models import (
    PlanReview,
    ProjectBrief,
    ProjectPlan,
    RiskAnalysis,
)


class ProjectState(TypedDict, total=False):
    brief: ProjectBrief
    plan: ProjectPlan
    review: PlanReview


llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0,
)


def planning_node(state: ProjectState) -> ProjectState:
    brief = state["brief"]

    structured_llm = llm.with_structured_output(ProjectPlan)

    prompt = f"""
You are an experienced project manager.

Create a practical project plan based on this project brief.

Project name:
{brief.name}

Project description:
{brief.description}

Project goal:
{brief.goal}

Deadline:
{brief.deadline or "Not specified"}

Constraints:
{", ".join(brief.constraints) if brief.constraints else "None specified"}

Create:

- A clear project summary
- Several milestones
- Specific actionable tasks
- A priority for every task
- Estimated hours for every task
- Dependencies when appropriate
- Potential project risks

Keep the scope realistic for an individual developer or small team.
Avoid vague tasks.
"""

    plan = structured_llm.invoke(prompt)

    return {
        "plan": plan
    }


def risk_analysis_node(state: ProjectState) -> ProjectState:
    brief = state["brief"]
    plan = state["plan"]

    structured_llm = llm.with_structured_output(RiskAnalysis)

    task_summary = "\n".join(
        f"- {task.title}: {task.description}"
        for task in plan.tasks
    )

    milestone_summary = "\n".join(
        f"- {milestone}"
        for milestone in plan.milestones
    )

    prompt = f"""
You are a project risk analyst.

Identify realistic and specific risks for this project.

Project name:
{brief.name}

Project description:
{brief.description}

Project goal:
{brief.goal}

Deadline:
{brief.deadline or "Not specified"}

Constraints:
{", ".join(brief.constraints) if brief.constraints else "None specified"}

Project summary:
{plan.summary}

Milestones:
{milestone_summary}

Tasks:
{task_summary}

Consider:

- Scope
- Schedule
- Technical complexity
- Dependencies
- Resources
- Security
- Testing
- Deployment
- Unclear requirements

Return three to six practical risks.
Each risk should be one clear sentence.
"""

    risk_analysis = structured_llm.invoke(prompt)

    plan.risks = risk_analysis.risks

    return {
        "plan": plan
    }


def review_node(state: ProjectState) -> ProjectState:
    brief = state["brief"]
    plan = state["plan"]

    structured_llm = llm.with_structured_output(PlanReview)

    task_summary = "\n".join(
        f"- {task.title}: {task.description}"
        for task in plan.tasks
    )

    milestone_summary = "\n".join(
        f"- {milestone}"
        for milestone in plan.milestones
    )

    risk_summary = "\n".join(
        f"- {risk}"
        for risk in plan.risks
    )

    prompt = f"""
You are a senior project manager reviewing a proposed project plan.

Review the plan for quality, realism, completeness, and consistency.

Original project brief:
Name: {brief.name}
Description: {brief.description}
Goal: {brief.goal}
Deadline: {brief.deadline or "Not specified"}
Constraints: {", ".join(brief.constraints) if brief.constraints else "None specified"}

Project summary:
{plan.summary}

Milestones:
{milestone_summary}

Tasks:
{task_summary}

Risks:
{risk_summary}

Check for:

- Missing or unclear milestones
- Tasks that are too vague
- Tasks that do not support the project goal
- Unrealistic estimates
- Missing dependencies
- Missing risks
- Scope that is too large
- Conflicts with the deadline or constraints

Set approved to true only if the plan is reasonably complete and usable.

If there are problems, list them in issues.
If improvements are useful but not required, list them in recommendations.
"""

    review = structured_llm.invoke(prompt)

    return {
        "review": review
    }


def build_workflow():
    workflow = StateGraph(ProjectState)

    workflow.add_node("planning", planning_node)
    workflow.add_node("risk_analysis", risk_analysis_node)
    workflow.add_node("review", review_node)

    workflow.add_edge(START, "planning")
    workflow.add_edge("planning", "risk_analysis")
    workflow.add_edge("risk_analysis", "review")
    workflow.add_edge("review", END)

    return workflow.compile()