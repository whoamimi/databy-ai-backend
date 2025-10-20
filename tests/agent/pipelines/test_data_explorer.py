"""
tests.agent.pipelines.data_explorer

Test cases for the data exploration pipeline components.
"""

import pytest
import pandas as pd
from io import StringIO
from unittest.mock import Mock, patch
from ollama import ChatResponse, Message

from app.agent.pipelines.data_explorer import (
    DataSummary,
    DataMetaSummary,
    NumericTyper,
    DataTyper,
    DefineDataset,
    DescribeDataset,
    DataTyperStage,
    DataExplorer,
)
from app.agent.pipelines.records import (
    DATA_SUMMARY_COLS,
    DATA_SUMMARY_NEW_COLS,
    DATA_SUMMARY_TYPE_COLS,
)
from app.agent.main import GabyWindow

def build_error_data_summary():
    """
    Build an empty or malformed data summary DataFrame to simulate error conditions.
    This is used to test error handling in the data explorer pipeline.

    Returns:
        pd.DataFrame: Empty DataFrame with expected columns but no data
    """
    # Return empty DataFrame with the expected columns structure
    # This simulates a scenario where data summary generation failed
    return pd.DataFrame(columns=DATA_SUMMARY_COLS)

def build_llm_response(content: str = "test content", role: str = "assistant"):
    message = Message(role=role, content=content)

    # Construct a valid ChatResponse instance as response
    return ChatResponse(
        model="test-model",
        created_at="2025-01-01T00:00:00Z",
        message=message,
        done=True,
        total_duration=0,
        load_duration=0,
        prompt_eval_count=0,
        prompt_eval_duration=0,
        eval_count=0,
        eval_duration=0
    )

@pytest.fixture(scope="session", autouse=True)
def sample_dataframe_medium():
    """Create a sample DataFrame for testing."""
    data = {
        'user_id': [1001, 1002, 1003, 1004, 1005],
        'name': ['Alex', 'Jordan', 'Riley', 'Casey', None],
        'age': [29, 35, 42, 26, None],
        'city': ['Sydney', 'Melbourne', 'Perth', None, 'Adelaide'],
        'purchases': [5, 3, None, 8, 2],
        'spend': [320.50, 180.75, 210.00, 540.10, None]
    }
    return pd.DataFrame(data)

#@pytest.fixture(scope="session", autouse=True)
def sample_dataframe_easy():
    csv_data = StringIO("""
    user_id,name,age,city,purchases,spend,signup_date
    1001,Alex,29,Sydney,5,320.50,2023-05-12
    1002,Jordan,35,Melbourne,3,180.75,2023-07-08
    1003,Riley,42,Perth,,210.00,2022-11-23
    1004,Casey,26,Brisbane,8,540.10,2023-02-19
    1005,Jamie,,Adelaide,2,95.00,2023-08-02
    1006,Taylor,31,Sydney,7,400.00,2023-01-15
    1007,Drew,38,,4,310.80,2022-09-30
    """)

    df = pd.read_csv(csv_data)
    return df

def build_mock_session(data_type: str = 'easy'):

    from uuid import uuid4
    from datetime import datetime

    if data_type == 'easy':
        df = sample_dataframe_easy()
    else:
        df = sample_dataframe_medium()

    id = uuid4()
    created_timestamp = datetime.now()

    return GabyWindow(id=id, created_timestamp=created_timestamp, data=df)

@patch("ollama.Client", return_value=Mock())
@patch("ollama.Client.chat", return_value=build_llm_response())
def test_data_summary(mock_ollama_client, mock_ollama_return_value):

    test_input = {
        "data_summary": "hello"
    }

    test_input_2 = {
        "data_summary": "another data summary table markdown"
    }

    mock_ollama_client.chat.return_value = build_llm_response()

    summarizer = DataSummary()
    response = summarizer.run(mock_ollama_client, **test_input)

    print("Response output:", response)
    assert summarizer.model_name == "base" and summarizer.model_id == "hf.co/bartowski/Llama-3.2-3B-Instruct-GGUF:Q3_K_L", f"Unexpected model id: {summarizer.model_id} and model name: {summarizer.model_name}"
    assert len(summarizer.history) == 1, f"Expected 1 message to be added after one chat instance."

    response_2 = summarizer.run(mock_ollama_client, **test_input_2)
    assert len(summarizer.history) == 2, f"Expected 2 messages to be added after 2 chat instances."

@patch("ollama.Client", return_value=Mock())
def test_data_summary_error_user_input(mock_ollama_client):
    test_input = {
        "not_data_summary": "asdfasdfasd"
    }

    summarizer = DataSummary()

    with pytest.raises(TypeError) as excinfo:
        response = summarizer.run(mock_ollama_client, **test_input)
        assert isinstance(excinfo.value, TypeError) and isinstance(response, str), f"Invalid type error and value returned."

