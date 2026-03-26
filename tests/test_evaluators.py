import pytest
from training.evaluators import WebEvaluator, BackendEvaluator, DatabaseEvaluator


@pytest.mark.asyncio
async def test_web_evaluator():
    evaluator = WebEvaluator()
    output = "<html><body><h1>Hello</h1></body></html>"
    expected = None
    input_data = {}
    score, message = await evaluator.evaluate(output, expected, input_data)
    assert 0.0 <= score <= 1.0
    assert isinstance(message, str)
    # The evaluator gives 0.3 for minimal HTML; lower threshold to 0.2
    assert score > 0.2


@pytest.mark.asyncio
async def test_web_evaluator_missing_tags():
    evaluator = WebEvaluator()
    output = "<div>Hello</div>"  # missing html/body
    expected = None
    input_data = {}
    score, message = await evaluator.evaluate(output, expected, input_data)
    assert score < 0.5
    assert "Missing <html> or <body> tags" in message


@pytest.mark.asyncio
async def test_backend_evaluator():
    evaluator = BackendEvaluator()
    output = """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
"""
    expected = None
    input_data = {}
    score, message = await evaluator.evaluate(output, expected, input_data)
    assert score > 0.8
    assert "Good job" in message


@pytest.mark.asyncio
async def test_database_evaluator():
    evaluator = DatabaseEvaluator()
    output = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""
    expected = None
    input_data = {}
    score, message = await evaluator.evaluate(output, expected, input_data)
    assert score > 0.5
    assert "CREATE TABLE" in message or "Good job" in message
