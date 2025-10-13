
import pytest
from app.schemas import ContactFormInput

TEST_SESSION_USER = dict(
    email="hello@hello.com",
    firstName="TestFirstName",
    lastName="TestLastName",
    message="Test Hello"
)

def test_working_input_contact():
    """Test that valid ContactFormInput parses and retains data correctly."""
    contact = ContactFormInput(**TEST_SESSION_USER)

    assert contact.email == TEST_SESSION_USER["email"]
    assert contact.firstName == TEST_SESSION_USER["firstName"]
    assert contact.lastName == TEST_SESSION_USER["lastName"]
    assert contact.message == TEST_SESSION_USER["message"]
