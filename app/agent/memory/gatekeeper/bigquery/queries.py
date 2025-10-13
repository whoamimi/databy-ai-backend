"""
app.agent.memory.gatekeeper.bigquery.queries

This script contains all prompts associated with the gatekeeper module.
"""

SQL_DESCRIBE_DATA_FIELD_LABEL= """
SELECT
  data_field_name,
  AI.GENERATE( ('The data field name ',
      data_field_name,
      'with values of data type,',
      data_type,
      'is one of the dataset column labels of a dataset with description: cafe sale logs. In a sentence, define what each data field represent.'),
    connection_id => '{connection_id}',
    endpoint => '{endpoint}',
    output_schema => 'data_field_name STRING, description STRING').description
FROM
  {data_summary_id};
"""

SQL_DETECT_NUMERIC_FIELD = """
SELECT
  data_field_name,
  AI.GENERATE( ('The data field name ',
      data_field_name,
      'with values of data type,',
      data_type,
      'is one of the dataset column labels of a dataset with description: cafe sale logs.'
      'Classify the dataset field into one of: Nominal, Ordinal, Continuous, Unknown, if the data type is numerical and if not, return Unknown. Return the result strictly as: "<Nominal|Ordinal|Continuous|Unknown>"'
      ),
    connection_id => '{connection_id}',
    endpoint => '{endpoint}',
    output_schema => 'data_field_name STRING, numeric_type STRING').numeric_type
FROM
  {data_summary_id};
"""
