from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def test_llm_failure_shows_error_instead_of_crashing():
    """
    If workflow.invoke() raises RuntimeError (e.g. Ollama isn't
    running), the app should show st.error and keep running,
    not crash with an unhandled exception.
    """

    at = AppTest.from_file("../app/main.py")
    at.run()

    at.text_input[0].input("Test Project")
    at.text_area[0].input("A test description")
    at.text_area[1].input("A test goal")

    with patch(
        "app.main.build_workflow"
    ) as mock_build_workflow:
        mock_build_workflow.return_value.invoke.side_effect = (
            RuntimeError("The local LLM failed to return valid data.")
        )

        at.button[0].click().run()

    assert not at.exception
    assert any(
        "could not generate a plan" in error.value
        for error in at.error
    )