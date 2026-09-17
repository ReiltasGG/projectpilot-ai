from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from app.models import ProjectBrief, ProjectPlan, RiskAnalysis


class ProjectState(TypedDict, total=False):
    brief: ProjectBrief
    plan: ProjectPlan


# Local LLM configuration
llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0,
)


def planning_node(state: ProjectState) -> ProjectState:
    brief = state["brief"]

    structured_llm = llm.with_structured_output(ProjectPlan)

    prompt = f"""
You are an experienced project manager.

Create a practical project plan based on the following project brief.

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

Create a realistic plan with:

- A clear project summary
- Several milestones
- Specific actionable tasks
- A priority for every task
- Estimated hours for every task
- Dependencies between tasks when appropriate
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

Analyze the following project and identify realistic, specific risks.

PROJECT BRIEF

Name:
{brief.name}

Description:
{brief.description}

Goal:
{brief.goal}

Deadline:
{brief.deadline or "Not specified"}

Constraints:
{", ".join(brief.constraints) if brief.constraints else "None specified"}


PROJECT PLAN

Summary:
{plan.summary}

Milestones:
{milestone_summary}

Tasks:
{task_summary}

Identify risks related to areas such as:

- Scope
- Schedule
- Technical complexity
- Dependencies
- Resources
- Security
- Testing
- Deployment
- Unclear requirements

Return only practical risks that are relevant to this specific project.

For each risk, write one clear sentence.
Return between three and six risks.
"""

    risk_analysis = structured_llm.invoke(prompt)

    plan.risks = risk_analysis.risks

    return {
        "plan": plan
    }


def review_node(state: ProjectState) -> ProjectState:
    plan = state["plan"]

    review_notes = []

    if not plan.project_name.strip():
        review_notes.append("The project is missing a name.")

    if not plan.summary.strip():
        review_notes.append("The project is missing a summary.")

    if not plan.milestones:
        review_notes.append("The project has no milestones.")

    if not plan.tasks:
        review_notes.append("The project has no tasks.")

    if not plan.risks:
        review_notes.append("The project has no identified risks.")

    if review_notes:
        plan.risks.extend(review_notes)

    return {
        "plan": plan
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