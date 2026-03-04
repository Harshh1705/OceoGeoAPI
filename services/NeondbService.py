import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras


class NeonDBService:
    """Handles all interactions with the Neon PostgreSQL database.

    Assumes the schema is already provisioned. Column names and foreign keys
    match the existing Neon DB schema exactly.
    """

    def __init__(self):
        self.connection_string = os.environ.get("NEON_DATABASE_URL")
        if not self.connection_string:
            raise RuntimeError("NEON_DATABASE_URL environment variable not set")

    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ── files ─────────────────────────────────────────────────────────────────

    def insert_file_record(
        self,
        cursor,
        project_id: int,
        filename: str,
        metadata: dict,
        file_size_bytes: int | None = None,
    ) -> int:
        """
        Insert a row into `files` and return the generated file_id.

        project_id must already exist in `projects` (validated by the FK).
        metadata keys used: platform_number, data_centre
        """
        cursor.execute(
            """
            INSERT INTO files (project_id, filename, platform_number, data_centre, file_size_bytes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING file_id
            """,
            (
                project_id,
                filename,
                metadata.get("platform_number"),
                metadata.get("data_centre"),
                file_size_bytes,
            ),
        )
        return cursor.fetchone()[0]

    # ── profiles ──────────────────────────────────────────────────────────────

    def insert_profile_record(self, cursor, file_id: int, profile: dict) -> int:
        """
        Insert a row into `profiles` and return the generated profile_id.

        profile keys: cycle_number, direction, latitude, longitude,
                      position_qc, observed_at (ISO string or None)
        """
        cursor.execute(
            """
            INSERT INTO profiles (file_id, cycle_number, direction, latitude, longitude,
                                  position_qc, observed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING profile_id
            """,
            (
                file_id,
                profile.get("cycle_number"),
                profile.get("direction"),
                profile.get("latitude"),
                profile.get("longitude"),
                profile.get("position_qc"),
                profile.get("observed_at"),  # TIMESTAMP — psycopg2 accepts ISO strings
            ),
        )
        return cursor.fetchone()[0]

    # ── measurements ──────────────────────────────────────────────────────────

    def insert_measurements_batch(self, cursor, measurements: list[dict]):
        """
        Bulk-insert measurement rows using execute_values (500 rows per page).

        Each dict must contain a 'profile_id' key plus the measurement columns.
        """
        if not measurements:
            return

        psycopg2.extras.execute_values(
            cursor,
            """
            INSERT INTO measurements (
                profile_id,
                depth_level,
                pressure,             pressure_qc,
                pressure_adjusted,    pressure_adjusted_qc,
                temperature,          temperature_qc,
                temperature_adjusted, temperature_adjusted_qc,
                salinity,             salinity_qc,
                salinity_adjusted,    salinity_adjusted_qc
            ) VALUES %s
            """,
            [
                (
                    m["profile_id"],
                    m.get("depth_level"),
                    m.get("pressure"),              m.get("pressure_qc"),
                    m.get("pressure_adjusted"),     m.get("pressure_adjusted_qc"),
                    m.get("temperature"),           m.get("temperature_qc"),
                    m.get("temperature_adjusted"),  m.get("temperature_adjusted_qc"),
                    m.get("salinity"),              m.get("salinity_qc"),
                    m.get("salinity_adjusted"),     m.get("salinity_adjusted_qc"),
                )
                for m in measurements
            ],
            page_size=500,
        )