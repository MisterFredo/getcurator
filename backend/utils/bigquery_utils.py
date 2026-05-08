import os
import json
from datetime import datetime, date
from google.cloud import bigquery
from google.oauth2 import service_account


# ---------------------------------------------------------
# Client BigQuery (version minimaliste pour Ratecard)
# ---------------------------------------------------------
def get_bigquery_client() -> bigquery.Client:
    """
    Crée un client BigQuery dans la région correcte.
    """
    credentials_path = os.environ.get("GOOGLE_CREDENTIALS_FILE")

    if credentials_path:
        with open(credentials_path, "r") as f:
            info = json.load(f)
        credentials = service_account.Credentials.from_service_account_info(info)
        project_id = info.get("project_id")
        return bigquery.Client(
            credentials=credentials,
            project=project_id,
            location="EU"   # 🔥 FORCE LA RÉGION CORRECTE
        )

    # Local dev ou ADC
    return bigquery.Client(location="EU")


# ---------------------------------------------------------
# Helpers : inférer le type BigQuery standard
# ---------------------------------------------------------
def _infer_type(value):
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, int):
        return "INT64"
    if isinstance(value, float):
        return "FLOAT64"
    if isinstance(value, datetime):
        return "TIMESTAMP"
    if isinstance(value, date):
        return "DATE"
    return "STRING"


# ---------------------------------------------------------
# Requête BigQuery (SELECT)
# ---------------------------------------------------------
def query_bq(sql: str, params: dict = None) -> list[dict]:
    """
    Exécute une requête SELECT sur BigQuery.
    Supporte automatiquement les paramètres ARRAY.
    """

    client = get_bigquery_client()

    job_config = None

    if params:
        query_parameters = []

        for name, value in params.items():

            # 🔥 CAS ARRAY (LIST)
            if isinstance(value, list):

                # 👉 FIX CRITIQUE : array vide sécurisé
                if len(value) == 0:
                    value = ["__EMPTY__"]  # valeur impossible

                query_parameters.append(
                    bigquery.ArrayQueryParameter(
                        name,
                        "STRING",
                        value
                    )
                )

            # 🔥 CAS INT
            elif isinstance(value, int):
                query_parameters.append(
                    bigquery.ScalarQueryParameter(
                        name,
                        "INT64",
                        value
                    )
                )

            # 🔥 CAS AUTRES
            else:
                query_parameters.append(
                    bigquery.ScalarQueryParameter(
                        name,
                        _infer_type(value),
                        value
                    )
                )

        job_config = bigquery.QueryJobConfig(
            query_parameters=query_parameters
        )

    job = client.query(sql, job_config=job_config)

    return [dict(row) for row in job.result()]


# ---------------------------------------------------------
# Insertion BigQuery (INSERT SQL, PAS de streaming)
# ---------------------------------------------------------
def insert_bq(table: str, rows: list[dict]):
    """
    Insère des lignes dans une table BigQuery via INSERT SQL
    (évite le streaming buffer pour permettre UPDATE immédiat).
    """
    client = get_bigquery_client()

    for row in rows:
        columns = []
        placeholders = []
        params = []

        for key, value in row.items():
            columns.append(key)
            placeholders.append(f"@{key}")

            # Conversion datetime/date propre
            if hasattr(value, "isoformat"):
                value = value.isoformat()

            params.append(
                bigquery.ScalarQueryParameter(
                    key,
                    _infer_type(value),
                    value
                )
            )

        sql = f"""
            INSERT INTO `{table}` ({", ".join(columns)})
            VALUES ({", ".join(placeholders)})
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=params
        )

        client.query(sql, job_config=job_config).result()


# ---------------------------------------------------------
# Mise à jour BigQuery (UPDATE SQL CANONIQUE)
# ---------------------------------------------------------
def update_bq(table: str, fields: dict, where: dict) -> bool:
    """
    Exécute un UPDATE BigQuery sécurisé avec paramètres typés.

    fields = {"COL": value}
    where = {"ID": value}
    """

    if not fields:
        return False

    client = get_bigquery_client()

    set_clause = []
    where_clause = []
    params = []

    # ==========================================================
    # SET
    # ==========================================================
    for k, v in fields.items():

        set_clause.append(f"{k} = @{k}")

        # 🔥 ARRAY<STRING>
        if isinstance(v, list):
            params.append(
                bigquery.ArrayQueryParameter(
                    k,
                    "STRING",
                    v
                )
            )

        # 🔥 TIMESTAMP
        elif isinstance(v, datetime):
            params.append(
                bigquery.ScalarQueryParameter(
                    k,
                    "TIMESTAMP",
                    v
                )
            )

        # 🔥 DATE
        elif isinstance(v, date):
            params.append(
                bigquery.ScalarQueryParameter(
                    k,
                    "DATE",
                    v
                )
            )

        # 🔥 BOOL
        elif isinstance(v, bool):
            params.append(
                bigquery.ScalarQueryParameter(
                    k,
                    "BOOL",
                    v
                )
            )

        # 🔥 INT
        elif isinstance(v, int):
            params.append(
                bigquery.ScalarQueryParameter(
                    k,
                    "INT64",
                    v
                )
            )

        # 🔥 FLOAT
        elif isinstance(v, float):
            params.append(
                bigquery.ScalarQueryParameter(
                    k,
                    "FLOAT64",
                    v
                )
            )

        # 🔥 STRING / fallback
        else:
            params.append(
                bigquery.ScalarQueryParameter(
                    k,
                    "STRING",
                    v
                )
            )

    # ==========================================================
    # WHERE
    # ==========================================================
    for k, v in where.items():

        where_key = f"where_{k}"
        where_clause.append(f"{k} = @{where_key}")

        if isinstance(v, datetime):
            params.append(
                bigquery.ScalarQueryParameter(
                    where_key,
                    "TIMESTAMP",
                    v
                )
            )

        elif isinstance(v, date):
            params.append(
                bigquery.ScalarQueryParameter(
                    where_key,
                    "DATE",
                    v
                )
            )

        elif isinstance(v, bool):
            params.append(
                bigquery.ScalarQueryParameter(
                    where_key,
                    "BOOL",
                    v
                )
            )

        elif isinstance(v, int):
            params.append(
                bigquery.ScalarQueryParameter(
                    where_key,
                    "INT64",
                    v
                )
            )

        elif isinstance(v, float):
            params.append(
                bigquery.ScalarQueryParameter(
                    where_key,
                    "FLOAT64",
                    v
                )
            )

        else:
            params.append(
                bigquery.ScalarQueryParameter(
                    where_key,
                    "STRING",
                    v
                )
            )

    # ==========================================================
    # EXECUTION
    # ==========================================================
    sql = f"""
        UPDATE `{table}`
        SET {", ".join(set_clause)}
        WHERE {" AND ".join(where_clause)}
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=params
    )

    client.query(sql, job_config=job_config).result()

    return True
