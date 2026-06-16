import pandas as pd
import altair as alt
import streamlit as st
import logging

logger = logging.getLogger(__name__)


def _detect_chart_type(df: pd.DataFrame) -> str:
    """
    Automatically detect the best chart type based on DataFrame structure.

    Returns one of: 'bar', 'line', 'pie', 'table'
    """
    if len(df) <= 1:
        return "table"

    # Check for date/time columns (line chart candidate)
    has_date = False
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            has_date = True
            break

    if has_date:
        return "line"

    # Count categorical vs numeric columns
    numeric_cols = df.select_dtypes(include=["number", "int64", "float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

    # Pie chart: exactly 1 categorical + 1 numeric, few rows
    #if len(categorical_cols) == 1 and len(numeric_cols) == 1 and len(df) <= 10:
    #    return "pie"

    # Bar chart: has categorical + numeric columns
    if categorical_cols and numeric_cols:
        return "bar"

    # Default to bar if there are numeric columns
    if numeric_cols:
        return "bar"

    return "table"


def _get_label_column(df: pd.DataFrame) -> str:
    """Find the best column to use as X-axis label (categorical or first column)."""
    categorical = df.select_dtypes(include=["object", "string"]).columns.tolist()
    if categorical:
        return categorical[0]
    return df.columns[0]


def _get_value_columns(df: pd.DataFrame) -> list:
    """Find all numeric columns to use as values."""
    return df.select_dtypes(include=["number", "int64", "float64"]).columns.tolist()


def render_chart(df_rows: list):
    """
    Render an interactive chart in the Streamlit UI based on BigQuery results.

    :param df_rows: List of dicts from BigQuery query results.
    """
    if not df_rows or len(df_rows) < 2:
        return

    try:
        df = pd.DataFrame(df_rows)

        # Clean up: convert numeric-like strings to numbers where possible.
        # Wrap in try/except since newer pandas may raise on complex types.
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="ignore")
            except Exception:
                pass  # Skip columns that cannot be converted

        chart_type = _detect_chart_type(df)
        logger.info(f"Chart type detected: {chart_type}")

        label_col = _get_label_column(df)
        value_cols = _get_value_columns(df)

        if chart_type == "bar":
            _render_bar_chart(df, label_col, value_cols)
        elif chart_type == "line":
            _render_line_chart(df, label_col, value_cols)
        elif chart_type == "pie":
            _render_pie_chart(df, label_col, value_cols[0] if value_cols else df.columns[1])

    except Exception as e:
        logger.exception(f"Failed to render chart: {str(e)}")
        st.error(f"Could not render chart: {str(e)}")


def _render_bar_chart(df: pd.DataFrame, label_col: str, value_cols: list):
    """Render a bar chart using Altair."""
    if not value_cols:
        value_cols = [df.columns[-1]]

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(label_col, sort="-y", axis=alt.Axis(labelAngle=0)),
        y=alt.Y(value_cols[0]),
        color=alt.Color(value_cols[0], legend=None),
        tooltip=[label_col] + value_cols,
    ).properties(
        width=alt.Step(80),
        height=400,
        title=f"Bar Chart — {value_cols[0]} by {label_col}",
    )

    st.altair_chart(chart, use_container_width=True)


def _render_line_chart(df: pd.DataFrame, label_col: str, value_cols: list):
    """Render a line chart using Altair."""
    if not value_cols:
        return

    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X(label_col, title=label_col),
        y=alt.Y(value_cols[0], title=value_cols[0]),
        tooltip=[label_col] + value_cols,
    ).properties(
        width=800,
        height=400,
        title=f"Line Chart — {value_cols[0]} over {label_col}",
    )

    st.altair_chart(chart, use_container_width=True)


def _render_pie_chart(df: pd.DataFrame, label_col: str, value_col: str):
    """Render a pie chart using Altair."""
    chart = alt.Chart(df).mark_arc().encode(
        theta=alt.Theta(field=value_col, type="quantitative"),
        color=alt.Color(field=label_col, type="nominal", legend=None),
        tooltip=[label_col, value_col],
    ).properties(
        width=400,
        height=400,
        title=f"Pie Chart — {value_col} by {label_col}",
    )

    st.altair_chart(chart, use_container_width=True)