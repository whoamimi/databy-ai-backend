"""
app.agent.memory.gatekeeper.bigquery

"""

from .utils import pandas_gatekeeper
from .queries import SQL_DESCRIBE_DATA_FIELD_LABEL, SQL_DETECT_NUMERIC_FIELD

@pandas_gatekeeper
def describe_data_field(
    data_summary_id: str,
    connection_id: str | None = config.bq_model_connection,
    endpoint: str | None = config.default_model_type
):
    return SQL_DESCRIBE_DATA_FIELD_LABEL.format(
        data_summary_id=data_summary_id,
        connection_id=connection_id,
        endpoint=endpoint
    )

@pandas_gatekeeper
def detect_numeric_field(
    data_summary_id: str,
    connection_id: str | None = config.bq_model_connection,
    endpoint: str | None = config.default_model_type
):
    return SQL_DETECT_NUMERIC_FIELD.format(
        data_summary_id=data_summary_id,
        connection_id=connection_id,
        endpoint=endpoint
    )
