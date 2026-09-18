import json

import streamlit as st

from app.models import ProjectBrief
from app.workflow import MAX_REVISIONS, build_workflow


st.set_page_config(
    page_title="ProjectPilot AI",
    page_icon="🚀",
    layout="wide",
)


def plan_to_markdown(plan) -> str:
    """
    Convert a ProjectPlan into Markdown format.
    """

    lines = [
        f"# {plan.project_name}",
        "",
        "## Summary",
        plan.summary,
        "",
        "## Milestones",
    ]

    for index, milestone in enumerate(plan.milestones, start=1):
        lines.append(f"{index}. {milestone}")

    lines.extend(
        [
            "",
            "## Tasks",
            "",
        ]
    )

    for index, task in enumerate(plan.tasks, start=1):
        lines.extend(
            [
                f"### {index}. {task.title}",
                "",
                f"**Description:** {task.description}",
                "",
                f"**Priority:** {task.priority}",
                "",
                f"**Estimated hours:** {task.estimated_hours}",
                "",
            ]
        )

        if task.dependencies:
            lines.append(
                f"**Dependencies:** {', '.join(task.dependencies)}"
            )
        else:
            lines.append("**Dependencies:** None")

        lines.append("")

    lines.append("## Risks")
    lines.append("")

    if plan.risks:
        for risk in plan.risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- No risks were identified.")

    lines.append("")

    return "\n".join(lines)


st.title("🚀 ProjectPilot AI")

