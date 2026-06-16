from google.cloud import bigquery
import logging

from config.settings import BIGQUERY_PROJECT

logger = logging.getLogger(__name__)

# Tier question limits
TIER_LIMITS = {
    "free": 5,
    "basic": 20,
    "pro": 50,
}

# Warning thresholds per tier
TIER_WARNINGS = {
    "free": 5,      # warning at limit (triggers block)
    "basic": 15,    # warning at 15
    "pro": 45,      # warning at 45
}


def get_bq_client():
    """Get a BigQuery client instance."""
    return bigquery.Client(project=BIGQUERY_PROJECT)


def get_customer_info(user_id: str) -> dict | None:
    """
    Look up customer info from demografy.ref_tables.dev_customers.

    Returns a dict with keys: user_id, tier, is_active
    Returns None if customer not found.
    """
    query = f"""
        SELECT
            user_id,
            tier,
            is_active
        FROM demografy.ref_tables.dev_customers
        WHERE user_id = '{user_id}'
        LIMIT 1
    """

    try:
        client = get_bq_client()
        results = client.query(query).result()

        for row in results:
            return {
                "user_id": row.user_id,
                "tier": row.tier.lower() if row.tier else "free",
                "is_active": row.is_active if row.is_active is not None else False,
            }
    except Exception as e:
        logger.exception(f"Failed to look up customer {user_id}: {str(e)}")

    return None


def get_question_limit(tier: str) -> int:
    """Return the max question count for a given tier."""
    return TIER_LIMITS.get(tier.lower(), 5)


def get_warning_threshold(tier: str) -> int:
    """Return the warning threshold for a given tier."""
    return TIER_WARNINGS.get(tier.lower(), 5)


def is_active_customer(customer_info: dict | None) -> bool:
    """Check if customer exists and is active."""
    return customer_info is not None and customer_info.get("is_active", False)