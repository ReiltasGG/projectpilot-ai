
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from app.models import (
    PlanReview,
    ProjectBrief,
    ProjectPlan,
    RiskAnalysis,
)


MAX_REVISIONS = 3
MAX_LLM_RETRIES = 2


class ProjectState(TypedDict, total=False):
    brief: ProjectBrief
    plan: ProjectPlan
    review: PlanReview
    revision_count: int


llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0,
)


def invoke_structured_with_retry(
    output_model,
    prompt: str,
    model=None,
):
    """
    Invoke the LLM with structured output.

    Retry if the model returns invalid structured data
    or the structured-output call raises an exception.

    The model parameter allows tests to inject a fake LLM
    without requiring Ollama to be running.
    """

    if model is None:
        model = llm

    last_error = None

    for attempt in range(MAX_LLM_RETRIES + 1):
        try:
            structured_llm = model.with_structured_output(
                output_model
            )

            return structured_llm.invoke(prompt)

        except Exception as error:
            last_error = error

            if attempt >= MAX_LLM_RETRIES:
                raise RuntimeError(
                    "The local LLM failed to return valid "
                    "structured data after "
                    f"{MAX_LLM_RETRIES + 1} attempts."
                ) from last_error


def create_basic_fallback_plan(brief: ProjectBrief) -> ProjectPlan:
    """
    Create a basic backup plan if the local model returns
    an incomplete project plan.
    """

    return ProjectPlan(
        project_name=brief.name,
        summary=(
            f"Create {brief.name} by breaking the project into "
            "requirements, implementation, testing, and delivery."
        ),
        milestones=[
            "Define project requirements and scope",
            "Design the project structure",
            "Implement the core functionality",
            "Test and improve the project",
            "Document and prepare the final project",
        ],
        tasks=[
            {
                "title": "Define project requirements",
                "description": (
                    "Document the main features, users, inputs, "
                    "outputs, and success criteria."
                ),
                "priority": "high",
                "estimated_hours": 3.0,
                "dependencies": [],
            },
            {
                "title": "Define the technical approach",
                "description": (
                    "Choose the project structure, technologies, "
                    "data storage, and major components."
                ),
                "priority": "high",
                "estimated_hours": 3.0,
                "dependencies": [
                    "Define project requirements",
                ],
            },
            {
                "title": "Implement the core functionality",
                "description": (
                    "Build the main features required to achieve "
                    "the project's primary goal."
                ),
                "priority": "high",
                "estimated_hours": 12.0,
                "dependencies": [
                    "Define the technical approach",
                ],
            },
            {
                "title": "Test the main workflows",
                "description": (
                    "Test the core functionality and fix important "
                    "bugs or incorrect behavior."
                ),
                "priority": "high",
                "estimated_hours": 5.0,
                "dependencies": [
                    "Implement the core functionality",
                ],
            },
            {
                "title": "Write project documentation",
                "description": (
                    "Document setup instructions, features, usage, "
                    "limitations, and future improvements."
                ),
                "priority": "medium",
                "estimated_hours": 3.0,
                "dependencies": [
                    "Test the main workflows",
                ],
            },
        ],
        risks=[
            "The project scope may become larger than the available time.",
            "Technical issues may require additional development time.",
            "Testing and documentation may take longer than expected.",
        ],
    )


def plan_is_incomplete(plan: ProjectPlan) -> bool:
    """
    Determine whether a plan is missing important information.
    """

    return (
        not plan.project_name
        or not plan.summary
        or len(plan.milestones) == 0
        or len(plan.tasks) == 0
    )


def planning_node(state: ProjectState) -> ProjectState:
    """
    Create the initial project plan.
    """

    brief = state["brief"]

    plan = invoke_structured_with_retry(
        ProjectPlan,
        f"""
You are an experienced project manager.

Create a complete, practical project plan from this brief.

Project name:
{brief.name}

Description:
{brief.description}

Goal:
{brief.goal}

Deadline:
{brief.deadline or "Not specified"}

Constraints:
{brief.constraints or "None specified"}

IMPORTANT REQUIREMENTS:

- Return at least 5 milestones.
- Return at least 5 actionable tasks.
- Every task must have a title.
- Every task must have a useful description.
- Every task must have a priority.
- Every task must have an estimated number of hours.
- Include dependencies when appropriate.
- Include at least 3 specific risks.
- Do not leave milestones or tasks empty.
- Do not return a partial plan.

The plan should be realistic for the deadline and constraints.
""",
    )

    if plan_is_incomplete(plan):
        plan = create_basic_fallback_plan(brief)

    return {
        "plan": plan,
        "revision_count": state.get("revision_count", 0),
    }


