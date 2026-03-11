import json
import re
import logging

from agno.tools import tool

from services.NeondbService import NeonDBService

logger = logging.getLogger(__name__)

# Statements that must never appear in a query from the agent
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)


def create_sql_tool(project_id: int, user_id: str, db: NeonDBService):
    """
    Factory that returns an Agno @tool function bound to a specific
    project_id / user_id.  The tool validates, scopes, and executes
    SELECT queries against NeonDB.
    """

    @tool(
        name="run_sql_query",
        description=(
            "Execute a read-only SQL SELECT query against the project's "
            "oceanographic database and return the result rows as JSON."
        ),
    )
    def run_sql_query(query: str) -> str:
        """Run a SELECT query and return JSON rows.

        Args:
            query: A valid PostgreSQL SELECT statement. Use {project_id}
                   as a placeholder for the current project.
        """
        # ── 1. Strip markdown fencing if the LLM wrapped it ──────────
        cleaned = query.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        # ── 2. Block anything that is not a SELECT ───────────────────
        if _FORBIDDEN_KEYWORDS.search(cleaned):
            return json.dumps({"error": "Only SELECT queries are allowed."})

        # Rough check: first meaningful keyword must be SELECT / WITH
        first_word = cleaned.lstrip("( \t\n").split()[0].upper() if cleaned.strip() else ""
        if first_word not in ("SELECT", "WITH"):
            return json.dumps({"error": "Only SELECT queries are allowed."})

        # Block multiple statements (semicolon followed by another statement)
        statements = [s.strip() for s in cleaned.split(";") if s.strip()]
        if len(statements) > 1:
            return json.dumps({"error": "Only a single SELECT statement is allowed."})

        # ── 3. Substitute {project_id} safely via psycopg2 params ────
        # Replace the placeholder with a psycopg2 parameter marker
        parameterized = cleaned.replace("{project_id}", "%s")
        params = []
        # Count how many %s we introduced (one per {project_id} occurrence)
        count = cleaned.count("{project_id}")
        params = tuple([project_id] * count) if count else ()

        # ── 4. Add a default LIMIT if none present ───────────────────
        if not re.search(r"\bLIMIT\b", parameterized, re.IGNORECASE):
            parameterized = parameterized.rstrip("; \t\n") + " LIMIT 100"

        # ── 5. Verify ownership, then execute ────────────────────────
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                db.verify_project_ownership(cursor, project_id, user_id)

            rows = db.execute_select(parameterized, params)
            return json.dumps(rows, default=str)
        except LookupError as exc:
            return json.dumps({"error": str(exc)})
        except PermissionError as exc:
            return json.dumps({"error": str(exc)})
        except Exception as exc:
            logger.exception("SQL tool error")
            return json.dumps({"error": "Failed to execute query. Please try rephrasing your question."})

    return run_sql_query