import streamlit as st

from app.models import ProjectBrief
from app.workflow import build_workflow


def plan_to_markdown(plan) -> str:
    milestones = "\n".join(
        f"- {milestone}"
        for milestone in plan.milestones
    )

    tasks = "\n".join(
        f"- **{task.title}**\n"
        f"  - Description: {task.description}\n"
        f"  - Priority: {task.priority}\n"
        f"  - Estimated hours: {task.estimated_hours}\n"
        f"  - Dependencies: {', '.join(task.dependencies) or 'None'}"
        for task in plan.tasks
    )

    risks = "\n".join(
        f"- {risk}"
        for risk in plan.risks
    )

    return f"""# {plan.project_name}

## Summary

{plan.summary}

## Milestones

{milestones}

## Tasks

{tasks}

## Risks

{risks}
"""


st.set_page_config(
    page_title="ProjectPilot AI",
    page_icon="🚀",
    layout="wide",
)


st.title("🚀 ProjectPilot AI")

st.write(
    "Turn a project idea into a structured project plan with "
    "milestones, tasks, dependencies, risks, and automated review."
)


# Initialize session state
if "plan" not in st.session_state:
    st.session_state.plan = None

if "review" not in st.session_state:
    st.session_state.review = None

if "approved" not in st.session_state:
    st.session_state.approved = False


# ---------------------------------------------------------
# Project Brief
# ---------------------------------------------------------

st.header("1. Project Brief")

project_name = st.text_input(
    "Project Name",
    placeholder="Example: Personal Portfolio Website",
)

description = st.text_area(
    "Project Description",
    placeholder="Describe what the project is about.",
)

goal = st.text_area(
    "Project Goal",
    placeholder="What should this project accomplish?",
)

deadline = st.text_input(
    "Deadline",
    placeholder="Example: December 2026",
)

constraints_text = st.text_area(
    "Constraints",
    placeholder="Enter one constraint per line.",
)

constraints = [
    constraint.strip()
    for constraint in constraints_text.splitlines()
    if constraint.strip()
]


# ---------------------------------------------------------
# Generate Project Plan
# ---------------------------------------------------------

st.header("2. Generate Project Plan")

if st.button("Generate Project Plan", type="primary"):
    if not project_name.strip():
        st.error("Please enter a project name.")

    elif not description.strip():
        st.error("Please enter a project description.")

    elif not goal.strip():
        st.error("Please enter the project goal.")

    else:
        brief = ProjectBrief(
            name=project_name.strip(),
            description=description.strip(),
            goal=goal.strip(),
            deadline=deadline.strip() or None,
            constraints=constraints,
        )

        workflow = build_workflow()

        with st.spinner(
            "Generating project plan, analyzing risks, and reviewing the plan..."
        ):
            result = workflow.invoke(
                {
                    "brief": brief,
                }
            )

        st.session_state.plan = result["plan"]
        st.session_state.review = result.get("review")
        st.session_state.approved = False

        st.success("Project plan generated successfully!")


# ---------------------------------------------------------
# Display Generated Project Plan
# ---------------------------------------------------------

if st.session_state.plan is not None:
    plan = st.session_state.plan

    st.header("3. Generated Project Plan")

    st.subheader("Project Summary")
    st.write(plan.summary)

    # -----------------------------------------------------
    # Milestones
    # -----------------------------------------------------

    st.subheader("Milestones")

    if plan.milestones:
        for milestone in plan.milestones:
            st.write(f"✅ {milestone}")
    else:
        st.info("No milestones were generated.")

    # -----------------------------------------------------
    # Tasks
    # -----------------------------------------------------

    st.subheader("Tasks")

    if plan.tasks:
        for index, task in enumerate(plan.tasks, start=1):
            with st.expander(f"{index}. {task.title}"):
                st.write(f"**Description:** {task.description}")
                st.write(f"**Priority:** {task.priority}")
                st.write(
                    f"**Estimated Hours:** {task.estimated_hours}"
                )

                if task.dependencies:
                    st.write(
                        f"**Dependencies:** "
                        f"{', '.join(task.dependencies)}"
                    )
                else:
                    st.write("**Dependencies:** None")
    else:
        st.info("No tasks were generated.")

    # -----------------------------------------------------
    # Risks
    # -----------------------------------------------------

    st.subheader("Risks")

    if plan.risks:
        for risk in plan.risks:
            st.warning(risk)
    else:
        st.info("No risks were identified.")

    # -----------------------------------------------------
    # Automated Plan Review
    # -----------------------------------------------------

    st.subheader("Automated Plan Review")

    review = st.session_state.review

    if review is not None:
        if review.approved:
            st.success(
                "The review agent found the plan reasonably complete."
            )
        else:
            st.warning(
                "The review agent found issues with this plan."
            )

        if review.issues:
            st.write("**Issues:**")

            for issue in review.issues:
                st.error(issue)

        if review.recommendations:
            st.write("**Recommendations:**")

            for recommendation in review.recommendations:
                st.info(recommendation)

        if not review.issues and not review.recommendations:
            st.write(
                "The review agent did not identify any additional issues "
                "or recommendations."
            )
    else:
        st.info("No automated review is available.")

    # -----------------------------------------------------
    # Human Approval
    # -----------------------------------------------------

    st.header("4. Human Approval")

    if not st.session_state.approved:
        st.write(
            "Review the generated project plan and automated review. "
            "Approve the plan when you are satisfied with the results."
        )

        if st.button("Approve Project Plan"):
            st.session_state.approved = True
            st.rerun()

    else:
        st.success("Project plan approved by the user.")

        # -------------------------------------------------
        # JSON Export
        # -------------------------------------------------

        st.download_button(
            label="Download Approved Plan as JSON",
            data=plan.model_dump_json(indent=2),
            file_name="approved_project_plan.json",
            mime="application/json",
        )

        # -------------------------------------------------
        # Markdown Export
        # -------------------------------------------------

        markdown_plan = plan_to_markdown(plan)

        st.download_button(
            label="Download Approved Plan as Markdown",
            data=markdown_plan,
            file_name="approved_project_plan.md",
            mime="text/markdown",
        )

        # -------------------------------------------------
        # Revoke Approval
        # -------------------------------------------------

        if st.button("Revoke Approval"):
            st.session_state.approved = False
            st.rerun()