
import pytest
import pandas as pd
from uuid import uuid4
from datetime import datetime
from app.agent.main import GabyWindow, GabyAgent

def test_gaby_window_init():
    """ Tests basic initiation of Gaby Window. """

    id = uuid4()
    created = datetime.now()
    data = pd.DataFrame()

    ss = GabyWindow(id=id, created_timestamp=created, data=data)

    assert ss.data is not None and ss.id is not None and ss.created_timestamp is not None

def test_gaby_window_error_init():
    """ Tests initiation error cases. """

    with pytest.raises(TypeError) as excinfo:
        ss = GabyWindow(data=pd.DataFrame())
        assert isinstance(excinfo.value, TypeError), f"Expected Type Error raise when id and created_timestamp not defined at initiation."