st.write(
    "Turn a project idea into a structured project plan with "
    "milestones, tasks, risks, automated review, and human approval."
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "plan" not in st.session_state:
    st.session_state.plan = None

if "review" not in st.session_state:
    st.session_state.review = None

if "approved" not in st.session_state:
    st.session_state.approved = False

if "rejected" not in st.session_state:
    st.session_state.rejected = False

if "revision_count" not in st.session_state:
    st.session_state.revision_count = 0


# ---------------------------------------------------------
# Project brief input
# ---------------------------------------------------------

st.header("1. Project Brief")

project_name = st.text_input(
    "Project name",
    placeholder="Example: Personal Finance Dashboard",
)

description = st.text_area(
    "Project description",
    placeholder="Describe what you want to build.",
)

goal = st.text_area(
    "Project goal",
    placeholder="What should this project accomplish?",
)

deadline = st.text_input(
    "Deadline",
    placeholder="Example: 4 weeks, October 30, or leave blank",
)

constraints_text = st.text_area(
    "Constraints",
    placeholder=(
        "Enter one constraint per line.\n"
        "Example:\n"
        "Must use Python\n"
        "Solo developer\n"
        "Limited budget"
    ),
)

constraints = [
    constraint.strip()
    for constraint in constraints_text.splitlines()
    if constraint.strip()
]


# ---------------------------------------------------------
# Generate project plan
# ---------------------------------------------------------

if st.button(
    "Generate Project Plan",
    type="primary",
    use_container_width=True,
):
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

        try:
            with st.spinner(
                "Creating, reviewing, and revising your project plan..."
            ):
                result = workflow.invoke(
                    {
                        "brief": brief,
                        "revision_count": 0,
                    }
                )

        except RuntimeError as error:
            st.error(
                "The local LLM could not generate a plan. "
                "Make sure Ollama is running and the "
                "llama3.2:3b model is pulled, then try again.\n\n"
                f"Details: {error}"
            )

        else:
            st.session_state.plan = result.get("plan")
            st.session_state.review = result.get("review")
            st.session_state.revision_count = result.get(
                "revision_count",
                0,
            )
            st.session_state.approved = False
            st.session_state.rejected = False

            if st.session_state.plan is not None:
                st.success("Project plan generated successfully.")
            else:
                st.error("The workflow did not return a project plan.")


# ---------------------------------------------------------
# Display project plan
# ---------------------------------------------------------

if st.session_state.plan is not None:
    plan = st.session_state.plan
    review = st.session_state.review

    st.divider()
    st.header("2. Generated Project Plan")

    st.subheader("Summary")
    st.write(plan.summary)

    st.subheader("Milestones")

    if plan.milestones:
        for index, milestone in enumerate(
            plan.milestones,
            start=1,
        ):
            st.write(f"{index}. {milestone}")
    else:
        st.info("No milestones were generated.")

    st.subheader("Tasks")

    if plan.tasks:
        for index, task in enumerate(
            plan.tasks,
            start=1,
        ):
            with st.expander(
                f"{index}. {task.title}",
                expanded=False,
            ):
                st.write(task.description)

                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        f"**Priority:** {task.priority}"
                    )

                with col2:
                    st.write(
                        f"**Estimated hours:** "
                        f"{task.estimated_hours}"
                    )

                if task.dependencies:
                    st.write(
                        "**Dependencies:** "
                        f"{', '.join(task.dependencies)}"
                    )
                else:
                    st.write("**Dependencies:** None")
    else:
        st.info("No tasks were generated.")

    st.subheader("Risks")

    if plan.risks:
        for risk in plan.risks:
            st.warning(risk)
    else:
        st.info(
            "No risks were returned by the risk analysis step."
        )

    # -----------------------------------------------------
    # Automated revision status
    # -----------------------------------------------------

    st.divider()
    st.header("3. Automated Revision Status")

    revision_count = st.session_state.revision_count

    st.write(
        f"Revision attempts used: "
        f"**{revision_count} / {MAX_REVISIONS}**"
    )

    if review is not None:
        if review.approved:
            st.success(
                "The automated review approved this plan. "
                "Human approval is still required."
            )

        elif revision_count >= MAX_REVISIONS:
            st.warning(
                "The maximum number of automated revisions has "
                "been reached. Please review the plan manually "
                "before approving or rejecting it."
            )

        else:
            st.info(
                "The automated review did not approve the plan."
            )
    else:
        st.warning(
            "No automated review was returned."
        )

    # -----------------------------------------------------
    # Automated plan review
    # -----------------------------------------------------

    st.header("4. Automated Plan Review")

    if review is not None:
        approval_text = (
            "Approved"
            if review.approved
            else "Not approved"
        )

        st.write(
            f"**Automated approval:** {approval_text}"
        )

        st.subheader("Issues")

        if review.issues:
            for issue in review.issues:
                st.write(f"- {issue}")
        else:
            st.write("No issues identified.")

        st.subheader("Recommendations")

        if review.recommendations:
            for recommendation in review.recommendations:
                st.write(f"- {recommendation}")
        else:
            st.write("No recommendations provided.")

    else:
        st.info(
            "The automated review information is unavailable."
        )

    # -----------------------------------------------------
    # Human approval
    # -----------------------------------------------------

    st.divider()
    st.header("5. Human Approval")

    st.write(
        "Review the generated plan carefully. "
        "The automated review is advisory and does not replace "
        "your judgment."
    )

    if (
        not st.session_state.approved
        and not st.session_state.rejected
    ):
        approve_col, reject_col = st.columns(2)

        with approve_col:
            if st.button(
                "Approve Plan",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.approved = True
                st.session_state.rejected = False
                st.rerun()

        with reject_col:
            if st.button(
                "Reject Plan",
                use_container_width=True,
            ):
                st.session_state.approved = False
                st.session_state.rejected = True
                st.rerun()

    elif st.session_state.approved:
        st.success(
            "This plan has been approved by a human."
        )

        if st.button(
            "Revoke Approval",
            use_container_width=True,
        ):
            st.session_state.approved = False
            st.session_state.rejected = False
            st.rerun()

    elif st.session_state.rejected:
        st.error(
            "This plan has been rejected."
        )

        st.write(
            "You can generate a new plan or reconsider "
            "this plan."
        )

        if st.button(
            "Reconsider Plan",
            use_container_width=True,
        ):
            st.session_state.rejected = False
            st.rerun()

    # -----------------------------------------------------
    # Export options
    # -----------------------------------------------------

    if st.session_state.approved:
        st.divider()
        st.header("6. Export Plan")

        plan_json = json.dumps(
            plan.model_dump(),
            indent=2,
        )

        plan_markdown = plan_to_markdown(plan)

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="Download JSON",
                data=plan_json,
                file_name="project_plan.json",
                mime="application/json",
                use_container_width=True,
            )

        with col2:
            st.download_button(
                label="Download Markdown",
                data=plan_markdown,
                file_name="project_plan.md",
                mime="text/markdown",
                use_container_width=True,
            )