def risk_analysis_node(state: ProjectState) -> ProjectState:
    """
    Analyze the current plan and identify risks.
    """

    brief = state["brief"]
    plan = state["plan"]

    risk_result = invoke_structured_with_retry(
        RiskAnalysis,
        f"""
You are a project risk analyst.

Project brief:

{brief.model_dump_json(indent=2)}

Project plan:

{plan.model_dump_json(indent=2)}

Identify 3 to 6 specific risks related to this project.

Consider:

- Deadline risk
- Scope risk
- Technical risk
- Resource risk
- Dependency risk
- Quality risk
- Unclear requirements
- Project constraints

Do not return an empty list.
Do not use generic wording when a project-specific risk can be identified.
""",
    )

    risks = risk_result.risks

    if not risks:
        risks = [
            "The project scope may become larger than the available time.",
            "Technical issues may require additional development time.",
            "Testing and documentation may take longer than expected.",
        ]

    updated_plan = plan.model_copy(
        update={
            "risks": risks,
        }
    )

    return {
        "plan": updated_plan,
    }


def review_node(state: ProjectState) -> ProjectState:
    """
    Review the current project plan.
    """

    brief = state["brief"]
    plan = state["plan"]

    review = invoke_structured_with_retry(
        PlanReview,
        f"""
You are a senior project manager reviewing a project plan.

Project brief:

{brief.model_dump_json(indent=2)}

Project plan:

{plan.model_dump_json(indent=2)}

Review the plan for:

1. Completeness
2. Realistic milestones
3. Actionable tasks
4. Clear priorities
5. Reasonable time estimates
6. Logical dependencies
7. Alignment with the project goal
8. Respect for constraints
9. Specific risks
10. Deadline feasibility

Approve the plan if it is reasonably clear, actionable, and realistic.

Only reject the plan for meaningful problems.
Do not reject the plan for minor wording preferences.

If approved:
- Set approved to true.
- Issues may be empty.
- Recommendations may contain optional future improvements.

If not approved:
- Set approved to false.
- List specific issues.
- List practical recommendations for fixing those issues.
""",
    )

    if not review.approved and not review.recommendations:
        review = review.model_copy(
            update={
                "recommendations": [
                    "Review the milestones and tasks for completeness.",
                    "Confirm that the estimated hours fit the deadline.",
                    "Check that the project constraints are reflected in the plan.",
                ]
            }
        )

    return {
        "review": review,
    }


def revision_node(state: ProjectState) -> ProjectState:
    """
    Revise the plan based on review feedback.
    """

    brief = state["brief"]
    current_plan = state["plan"]
    review = state["review"]

    current_revision_count = state.get("revision_count", 0)
    next_revision_count = current_revision_count + 1

    revised_plan = invoke_structured_with_retry(
        ProjectPlan,
        f"""
You are an experienced project manager revising a project plan.

Project brief:

{brief.model_dump_json(indent=2)}

Current project plan:

{current_plan.model_dump_json(indent=2)}

Review issues:

{review.issues}

Review recommendations:

{review.recommendations}

Create a complete revised project plan.

IMPORTANT REQUIREMENTS:

- Return the complete plan, not a partial plan.
- Preserve the existing project name.
- Preserve the useful summary.
- Include at least 5 milestones.
- Include at least 5 actionable tasks.
- Every task needs a title.
- Every task needs a description.
- Every task needs a priority.
- Every task needs an estimated number of hours.
- Include dependencies where appropriate.
- Include at least 3 risks.
- Do not return empty milestones or tasks.
- Address the review issues and recommendations.
""",
    )

    # Do not allow an incomplete revision to destroy a usable plan.
    if plan_is_incomplete(revised_plan):
        revised_plan = current_plan

    return {
        "plan": revised_plan,
        "revision_count": next_revision_count,
    }


def route_after_review(state: ProjectState) -> str:
    """
    Decide whether to finish or perform another revision.
    """

    review = state.get("review")
    revision_count = state.get("revision_count", 0)

    if review and review.approved:
        return "finish"

    if revision_count >= MAX_REVISIONS:
        return "finish"

    return "revise"


def build_workflow():
    """
    Build and compile the ProjectPilot AI workflow.
    """

    workflow = StateGraph(ProjectState)

    workflow.add_node("planning", planning_node)
    workflow.add_node("risk_analysis", risk_analysis_node)
    workflow.add_node("review", review_node)
    workflow.add_node("revision", revision_node)

    workflow.add_edge(START, "planning")
    workflow.add_edge("planning", "risk_analysis")
    workflow.add_edge("risk_analysis", "review")

    workflow.add_conditional_edges(
        "review",
        route_after_review,
        {
            "revise": "revision",
            "finish": END,
        },
    )

    workflow.add_edge("revision", "risk_analysis")

    return workflow.compile()