def test_data_explorer_define_dataset():
    """Test DefineDataset stage creates proper data summary."""
    # Create real session with real DataFrame (not mocked)
    pre_session = build_mock_session("easy")

    defineData = DefineDataset()
    print(f"data define obj: {defineData}")

    session = defineData.forward(pre_session)
    print(f"Output: {session}")

    assert session.data_summary is not None, "data_summary should be populated"
    assert session.data_types is not None, "data_types should be populated"
    assert isinstance(session.data_summary, pd.DataFrame), "data_summary should be DataFrame"
    assert len(session.data_summary) == len(session.data.columns), "Should have one row per column"
    assert pre_session == session, f"Checks if the same memory is used."

def test_data_explorer_define_dataset_error():
    """Test DefineDataset raises error when data_summary is None."""

    session = build_mock_session()
    defineData = DefineDataset()

    # Run forward to create data_summary
    session = defineData.forward(session)

    # NOW set it to None and test validation
    session.data_summary = None

    with pytest.raises(ValueError) as excinfo:
        defineData.validate_stage_output(session)

    assert "Expected Attribute" in str(excinfo.value)

@patch("ollama.Client", return_value=Mock())
@patch("ollama.Client.chat", return_value=build_llm_response())
def test_data_meta_summary_run_loop(mock_ollama_client, mock_ollama_response):
    """Test DataMetaSummary.run_loop generates descriptions for all columns."""

    # Create sample data
    sample_df = sample_dataframe_easy()

    # Mock client
    mock_client = Mock()
    mock_client.chat.return_value = build_llm_response(content="Column description")

    # Create instance and run
    meta_describer = DataMetaSummary()
    description = "This is a customer dataset"

    result = meta_describer.run_loop(
        client=mock_client,
        description=description,
        data_sample=sample_df
    )

    # Assertions
    assert isinstance(result, dict), "Result should be a dictionary"
    assert len(result) == len(sample_df.columns), f"Should have description for all {len(sample_df.columns)} columns"

    # Check all columns are present
    for col in sample_df.columns:
        assert col in result, f"Column {col} should have a description"
        assert isinstance(result[col], str), f"Description for {col} should be a string"

    # Verify run was called for each column
    assert len(meta_describer.history) == len(sample_df.columns), \
        f"Should have {len(sample_df.columns)} entries in history"

def test_describe_dataset_forward():
    """Test DescribeDataset.forward generates descriptions and updates session."""

    # Create session with data_summary already populated
    session = build_mock_session()
    define_stage = DefineDataset()
    session = define_stage.forward(session)

    # Mock agent with client
    from app.agent.main import GabyAgent
    mock_agent = Mock(spec=GabyAgent)
    mock_client = Mock()
    mock_client.chat.return_value = build_llm_response(content="Dataset contains customer information")
    mock_agent.client = mock_client

    # Create DescribeDataset instance and run
    describe_stage = DescribeDataset()

    result_session = describe_stage.forward(mock_agent, session)

    # Assertions
    assert result_session.description is not None, "Description should be set"
    assert isinstance(result_session.description, str), "Description should be a string"
    assert "description" in result_session.data_summary.columns, \
        "data_summary should have 'description' column"
    assert len(result_session.data_summary) > 0, "data_summary should have rows"

def test_describe_dataset_validation():
    """Test DescribeDataset.validate_stage_output checks required columns."""

    session = build_mock_session()
    define_stage = DefineDataset()
    session = define_stage.forward(session)

    # Mock agent
    mock_agent = Mock()
    mock_client = Mock()
    mock_client.chat.return_value = build_llm_response(content="Test description")
    mock_agent.client = mock_client

    describe_stage = DescribeDataset()
    session = describe_stage.forward(mock_agent, session)

    # Validation should pass with correct columns
    describe_stage.validate_stage_output(session)

    # Test with missing column - remove 'description'
    session.data_summary = session.data_summary.drop(columns=['description'])

    with pytest.raises(ValueError) as excinfo:
        describe_stage.validate_stage_output(session)

    assert "columns mismatch" in str(excinfo.value).lower()

def test_describe_dataset_error_none_data_summary():
    """Test DescribeDataset raises error when data_summary is None."""

    session = build_mock_session()
    session.data_summary = None

    mock_agent = Mock()
    describe_stage = DescribeDataset()

    with pytest.raises(ValueError) as excinfo:
        describe_stage.forward(mock_agent, session)

    assert "Data Summary unavailable" in str(excinfo.value)

def test_data_explorer_pipeline():
    pass

def test_data_explorer_pipeline_cycle():
    pass