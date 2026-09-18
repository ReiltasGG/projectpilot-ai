import pytest

from app.workflow import (
    MAX_LLM_RETRIES,
    invoke_structured_with_retry,
)


class FakeStructuredModel:
    """
    Fake model used to test retry behavior.

    It fails a configurable number of times, then returns
    a successful result.
    """

    def __init__(self, failures_before_success=0):
        self.failures_before_success = failures_before_success
        self.invoke_count = 0

    def with_structured_output(self, output_model):
        """
        The real LangChain model returns a structured-output
        wrapper. For this test, the fake model can return itself.
        """
        return self

    def invoke(self, prompt):
        self.invoke_count += 1

        if self.invoke_count <= self.failures_before_success:
            raise ValueError("Simulated structured-output failure")

        return {
            "status": "success",
            "attempt": self.invoke_count,
        }


def test_retry_succeeds_after_temporary_failure():
    """
    The first attempt fails, but the second attempt succeeds.
    """

    fake_model = FakeStructuredModel(
        failures_before_success=1
    )

    result = invoke_structured_with_retry(
        output_model=dict,
        prompt="Test prompt",
        model=fake_model,
    )

    assert result["status"] == "success"
    assert result["attempt"] == 2
    assert fake_model.invoke_count == 2


def test_retry_allows_multiple_attempts():
    """
    The model fails twice, then succeeds on the third attempt.

    MAX_LLM_RETRIES is currently 2, so the total allowed
    attempts should be 3.
    """

    fake_model = FakeStructuredModel(
        failures_before_success=2
    )

    result = invoke_structured_with_retry(
        output_model=dict,
        prompt="Test prompt",
        model=fake_model,
    )

    assert result["status"] == "success"
    assert result["attempt"] == 3
    assert fake_model.invoke_count == 3


def test_retry_raises_after_all_attempts_fail():
    """
    The model fails on every attempt.

    The helper should raise RuntimeError after the initial
    attempt plus MAX_LLM_RETRIES retries.
    """

    fake_model = FakeStructuredModel(
        failures_before_success=MAX_LLM_RETRIES + 1
    )

    with pytest.raises(
        RuntimeError,
        match="failed to return valid structured data",
    ):
        invoke_structured_with_retry(
            output_model=dict,
            prompt="Test prompt",
            model=fake_model,
        )

    expected_attempts = MAX_LLM_RETRIES + 1
    assert fake_model.invoke_count == expected_attempts