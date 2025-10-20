"""
tests/api/test_socket.py

Test suite for agent socket streaming endpoints and data validation.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.api.utils.schemas import CleanForm, FileUploadData

@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)

@pytest.fixture
def valid_file_upload_payload():
    """Valid file upload payload for testing."""
    return {
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_method": "file-upload",
        "service": "clean",
        "data": {
            "filename": "test_data.csv",
            "content": "col1,col2\n1,2\n3,4",
            "file_type": "csv"
        },
        "user_input_tags": ["test", "sample"],
        "model_objective": "Clean and validate the dataset"
    }

@pytest.fixture
def invalid_file_upload_missing_fields():
    """Invalid payload - missing required fields in data."""
    return {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "timestamp": "2025-10-20T07:56:14.764Z",
        "input_method": "file-upload",
        "service": "clean",
        "data": {},  # Missing filename and content
        "user_input_tags": ["string"],
        "model_objective": "string"
    }

@pytest.fixture
def invalid_file_upload_wrong_type():
    """Invalid payload - wrong data structure."""
    return {
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input_method": "file-upload",
        "service": "clean",
        "data": {
            "filename": "test.csv",
            "content": "data",
            "file_type": "invalid_type"  # Not in allowed literals
        },
        "user_input_tags": ["test"],
        "model_objective": "Test"
    }


class TestFileUploadValidation:
    """Test suite for file upload input validation."""

    def test_valid_file_upload_csv(self, client, valid_file_upload_payload):
        """Test valid CSV file upload payload."""
        response = client.post("/agent/start-wrangler", json=valid_file_upload_payload)

        # Should redirect to the agent window
        assert response.status_code in [200, 307, 302], f"Expected redirect, got {response.status_code}"

    def test_valid_file_upload_json(self, client):
        """Test valid JSON file upload payload."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "file-upload",
            "service": "clean",
            "data": {
                "filename": "test_data.json",
                "content": '{"key": "value"}',
                "file_type": "json"
            },
            "user_input_tags": ["json", "test"],
            "model_objective": "Process JSON data"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code in [200, 307, 302]

    def test_invalid_file_upload_missing_filename(self, client, invalid_file_upload_missing_fields):
        """Test file upload with missing required fields - should return 422."""
        response = client.post("/agent/start-wrangler", json=invalid_file_upload_missing_fields)

        assert response.status_code == 422, f"Expected 422 Unprocessable Entity, got {response.status_code}"

        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0

        # Check that the error mentions the validation failure
        error = data["detail"][0]
        assert error["type"] == "value_error"
        assert "file-upload" in error["msg"]
        assert "filename" in error["msg"] or "content" in error["msg"]

    def test_invalid_file_upload_missing_content(self, client):
        """Test file upload with missing content field."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "file-upload",
            "service": "clean",
            "data": {
                "filename": "test.csv"
                # Missing content field
            },
            "user_input_tags": ["test"],
            "model_objective": "Test"
        }
        response = client.post("/agent/start-wrangler", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "content" in str(data["detail"]).lower()

    def test_invalid_file_upload_wrong_file_type(self, client):
        """Test file upload with invalid file_type literal."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "file-upload",
            "service": "clean",
            "data": {
                "filename": "test.txt",
                "content": "some text content",
                "file_type": "txt"  # Not in ["csv", "json", "xlsx", "parquet"]
            },
            "user_input_tags": ["test"],
            "model_objective": "Test"
        }
        response = client.post("/agent/start-wrangler", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_invalid_input_method(self, client):
        """Test with invalid input_method."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "invalid-method",
            "service": "clean",
            "data": {},
            "user_input_tags": ["test"],
            "model_objective": "Test"
        }
        response = client.post("/agent/start-wrangler", json=payload)

        assert response.status_code == 422

    def test_missing_required_top_level_fields(self, client):
        """Test missing required top-level fields."""
        payload = {
            # Missing id, timestamp
            "input_method": "file-upload",
            "service": "clean",
            "data": {
                "filename": "test.csv",
                "content": "data"
            }
        }
        response = client.post("/agent/start-wrangler", json=payload)

        # Should still work if id and timestamp have defaults
        # Or should fail if they're required
        assert response.status_code in [200, 307, 302, 422]


class TestOtherInputMethods:
    """Test suite for other data input methods."""

    def test_valid_huggingface_input(self, client):
        """Test valid Hugging Face dataset input."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "hugging-face",
            "service": "clean",
            "data": {
                "dataset_id": "username/dataset-name",
                "split": "train"
            },
            "user_input_tags": ["huggingface"],
            "model_objective": "Load from HF"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code in [200, 307, 302]

    def test_valid_kaggle_input(self, client):
        """Test valid Kaggle dataset input."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "kaggle",
            "service": "clean",
            "data": {
                "dataset_id": "username/dataset-name",
                "file_name": "data.csv"
            },
            "user_input_tags": ["kaggle"],
            "model_objective": "Load from Kaggle"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code in [200, 307, 302]

    def test_valid_supabase_input(self, client):
        """Test valid Supabase connection input."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "supabase",
            "service": "clean",
            "data": {
                "connection_string": "postgresql://user:pass@host:5432/db",
                "table_name": "users"
            },
            "user_input_tags": ["supabase"],
            "model_objective": "Load from Supabase"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code in [200, 307, 302]

    def test_valid_mongodb_input(self, client):
        """Test valid MongoDB connection input."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "mongodb",
            "service": "clean",
            "data": {
                "connection_string": "mongodb://localhost:27017",
                "database_name": "test_db",
                "collection_name": "test_collection"
            },
            "user_input_tags": ["mongodb"],
            "model_objective": "Load from MongoDB"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code in [200, 307, 302]

    def test_valid_google_sheets_input(self, client):
        """Test valid Google Sheets input."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "google-sheets",
            "service": "clean",
            "data": {
                "spreadsheet_id": "abc123xyz",
                "sheet_name": "Sheet1",
                "oauth_token": "fake_token_for_testing"
            },
            "user_input_tags": ["google-sheets"],
            "model_objective": "Load from Google Sheets"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code in [200, 307, 302]


class TestAgentWindow:
    """Test suite for agent window endpoints."""

    def test_agent_window_nonexistent_room(self, client):
        """Test accessing non-existent room returns 404."""
        fake_room_id = str(uuid4())
        response = client.get(f"/agent/{fake_room_id}/clean")

        assert response.status_code == 404
        assert "room not found" in response.text.lower()

    def test_agent_window_html_response(self, client, valid_file_upload_payload):
        """Test that agent window returns HTML when accessed normally."""
        # First create a session
        post_response = client.post("/agent/start-wrangler", json=valid_file_upload_payload)

        if post_response.status_code in [307, 302]:
            # Follow redirect
            redirect_url = post_response.headers.get("location")
            if redirect_url:
                response = client.get(redirect_url)
                assert response.status_code == 200
                assert "text/html" in response.headers.get("content-type", "")

    def test_agent_window_sse_response(self, client, valid_file_upload_payload):
        """Test that agent window returns SSE stream when requested."""
        # First create a session
        post_response = client.post("/agent/start-wrangler", json=valid_file_upload_payload)

        if post_response.status_code in [307, 302]:
            # Get the redirect URL
            redirect_url = post_response.headers.get("location")
            if redirect_url:
                # Request with SSE headers
                response = client.get(
                    redirect_url,
                    headers={"accept": "text/event-stream"}
                )
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_payload(self, client):
        """Test completely empty payload."""
        response = client.post("/agent/start-wrangler", json={})
        assert response.status_code == 422

    def test_null_data_field(self, client):
        """Test null data field."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "file-upload",
            "service": "clean",
            "data": None,
            "user_input_tags": [],
            "model_objective": ""
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code == 422

    def test_very_large_file_content(self, client):
        """Test with very large file content."""
        large_content = "x" * (10 * 1024 * 1024)  # 10MB string
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "file-upload",
            "service": "clean",
            "data": {
                "filename": "large_file.csv",
                "content": large_content,
                "file_type": "csv"
            },
            "user_input_tags": ["large"],
            "model_objective": "Test large file"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 307, 302, 413, 422]

    def test_special_characters_in_filename(self, client):
        """Test filename with special characters."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "file-upload",
            "service": "clean",
            "data": {
                "filename": "test@#$%^&*()_+-={}[]|:;<>,.?/~`file.csv",
                "content": "data",
                "file_type": "csv"
            },
            "user_input_tags": ["special-chars"],
            "model_objective": "Test"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code in [200, 307, 302]

    def test_unicode_content(self, client):
        """Test file content with unicode characters."""
        payload = {
            "id": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input_method": "file-upload",
            "service": "clean",
            "data": {
                "filename": "unicode_test.csv",
                "content": "name,value\n你好,世界\nBonjour,Monde\nΓειά,κόσμος",
                "file_type": "csv"
            },
            "user_input_tags": ["unicode"],
            "model_objective": "Test unicode"
        }
        response = client.post("/agent/start-wrangler", json=payload)
        assert response.status_code in [200, 307, 302]
