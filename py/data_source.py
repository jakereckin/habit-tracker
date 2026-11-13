import sqlitecloud
import pandas as pd
from typing import Any, Optional, Sequence


def run_query(
    sql: str,
    connection: str,
    params: Optional[Sequence[Any]] = None,
) -> pd.DataFrame:
    """
    Runs a SQL query on the given SQLite database connection.

    Args:
        sql (str): The SQL query to execute.
        connection (str): The SQLite database connection string.

    Returns:
        pd.DataFrame: The result of the SQL query as a 
        pandas DataFrame.
    """
    with sqlitecloud.connect(connection) as conn:
        return pd.read_sql(sql, conn, params=params or [])