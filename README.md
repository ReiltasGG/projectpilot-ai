# ProjectPilot AI

ProjectPilot AI is a local AI-assisted project planning tool built with Python, Streamlit, LangGraph, Pydantic, and Ollama.

The app takes a project brief and generates a structured project plan containing:

* Project summary
* Milestones
* Actionable tasks
* Task priorities
* Estimated hours
* Task dependencies
* Project risks

The workflow also includes a dedicated risk-analysis step and a review step that can request revisions to the generated plan.

## How the workflow works

The current workflow follows this sequence:

1. **Planning**
   Creates a project plan from the submitted project brief.

2. **Risk analysis**
   Reviews the project plan and identifies project-specific risks.

3. **Review**
   Checks the plan for completeness, realistic estimates, task quality, dependencies, risks, and alignment with the project brief.

4. **Revision**
   If the plan is rejected, the workflow revises it using the review feedback.

5. **Completion**
   The workflow finishes when the plan is approved or the maximum number of revisions is reached.

The workflow allows up to three revisions.

## Requirements

You need:

* Python 3.10 or newer
* Ollama
* The `llama3.2:3b` Ollama model
* The Python dependencies used by the project
* Git, if you are working from the repository

## Ollama setup

Install Ollama from:

https://ollama.com/

After installing Ollama, download the model used by ProjectPilot AI:

```bash
ollama pull llama3.2:3b
```

Make sure Ollama is running before using the Streamlit application.

You can check that the model is available with:

```bash
ollama list
```

## Installation

Clone the repository:

```bash
git clone https://github.com/ReiltasGG/projectpilot-ai.git
```

Move into the project directory:

```bash
cd projectpilot-ai
```

Create and activate a virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the Streamlit app

From the project root, run:

```bash
PYTHONPATH=. python -m streamlit run app/main.py
```

The `PYTHONPATH=.` portion is important because the application imports modules from the project package using imports such as:

```python
from app.workflow import build_workflow
```

Using `python -m streamlit` also ensures that Streamlit runs through the currently active Python environment.

After starting the app, Streamlit will provide a local browser address.

## Using the application

1. Open the Streamlit page.
2. Enter a project name.
3. Describe the project.
4. Enter the project goal.
5. Add a deadline if one is known.
6. Add any project constraints.
7. Generate the project plan.
8. Review the generated milestones, tasks, risks, and recommendations.
9. Approve the plan or request a revision.

A useful test brief is:

```text
Project name: Customer Feedback Dashboard

Build an internal dashboard that collects customer feedback from support tickets, surveys, and product reviews. The dashboard should help the customer success and product teams identify common complaints, monitor satisfaction trends, and prioritize product improvements.

The project should include:
- A way to import feedback from CSV files
- A searchable feedback table
- Sentiment categories such as positive, neutral, and negative
- A dashboard showing feedback volume and sentiment trends
- A way to group feedback by topic
- Basic user access controls
- Documentation for future maintenance

The project should be completed in approximately 6 weeks by a small team consisting of one project manager, one frontend developer, one backend developer, and one data analyst.

Important constraints:
- Use existing company infrastructure where possible
- Avoid exposing personally identifiable customer information
- The first version should focus on CSV imports rather than live integrations
- The dashboard should be simple enough for nontechnical users
```

## Running the tests

The project uses `pytest` for automated tests.

Install pytest if it is not already installed:

```bash
python -m pip install pytest
```

Run all tests from the project root:

```bash
PYTHONPATH=. python -m pytest -v
```

The test suite includes tests for:

* Pydantic model behavior
* Structured-output retry handling
* Successful retry after a temporary failure
* Multiple retry attempts
* Final failure after all retries are exhausted
* Workflow plan generation
* Risk analysis
* Review approval
* Revision handling
* Incomplete-plan detection

The retry tests use a fake model rather than the live Ollama model. This makes the tests deterministic and avoids requiring Ollama to be running.

## Structured-output retry handling

The workflow uses structured output models for:

* `ProjectPlan`
* `RiskAnalysis`
* `PlanReview`

If the model fails to return valid structured output, the retry helper attempts the request again.

The current configuration allows:

```text
Initial attempt + 2 retries = 3 total attempts
```

If all attempts fail, the helper raises a clear runtime error.

## Project limitations

The current version is intended as a local prototype.

Known limitations include:

* The application depends on a locally running Ollama model.
* Generated plans depend on the quality of the model response.
* The current retry handling catches model invocation errors but does not independently evaluate every possible semantic problem in a valid response.
* The application does not currently persist projects in a database.
* There is no authentication or multi-user project workspace.
* The current workflow uses a fixed Ollama model configuration.

## Development workflow

Run the Streamlit app:

```bash
PYTHONPATH=. python -m streamlit run app/main.py
```

Run the tests:

```bash
PYTHONPATH=. python -m pytest -v
```

Check the current Git status:

```bash
git status
```

Commit changes:

```bash
git add .
git commit -m "Describe the change"
git push origin main
```

## Technology

* Python
* Streamlit
* LangGraph
* LangChain Ollama integration
* Pydantic
* Ollama
* Pytest
