"""Lakebase Postgres connection helper for Smart Claims app."""
import psycopg
import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient

ENDPOINT_NAME = "projects/smart-claims/branches/production/endpoints/primary"
DB_NAME = "databricks_postgres"


@st.cache_resource(ttl=2700)
def _get_connection_params():
    """Get connection params with a fresh OAuth token (cached 45 min)."""
    w = WorkspaceClient()
    endpoint = w.postgres.get_endpoint(name=ENDPOINT_NAME)
    host = endpoint.status.hosts.host
    username = w.current_user.me().user_name
    token = w.postgres.generate_database_credential(endpoint=endpoint.name).token
    return {
        "host": host,
        "dbname": DB_NAME,
        "user": username,
        "password": token,
        "sslmode": "require",
    }


def get_connection():
    """Return a fresh Postgres connection."""
    params = _get_connection_params()
    return psycopg.connect(**params)


def query_df(sql, params=None):
    """Execute a read query and return a pandas DataFrame."""
    with get_connection() as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d.name for d in cur.description]
            rows = cur.fetchall()
    return pd.DataFrame(rows, columns=cols)


def execute_write(sql, params=None):
    """Execute a write query (INSERT/UPDATE/DELETE). Returns first row if any."""
    with get_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                return cur.fetchone()
    return None
