import streamlit as st

from app.models import ProjectBrief
from app.workflow import build_workflow


st.set_page_config(
    page_title="ProjectPilot AI",
    page_icon="📋",
    layout="wide",
)

st.title("ProjectPilot AI")
st.write("Turn a project idea into an organized project plan.")

if "plan" not in st.session_state:
    st.session_state.plan = None

if "approved" not in st.session_state:
    st.session_state.approved = False


project_name = st.text_input(
    "Project name",
    placeholder="Example: AI Resume Analyzer",
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
    "Deadline (optional)",
    placeholder="Example: December 2026",
)

constraints_text = st.text_area(
    "Constraints (optional)",
    placeholder="Enter one constraint per line.",
)


if st.button("Generate Project Plan", type="primary"):
    if not project_name or not description or not goal:
        st.error("Please complete the project name, description, and goal.")
    else:
        brief = ProjectBrief(
            name=project_name,
            description=description,
            goal=goal,
            deadline=deadline or None,
            constraints=[
                item.strip()
                for item in constraints_text.splitlines()
                if item.strip()
            ],
        )

        workflow = build_workflow()
        result = workflow.invoke({"brief": brief})

        st.session_state.plan = result["plan"]
        st.session_state.approved = False


plan = st.session_state.plan

if plan is not None:
    st.success("Project plan generated!")

    st.subheader("Project Summary")
    st.write(plan.summary)

    st.subheader("Milestones")

    for milestone in plan.milestones:
        st.write(f"• {milestone}")

    st.subheader("Tasks")

    for index, task in enumerate(plan.tasks, start=1):
        with st.expander(f"{index}. {task.title}"):
            st.write(task.description)
            st.write(f"**Priority:** {task.priority}")
            st.write(f"**Estimated hours:** {task.estimated_hours}")
            st.write(
                f"**Dependencies:** "
                f"{', '.join(task.dependencies) or 'None'}"
            )

    st.subheader("Risks")

    for risk in plan.risks:
        st.warning(risk)

    st.divider()

    st.subheader("Human Approval")

    if not st.session_state.approved:
        st.info("Review the plan above before approving it.")

        if st.button("Approve Project Plan"):
            st.session_state.approved = True
            st.rerun()
    else:
        st.success("Project plan approved by the user.")

        st.download_button(
            label="Download Approved Plan as JSON",
            data=plan.model_dump_json(indent=2),
            file_name="approved_project_plan.json",
            mime="application/json",
        )

        if st.button("Revoke Approval"):
            st.session_state.approved = False
            st.rerun()