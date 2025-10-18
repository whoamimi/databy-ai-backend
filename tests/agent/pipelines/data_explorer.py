"""
tests.agent.pipelines.data_explorer

Test cases for the data exploration pipeline components.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

from ollama import ChatResponse, Message

from app.agent.pipelines.data_explorer import (
    DataSummary,
    DataMetaSummary,
    NumericTyper,
    DataTyper,
    DataExplorer,
    DefineDataset,
    DescribeDataset,
    DataTyperStage,
    DataExplorerPipeline,
    setup_pipeline
)
from app.agent.pipelines.records import (
    Session,
    DATA_SUMMARY_COLS,
    DATA_SUMMARY_NEW_COLS,
    DATA_SUMMARY_TYPE_COLS,
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'user_id': [1001, 1002, 1003, 1004, 1005],
        'name': ['Alex', 'Jordan', 'Riley', 'Casey', None],
        'age': [29, 35, 42, 26, None],
        'city': ['Sydney', 'Melbourne', 'Perth', 'Brisbane', 'Adelaide'],
        'purchases': [5, 3, None, 8, 2],
        'spend': [320.50, 180.75, 210.00, 540.10, 95.00]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_session(sample_dataframe):
    """Create a sample Session for testing."""
    return Session(data=sample_dataframe)

@pytest.fixture
def mock_ollama_client():
    """Create a mock Ollama client returning a ChatResponse."""
    # Mock message object
    message = Message(role="assistant", content="Test LLM response")

    # Construct a valid ChatResponse instance
    mock_response = ChatResponse(
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

    # Create mock client and set return value
    client = Mock()
    client.chat.return_value = mock_response

    return client

@pytest.fixture
def mock_agent(mock_ollama_client):
    """Create a mock agent with client. TODO: this is supposed to mock `GabyAgent` from app.agent.main. """

    agent = Mock()
    agent.client = mock_ollama_client

    return agent


class TestDataSummary:
    """Test cases for DataSummary class."""

    def test_pre_process(self):
        """Test DataSummary pre_process method."""

        data_summary = DataSummary()
        input_data = "| Column | Type | Count |\n| age | int64 | 5 |"

        result = data_summary.pre_process(input_data)

        assert isinstance(result, dict)
        assert 'data_table' in result
        assert result['data_table'] == input_data

class TestDataMetaSummary:
    """Test cases for DataMetaSummary class."""

    def test_pre_process(self):
        """Test DataMetaSummary pre_process method."""
        meta_summary = DataMetaSummary()
        sample_data = "Alex\nJordan\nRiley"
        label = "name"

        result = meta_summary.pre_process(sample_data, label)

        assert isinstance(result, dict)
        assert result['data_sample'] == sample_data
        assert result['data_label'] == label

    @patch('app.agent.pipelines.data_explorer.DataMetaSummary.run')
    def test_run_loop(self, mock_run, mock_ollama_client, sample_dataframe):
        """Test DataMetaSummary run_loop method."""
        meta_summary = DataMetaSummary()
        mock_run.return_value = "Mocked description"
        description = "Sample dataset description"

        result = meta_summary.run_loop(mock_ollama_client, description, sample_dataframe)

        assert isinstance(result, dict)
        assert len(result) == len(sample_dataframe.columns)
        assert all(col in result for col in sample_dataframe.columns)
        assert mock_run.call_count == len(sample_dataframe.columns)

    @patch('app.agent.pipelines.data_explorer.DataMetaSummary.run')
    def test_run_loop_exception_handling(self, mock_run, mock_ollama_client, sample_dataframe):
        """Test DataMetaSummary run_loop exception handling."""

        meta_summary = DataMetaSummary()
        mock_run.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            meta_summary.run_loop(mock_ollama_client, "description", sample_dataframe)

class TestNumericTyper:
    """Test cases for NumericTyper class."""

    def test_pre_process(self):
        """Test NumericTyper pre_process method."""
        numeric_typer = NumericTyper()
        test_kwargs = {'col_name': 'age', 'data_sample': [29, 35, 42]}

        result = numeric_typer.pre_process(**test_kwargs)

        assert result == test_kwargs

    @patch('app.agent.pipelines.data_explorer.NumericTyper.post_process')
    def test_post_process_valid_types(self, mock_super_post_process):
        """Test NumericTyper post_process with valid types."""
        numeric_typer = NumericTyper()
        valid_types = ["continuous", "binary", "multi", "ordinal", "nominal"]

        for valid_type in valid_types:
            mock_super_post_process.return_value = valid_type
            result = numeric_typer.post_process("response")
            assert result == valid_type

    @patch('app.agent.pipelines.data_explorer.NumericTyper.post_process')
    def test_post_process_invalid_type(self, mock_super_post_process):
        """Test NumericTyper post_process with invalid type."""
        numeric_typer = NumericTyper()
        mock_super_post_process.return_value = "invalid_type"

        with pytest.raises(ValueError):
            numeric_typer.post_process("response")


class TestDataTyper:
    """Test cases for DataTyper class."""

    def test_pre_process(self):
        """Test DataTyper pre_process method."""
        data_typer = DataTyper()
        test_kwargs = {'col_name': 'age', 'data_sample': [29, 35, 42]}

        result = data_typer.pre_process(**test_kwargs)

        assert result == test_kwargs

    @patch('app.agent.pipelines.data_explorer.DataTyper.run')
    @patch('app.agent.pipelines.data_explorer.NumericTyper.run')
    def test_run_loop(self, mock_numeric_run, mock_data_run, mock_ollama_client, sample_dataframe):
        """Test DataTyper run_loop method."""
        data_typer = DataTyper()
        mock_data_run.side_effect = ["text", "numeric", "text", "text", "numeric"]
        mock_numeric_run.side_effect = ["continuous", "continuous"]

        meta, meta_num = data_typer.run_loop(mock_ollama_client, sample_dataframe)

        assert isinstance(meta, dict)
        assert isinstance(meta_num, dict)
        assert len(meta) == len(sample_dataframe.columns)
        # Should only have numeric classifications for "numeric" typed columns
        assert len(meta_num) == 2  # age and purchases should be numeric

    @patch('app.agent.pipelines.data_explorer.DataTyper.run')
    def test_run_loop_exception_handling(self, mock_run, mock_ollama_client, sample_dataframe):
        """Test DataTyper run_loop exception handling."""
        data_typer = DataTyper()
        mock_run.side_effect = Exception("Test error")

        with pytest.raises(Exception, match="Test error"):
            data_typer.run_loop(mock_ollama_client, sample_dataframe)


class TestDataExplorer:
    """Test cases for DataExplorer dataclass."""

    def test_dataclass_initialization(self):
        """Test DataExplorer dataclass initialization."""
        explorer = DataExplorer()

        assert isinstance(explorer.dataDescriber, DataSummary)
        assert isinstance(explorer.metaDescriber, DataMetaSummary)
        assert isinstance(explorer.dataTyper, DataTyper)

    def test_dataclass_immutability(self):
        """Test DataExplorer dataclass is frozen."""

        explorer = DataExplorer()

        with pytest.raises(AttributeError, match="Cannot assign to attribute"):
            # Use object.__setattr__ to attempt assignment at runtime; this will raise
            # AttributeError for frozen dataclasses while avoiding static analyzer errors
            object.__setattr__(explorer, "dataDescriber", DataSummary())


class TestDefineDataset:
    """Test cases for DefineDataset pipeline stage."""

    def test_forward_success(self, mock_agent, sample_session):
        """Test DefineDataset forward method success case."""
        stage = DefineDataset()
        sample_session.data_summary = None  # Reset to test the creation

        with patch.object(stage, 'validate_stage_output') as mock_validate:
            with patch('app.agent.core.pipeline.ChainStage.forward') as mock_super_forward:
                mock_super_forward.return_value = "success"
                mock_validate.return_value = sample_session

                result = stage.forward(mock_agent, sample_session)

                assert result == "success"
                assert sample_session.data_summary is not None
                assert isinstance(sample_session.data_summary, pd.DataFrame)
                assert list(sample_session.data_summary.columns) == DATA_SUMMARY_COLS
                assert sample_session.data_types is not None
                assert isinstance(sample_session.data_types, dict)

    def test_forward_missing_data_summary_error(self, mock_agent):
        """Test DefineDataset forward with missing data summary."""
        stage = DefineDataset()
        session = Session(data=pd.DataFrame())
        session.data_summary = None

        with pytest.raises(ValueError, match="Session Data Summary unavailable"):
            stage.forward(mock_agent, session)

    def test_validate_stage_output_success(self, sample_session):
        """Test DefineDataset validate_stage_output success case."""
        stage = DefineDataset()
        sample_session.data_summary = pd.DataFrame()
        sample_session.description = "Test description"

        # Should not raise an exception
        stage.validate_stage_output(sample_session)

    def test_validate_stage_output_missing_attributes(self, sample_session):
        """Test DefineDataset validate_stage_output with missing attributes."""
        stage = DefineDataset()
        sample_session.data_summary = None

        with pytest.raises(ValueError, match="Attribute data_summary returned None"):
            stage.validate_stage_output(sample_session)


class TestDescribeDataset:
    """Test cases for DescribeDataset pipeline stage."""

    @patch('app.agent.pipelines.data_explorer.DescribeDataset.dataDescriber')
    @patch('app.agent.pipelines.data_explorer.DescribeDataset.metaDescriber')
    def test_forward_success(self, mock_meta_describer, mock_data_describer, mock_agent, sample_session):
        """Test DescribeDataset forward method success case."""
        stage = DescribeDataset()

        # Setup data summary
        sample_session.data_summary = pd.DataFrame({
            'data_field_name': ['col1', 'col2'],
            'data_type': ['int64', 'object'],
            'missing_count': [0, 1],
            'missing_ratio': [0.0, 20.0],
            'unique_count': [5, 4]
        })

        # Mock LLM responses
        mock_data_describer.run.return_value = "Dataset description"
        mock_meta_describer.run_loop.return_value = {
            'col1': 'Column 1 description',
            'col2': 'Column 2 description'
        }

        with patch('app.agent.core.pipeline.ChainStage.forward') as mock_super_forward:
            mock_super_forward.return_value = "success"

            result = stage.forward(mock_agent, sample_session)

            assert result == "success"
            assert sample_session.description == "Dataset description"
            assert 'description' in sample_session.data_summary.columns

    def test_forward_missing_data_summary_error(self, mock_agent):
        """Test DescribeDataset forward with missing data summary."""
        stage = DescribeDataset()
        session = Session(data=pd.DataFrame())
        session.data_summary = None

        with pytest.raises(ValueError, match="Session Data Summary unavailable"):
            stage.forward(mock_agent, session)

    def test_validate_stage_output_success(self, sample_session):
        """Test DescribeDataset validate_stage_output success case."""
        stage = DescribeDataset()
        expected_cols = DATA_SUMMARY_COLS + DATA_SUMMARY_NEW_COLS
        sample_session.data_summary = pd.DataFrame(columns=expected_cols)

        # Should not raise an exception
        stage.validate_stage_output(sample_session)

    def test_validate_stage_output_column_mismatch(self, sample_session):
        """Test DescribeDataset validate_stage_output with column mismatch."""
        stage = DescribeDataset()
        sample_session.data_summary = pd.DataFrame(columns=['wrong_col'])

        with pytest.raises(ValueError, match="Data summary columns mismatch"):
            stage.validate_stage_output(sample_session)


class TestDataTyperStage:
    """Test cases for DataTyperStage pipeline stage."""

    @patch('app.agent.pipelines.data_explorer.DataTyperStage.dataTyper')
    def test_forward_success(self, mock_data_typer, mock_agent, sample_session):
        """Test DataTyperStage forward method success case."""
        stage = DataTyperStage()

        # Setup data summary
        sample_session.data_summary = pd.DataFrame({
            'data_field_name': ['col1', 'col2'],
            'data_type': ['int64', 'object']
        })

        # Mock LLM responses
        mock_data_typer.run_loop.return_value = (
            {'col1': 'numeric', 'col2': 'text'},
            {'col1': 'continuous'}
        )

        stage.forward(mock_agent, sample_session)

        assert '_data_types' in sample_session.data_summary.columns
        assert '_data_num_types' in sample_session.data_summary.columns

    def test_validate_stage_output_success(self, sample_session):
        """Test DataTyperStage validate_stage_output success case."""
        stage = DataTyperStage()
        columns = DATA_SUMMARY_COLS + DATA_SUMMARY_NEW_COLS + DATA_SUMMARY_TYPE_COLS
        sample_session.data_summary = pd.DataFrame(columns=columns)

        # Should not raise an exception
        stage.validate_stage_output(sample_session)

    def test_validate_stage_output_missing_columns(self, sample_session):
        """Test DataTyperStage validate_stage_output with missing columns."""
        stage = DataTyperStage()
        sample_session.data_summary = pd.DataFrame(columns=DATA_SUMMARY_COLS)

        with pytest.raises(ValueError, match="Expected specific data_summary fields"):
            stage.validate_stage_output(sample_session)


class TestDataExplorerPipeline:
    """Test cases for DataExplorerPipeline class."""

    def test_initialization(self):
        """Test DataExplorerPipeline initialization."""
        pipeline = DataExplorerPipeline()

        assert isinstance(pipeline.prompt, DataExplorer)
        assert isinstance(pipeline.pipe, DefineDataset)

    @patch('app.agent.pipelines.data_explorer.DefineDataset.forward')
    def test_run(self, mock_forward, mock_agent, sample_session):
        """Test DataExplorerPipeline run method."""
        pipeline = DataExplorerPipeline()
        mock_forward.return_value = "pipeline_result"

        result = pipeline.run(mock_agent, sample_session)

        assert result == "pipeline_result"
        mock_forward.assert_called_once_with(mock_agent, sample_session)


class TestSetupPipeline:
    """Test cases for setup_pipeline function."""

    def test_setup_pipeline_structure(self):
        """Test setup_pipeline creates correct pipeline structure."""
        pipeline_gen = setup_pipeline()
        first_stage = next(pipeline_gen)

        assert isinstance(first_stage, DefineDataset)
        assert isinstance(first_stage._next_stage, DescribeDataset)
        assert isinstance(first_stage._next_stage._next_stage, DataTyperStage)

    def test_setup_pipeline_is_generator(self):
        """Test setup_pipeline returns a generator."""
        pipeline_gen = setup_pipeline()

        assert hasattr(pipeline_gen, '__next__')
        assert hasattr(pipeline_gen, '__iter__')


class TestIntegration:
    """Integration tests for the data exploration pipeline."""

    @patch('app.agent.pipelines.data_explorer.DescribeDataset.dataDescriber')
    @patch('app.agent.pipelines.data_explorer.DescribeDataset.metaDescriber')
    @patch('app.agent.pipelines.data_explorer.DataTyperStage.dataTyper')
    def test_full_pipeline_execution(self, mock_data_typer, mock_meta_describer,
                                   mock_data_describer, mock_agent, sample_dataframe):
        """Test full pipeline execution from start to finish."""
        # Setup session
        session = Session(data=sample_dataframe)
        session.data_summary = None  # Start fresh

        # Mock LLM responses
        mock_data_describer.run.return_value = "Complete dataset description"
        mock_meta_describer.run_loop.return_value = {
            col: f"Description for {col}" for col in sample_dataframe.columns
        }
        mock_data_typer.run_loop.return_value = (
            {col: 'numeric' if col in ['age', 'purchases', 'spend'] else 'text'
             for col in sample_dataframe.columns},
            {'age': 'continuous', 'purchases': 'continuous', 'spend': 'continuous'}
        )

        # Run pipeline
        pipeline = DataExplorerPipeline()
        result = pipeline.run(mock_agent, session)

        # Verify results
        assert session.data_summary is not None
        assert session.description is not None
        assert '_data_types' in session.data_summary.columns
        assert '_data_num_types' in session.data_summary.columns
        assert len(session.data_summary) == len(sample_dataframe.columns)

    def test_pipeline_with_empty_dataframe(self, mock_agent):
        """Test pipeline behavior with empty DataFrame."""
        session = Session(data=pd.DataFrame())
        session.data_summary = None

        pipeline = DataExplorerPipeline()

        # Should handle empty DataFrame gracefully
        with patch('app.agent.pipelines.data_explorer.DescribeDataset.forward') as mock_describe:
            with patch('app.agent.pipelines.data_explorer.DataTyperStage.forward') as mock_typer:
                mock_describe.return_value = None
                mock_typer.return_value = None

                pipeline.run(mock_agent, session)

                # Should still create data_summary structure
                assert session.data_summary is not None
                assert len(session.data_summary) == 0  # Empty but structured