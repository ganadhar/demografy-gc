from google.cloud import bigquery

from config.settings import (
    BIGQUERY_PROJECT,
    MAX_QUERY_ROWS,
    QUERY_TIMEOUT,
    FULL_TABLE_NAME,
)


class BigQueryTool:
    """Custom tool for executing safe, read-only BigQuery queries."""

    name = "bigquery_query"
    description = (
        "Execute a read-only SQL query against the Demografy Australian demographic data. "
        f"The only table available is {FULL_TABLE_NAME}. "
        "Use this to answer questions about Australian suburbs, states, and demographic KPIs. "
        "Always return results as a formatted table."
        "If exact matching suburb not found, query for area matching user query"
    )

    def __init__(self):
        self.client = bigquery.Client(project=BIGQUERY_PROJECT)
        self.last_result = None  # Store raw DataFrame-like result for charting

    def _sanitize_query(self, query: str) -> str:
        """Ensure query is read-only and safe."""
        # Strip trailing semicolon so we can properly append LIMIT before it
        has_semicolon = query.rstrip().endswith(";")
        query_clean = query.rstrip().rstrip(";").strip()

        query_upper = query_clean.upper()

        # Block dangerous operations
        dangerous_keywords = [
            "DELETE", "UPDATE", "INSERT", "DROP", "ALTER", "CREATE", "TRUNCATE", "MERGE",
        ]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(
                    f"Dangerous operation '{keyword}' is not allowed. "
                    "Only SELECT queries are permitted."
                )

        # Ensure it's a SELECT query
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")


        return query_clean

    def _run(self, query: str) -> str:
        """Execute the query and return results as a formatted string."""
        try:
            # Sanitize the query
            safe_query = self._sanitize_query(query)

            # Configure query job
            job_config = bigquery.QueryJobConfig(
                maximum_bytes_billed=1 * 1024 * 1024 * 1024,  # 1 GB limit
                priority=bigquery.QueryPriority.INTERACTIVE,
            )

            # Execute query
            query_job = self.client.query(safe_query, job_config=job_config)
            results = query_job.result(QUERY_TIMEOUT)

            # Format results
            rows = []
            for row in results:
                row_dict = dict(row)
                rows.append(row_dict)

            if not rows:
                self.last_result = None
                return "No results found for this query. Look for results that might match areas."

            # Store raw result for charting
            self.last_result = rows

            # Return as formatted output
            columns = list(rows[0].keys())
            output = f"Query returned {len(rows)} rows.\n\n"
            output += " | ".join(columns) + "\n"
            output += "-" * len(columns) + "\n"

            for row in rows:
                output += " | ".join(str(row.get(col, "")) for col in columns) + "\n"

            return output

        except ValueError as e:
            self.last_result = None
            return f"Query validation error: {str(e)}"
        except Exception as e:
            self.last_result = None
            return f"BigQuery execution error: {str(e)}"