
from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
    update_bq,
)
from datetime import datetime

from core.knowledge.cockpit_repository import (
    list_entities,
)

from core.knowledge.service import (
    update_knowledge,
)

from core.content.ai import (
    generate_topics_concepts,
)

from core.content.relation_service import (
    resolve_topics,
    resolve_concepts,
)




# ============================================================
# TABLES
# ============================================================

TABLE_CONTENT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT"
)

TABLE_CONTENT_RAW = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_RAW"
)

TABLE_CONTENT_ENRICHED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_ENRICHED"
)

TABLE_CONTENT_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_COMPANY"
)

TABLE_CONTENT_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_SOLUTION"
)

TABLE_CONTENT_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC"
)

TABLE_CONTENT_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT"
)

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_COMPANY_ALIAS"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOLUTION_ALIAS"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC"
)

TABLE_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT"
)

TABLE_SOURCE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE"
)

TABLE_SOURCE_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_SOURCE_UNIVERSE"
)

TABLE_UNIVERSE = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_UNIVERSE"
)

TABLE_ALIAS_REJECTED = (
    f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_ALIAS_REJECTED"
)


# ============================================================
# DATASETS
# ============================================================
DATASET_PROD = "GETCURATOR_PROD"
DATASET_DEV = "GETCURATOR_DEV"
DATASET_BACKUP = "GETCURATOR_BACKUP"

# ============================================================
# BACKUP TABLES
# ============================================================

BACKUP_TABLES = [

    # Companies
    "RATECARD_COMPANY",
    "RATECARD_COMPANY_ALIAS",
    "RATECARD_COMPANY_TYPE",
    "RATECARD_COMPANY_UNIVERSE",

    # Concepts
    "RATECARD_CONCEPT",

    # Content
    "RATECARD_CONTENT",
    "RATECARD_CONTENT_ENRICHED",
    "RATECARD_CONTENT_COMPANY",
    "RATECARD_CONTENT_CONCEPT",
    "RATECARD_CONTENT_RAW",
    "RATECARD_CONTENT_SOLUTION",
    "RATECARD_CONTENT_TOPIC",

    # Intelligence
    "RATECARD_DIGEST",
    "RATECARD_CAMPAIGN",
    "RATECARD_KNOWLEDGE",
    "RATECARD_KNOWLEDGE_STATUS",

    # Numbers
    "RATECARD_NUMBERS",
    "RATECARD_NUMBERS_BACKLOG",
    "RATECARD_NUMBERS_COMPANY",
    "RATECARD_NUMBERS_SOLUTION",
    "RATECARD_NUMBERS_TOPIC",
    "RATECARD_NUMBERS_TYPE",
    "RATECARD_NUMBER_OBSERVATION",
    "RATECARD_NUMBER_PROCESSING",
    "RATECARD_NUMBER_OBSERVATION_ENTITY",
    "RATECARD_NUMBER_OBSERVATION_REVIEW",

    # Solutions
    "RATECARD_SOLUTION",
    "RATECARD_SOLUTION_ALIAS",

    # Sources
    "RATECARD_SOURCE",
    "RATECARD_SOURCE_DISCOVERY",
    "RATECARD_SOURCE_UNIVERSE",

    # Topics
    "RATECARD_TOPIC",
    "RATECARD_TOPIC_UNIVERSE",

    # Universes
    "RATECARD_UNIVERSE",

    # Users
    "RATECARD_USER",
    "RATECARD_USER_KEYWORD",
    "RATECARD_USER_PROFILE",
    "RATECARD_USER_PREFERENCES",
    "RATECARD_USER_UNIVERSE",
    "RATECARD_USER_EXPERT",

    # Matching
    "RATECARD_ALIAS_REJECTED",

]
# ============================================================
# INTERNAL
# ============================================================

def _run_operation(
    sql: str,
    message: str,
):

    query_bq(sql)

    return {
        "status": "ok",
        "message": message,
    }


# ============================================================
# PUBLISHING
# ============================================================

def publish_all_drafts():

    sql = f"""
    UPDATE `{TABLE_CONTENT}`

    SET
        STATUS = 'PUBLISHED',

        PUBLISHED_AT = CASE
            WHEN SOURCE_DATE IS NOT NULL
             AND TIMESTAMP(SOURCE_DATE) <= CURRENT_TIMESTAMP()
                THEN TIMESTAMP(SOURCE_DATE)
            ELSE CURRENT_TIMESTAMP()
        END,

        UPDATED_AT = CURRENT_TIMESTAMP()

    WHERE STATUS = 'DRAFT'
    """

    return _run_operation(
        sql,
        "All draft contents have been published.",
    )


# ============================================================
# MAINTENANCE
# ============================================================

def rebuild_content_company():

    sql = f"""
    INSERT INTO `{TABLE_CONTENT_COMPANY}` (
        ID_CONTENT,
        ID_COMPANY
    )

    SELECT DISTINCT
        c.ID_CONTENT,
        a.ID_COMPANY

    FROM `{TABLE_CONTENT}` c,
    UNNEST(c.ACTEURS_CITES) AS raw

    JOIN `{TABLE_COMPANY_ALIAS}` a
      ON REGEXP_REPLACE(
            UPPER(TRIM(raw)),
            r'[^A-Z0-9 ]',
            ''
         )
       =
         REGEXP_REPLACE(
            UPPER(TRIM(a.ALIAS)),
            r'[^A-Z0-9 ]',
            ''
         )

    WHERE raw IS NOT NULL
      AND TRIM(raw) != ""

      AND NOT EXISTS (

          SELECT 1

          FROM `{TABLE_CONTENT_COMPANY}` existing

          WHERE
              existing.ID_CONTENT = c.ID_CONTENT
          AND existing.ID_COMPANY = a.ID_COMPANY

      )
    """

    return _run_operation(
        sql,
        "Content → Company rebuilt.",
    )


# ============================================================

def rebuild_content_solution():

    sql = f"""
    INSERT INTO `{TABLE_CONTENT_SOLUTION}` (
        ID_CONTENT,
        ID_SOLUTION
    )

    SELECT DISTINCT
        c.ID_CONTENT,
        a.ID_SOLUTION

    FROM `{TABLE_CONTENT}` c,

    UNNEST(
        ARRAY_CONCAT(
            IFNULL(c.SOLUTIONS_LLM, []),
            IFNULL(c.ACTEURS_CITES, [])
        )
    ) AS raw

    JOIN `{TABLE_SOLUTION_ALIAS}` a
      ON REGEXP_REPLACE(
            UPPER(TRIM(raw)),
            r'[^A-Z0-9 ]',
            ''
         )
       =
         REGEXP_REPLACE(
            UPPER(TRIM(a.ALIAS)),
            r'[^A-Z0-9 ]',
            ''
         )

    WHERE raw IS NOT NULL
      AND TRIM(raw) != ""

      AND NOT EXISTS (

          SELECT 1

          FROM `{TABLE_CONTENT_SOLUTION}` existing

          WHERE
              existing.ID_CONTENT = c.ID_CONTENT
          AND existing.ID_SOLUTION = a.ID_SOLUTION

      )
    """

    return _run_operation(
        sql,
        "Content → Solution rebuilt.",
    )


# ============================================================
# POPULATE CONTENT_ENRICHED
# ============================================================

def populate_content_enriched():

    # --------------------------------------------------------
    # CLEAN TABLE
    # --------------------------------------------------------

    query_bq(
        f"""
        TRUNCATE TABLE `{TABLE_CONTENT_ENRICHED}`
        """
    )

    # --------------------------------------------------------
    # REBUILD
    # --------------------------------------------------------

    sql = f"""
    INSERT INTO `{TABLE_CONTENT_ENRICHED}` (

        id_content,
        source_id,

        id_raw,
        source_url,
        source_title,

        title,
        title_en,
        excerpt,
        excerpt_en,
        content_body,
        content_body_en,

        signal_analytique,
        signal_analytique_en,

        mecanique_expliquee,
        mecanique_expliquee_en,

        enjeu_strategique,
        enjeu_strategique_en,

        point_de_friction,
        point_de_friction_en,

        chiffres,
        acteurs_cites,

        concepts_llm,
        solutions_llm,
        topics_llm,

        status,
        is_active,

        source_date,
        published_at,
        created_at,
        updated_at,

        universes,
        topics,
        companies,
        solutions,
        concepts,

        CONTENT_TYPE,
        ID_PRIMARY_COMPANY
    )

    SELECT

        c.ID_CONTENT AS id_content,

        c.SOURCE_ID AS source_id,

        c.ID_RAW AS id_raw,

        c.SOURCE_URL AS source_url,

        c.SOURCE_TITLE AS source_title,

        c.TITLE AS title,

        c.TITLE_EN AS title_en,

        c.EXCERPT AS excerpt,

        c.EXCERPT_EN AS excerpt_en,

        c.CONTENT_BODY AS content_body,

        c.CONTENT_BODY_EN AS content_body_en,

        c.SIGNAL_ANALYTIQUE AS signal_analytique,

        c.SIGNAL_ANALYTIQUE_EN AS signal_analytique_en,

        c.MECANIQUE_EXPLIQUEE AS mecanique_expliquee,

        c.MECANIQUE_EXPLIQUEE_EN AS mecanique_expliquee_en,

        c.ENJEU_STRATEGIQUE AS enjeu_strategique,

        c.ENJEU_STRATEGIQUE_EN AS enjeu_strategique_en,

        c.POINT_DE_FRICTION AS point_de_friction,

        c.POINT_DE_FRICTION_EN AS point_de_friction_en,

        c.CHIFFRES AS chiffres,

        c.ACTEURS_CITES AS acteurs_cites,

        c.CONCEPTS_LLM AS concepts_llm,

        c.SOLUTIONS_LLM AS solutions_llm,

        c.TOPICS_LLM AS topics_llm,

        c.STATUS AS status,

        c.IS_ACTIVE AS is_active,

        c.SOURCE_DATE AS source_date,

        c.PUBLISHED_AT AS published_at,

        c.CREATED_AT AS created_at,

        c.UPDATED_AT AS updated_at,

         -- ========================================================
    -- UNIVERSES (🔥 SOURCE BASED)
    -- ========================================================

    ARRAY(
        SELECT DISTINCT AS STRUCT
            u.ID_UNIVERSE AS id_universe,
            u.LABEL AS label

        FROM `{TABLE_SOURCE_UNIVERSE}` su

        JOIN `{TABLE_UNIVERSE}` u
          ON su.ID_UNIVERSE = u.ID_UNIVERSE

        WHERE su.ID_SOURCE = c.SOURCE_ID
    ) AS universes,

    -- ========================================================
    -- TOPICS
    -- ========================================================

    ARRAY(
        SELECT DISTINCT AS STRUCT
            t.ID_TOPIC AS id_topic,
            t.LABEL AS label,
            t.TOPIC_AXIS AS topic_axis

        FROM `{TABLE_CONTENT_TOPIC}` ct

        JOIN `{TABLE_TOPIC}` t
          ON ct.ID_TOPIC = t.ID_TOPIC

        WHERE ct.ID_CONTENT = c.ID_CONTENT
    ) AS topics,

    -- ========================================================
    -- COMPANIES
    -- ========================================================

    ARRAY(
        SELECT DISTINCT AS STRUCT
            co.ID_COMPANY AS id_company,
            co.NAME AS name,
            co.MEDIA_LOGO_RECTANGLE_ID AS media_logo_rectangle_id

        FROM `{TABLE_CONTENT_COMPANY}` cc

        JOIN `{TABLE_COMPANY}` co
          ON cc.ID_COMPANY = co.ID_COMPANY

        WHERE cc.ID_CONTENT = c.ID_CONTENT
    ) AS companies,

    -- ========================================================
    -- SOLUTIONS
    -- ========================================================

    ARRAY(
        SELECT DISTINCT AS STRUCT
            s.ID_SOLUTION AS id_solution,
            s.NAME AS name

        FROM `{TABLE_CONTENT_SOLUTION}` cs

        JOIN `{TABLE_SOLUTION}` s
          ON cs.ID_SOLUTION = s.ID_SOLUTION

        WHERE cs.ID_CONTENT = c.ID_CONTENT
    ) AS solutions,

    -- ========================================================
    -- CONCEPTS
    -- ========================================================

    ARRAY(
        SELECT DISTINCT AS STRUCT
            cp.ID_CONCEPT AS id_concept,
            cpt.LABEL AS label

        FROM `{TABLE_CONTENT_CONCEPT}` cp

        JOIN `{TABLE_CONCEPT}` cpt
          ON cp.ID_CONCEPT = cpt.ID_CONCEPT

        WHERE cp.ID_CONTENT = c.ID_CONTENT
    ) AS concepts,

    c.CONTENT_TYPE AS CONTENT_TYPE,

    c.ID_PRIMARY_COMPANY AS ID_PRIMARY_COMPANY

FROM `{TABLE_CONTENT}` c

WHERE
    c.STATUS = 'PUBLISHED'
    """

    query_bq(sql)

    return {
        "status": "ok",
        "message": "CONTENT_ENRICHED refreshed.",
    }


# ============================================================
# CONTINUE KNOWLEDGE
# ============================================================

def continue_all_knowledge():
    """
    Continue every Knowledge that:

    - has already started
    - has new/unprocessed contents

    Never starts a Knowledge from zero.

    Entities are processed sequentially.
    """

    explorer = list_entities()

    eligible = [

        entity

        for entity in explorer.entities

        if (
            entity.processed_contents > 0
            and
            entity.processed_contents
            < entity.contents_count
        )

    ]

    processed = 0

    failed = 0

    errors = []

    # ========================================================
    # SEQUENTIAL PROCESSING
    # ========================================================

    for entity in eligible:

        try:

            print(
                "[KNOWLEDGE CONTINUE]",
                entity.entity_type,
                entity.name,
                f"{entity.processed_contents}/{entity.contents_count}",
            )

            update_knowledge(

                entity_type=
                    entity.entity_type,

                entity_id=
                    entity.entity_id,

                auto_continue=True,

            )

            processed += 1

        except Exception as e:

            failed += 1

            errors.append({

                "entity_type":
                    entity.entity_type,

                "entity_id":
                    entity.entity_id,

                "name":
                    entity.name,

                "error":
                    str(e),

            })

            print(
                "[KNOWLEDGE CONTINUE ERROR]",
                entity.entity_type,
                entity.name,
                str(e),
            )

    # ========================================================
    # RESULT
    # ========================================================

    return {

        "status":
            "ok"
            if failed == 0
            else "partial",

        "message":
            (
                f"{processed} Knowledge entities updated"
                f" · {failed} failed"
            ),

        "eligible":
            len(eligible),

        "processed":
            processed,

        "failed":
            failed,

        "errors":
            errors,

    }


# ============================================================
# MATCHING FULL DISMISS
# ============================================================

def matching_full_dismiss():

    sql = f"""
    INSERT INTO `{TABLE_ALIAS_REJECTED}`
    (
      ID_REJECTED,
      ALIAS,
      ENTITY_TYPE,
      FIRST_SEEN_AT,
      LAST_SEEN_AT,
      NB_OCCURRENCES,
      STATUS
    )

    WITH entities AS (

      SELECT
        entity,
        COUNT(*) AS nb_occurrences

      FROM `{TABLE_CONTENT}`,
      UNNEST(
        ARRAY_CONCAT(
          IFNULL(ACTEURS_CITES, []),
          IFNULL(SOLUTIONS_LLM, [])
        )
      ) AS entity

      WHERE entity IS NOT NULL
        AND TRIM(entity) != ''

      GROUP BY entity

    ),

    processed AS (

      SELECT UPPER(TRIM(ALIAS)) AS alias
      FROM `{TABLE_COMPANY_ALIAS}`

      UNION DISTINCT

      SELECT UPPER(TRIM(ALIAS))
      FROM `{TABLE_SOLUTION_ALIAS}`

      UNION DISTINCT

      SELECT UPPER(TRIM(ALIAS))
      FROM `{TABLE_ALIAS_REJECTED}`

    )

    SELECT
      GENERATE_UUID(),
      entity,
      'unknown',
      CURRENT_TIMESTAMP(),
      CURRENT_TIMESTAMP(),
      CAST(nb_occurrences AS STRING),
      'REJECTED'

    FROM entities e

    LEFT JOIN processed p
      ON UPPER(TRIM(e.entity)) = p.alias

    WHERE p.alias IS NULL
    """

    return _run_operation(
        sql,
        "Unknown aliases dismissed.",
    )

# ============================================================
# BACKFILL TOPICS + CONCEPTS
# TEMPORARY — CONTENTS SINCE 2026-08-23
# ============================================================

def backfill_topics_concepts(
    limit: int = 5000,
    batch_size: int = 50,
):

    # ========================================================
    # LOAD CONTENTS
    # ========================================================

    rows = query_bq(
        f"""
        SELECT
            c.ID_CONTENT,
            c.ID_RAW,
            c.SOURCE_ID,
            r.RAW_TEXT

        FROM `{TABLE_CONTENT}` c

        JOIN `{TABLE_CONTENT_RAW}` r
          ON r.ID_RAW = c.ID_RAW

        WHERE
            c.CREATED_AT >= TIMESTAMP('2026-08-23')

            AND (
                c.TOPICS_LLM IS NULL
                OR ARRAY_LENGTH(c.TOPICS_LLM) = 0
            )

            AND (
                c.CONCEPTS_LLM IS NULL
                OR ARRAY_LENGTH(c.CONCEPTS_LLM) = 0
            )

        ORDER BY c.CREATED_AT ASC

        LIMIT {int(limit)}
        """
    )

    if not rows:

        return {
            "status": "ok",
            "processed": 0,
            "failed": 0,
            "remaining": 0,
            "message":
                "Topics / Concepts backfill complete.",
        }

    # ========================================================
    # LOAD REFERENCE MAPS ONCE
    # ========================================================

    topic_rows = query_bq(
        f"""
        SELECT
            ID_TOPIC,
            LABEL

        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_TOPIC`

        WHERE IS_ACTIVE = TRUE
        """
    )

    concept_rows = query_bq(
        f"""
        SELECT
            ID_CONCEPT,
            LABEL

        FROM `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONCEPT`

        WHERE IS_ACTIVE = TRUE
        """
    )

    topic_map = {
        row["LABEL"]: row["ID_TOPIC"]
        for row in topic_rows
    }

    concept_map = {
        row["LABEL"]: row["ID_CONCEPT"]
        for row in concept_rows
    }

    # ========================================================
    # FLUSH BATCH
    # ========================================================

    def flush_batch(
        batch,
    ):

        if not batch:
            return

        # ----------------------------------------------------
        # CONTENT ARRAYS
        # ----------------------------------------------------

        values = []

        for item in batch:

            topics_sql = (
                "["
                + ",".join(
                    "'" + topic.replace(
                        "'",
                        "\\'",
                    ) + "'"
                    for topic in item["topics"]
                )
                + "]"
            )

            concepts_sql = (
                "["
                + ",".join(
                    "'" + concept.replace(
                        "'",
                        "\\'",
                    ) + "'"
                    for concept in item["concepts"]
                )
                + "]"
            )

            values.append(
                f"""
                STRUCT(
                    '{item["id_content"]}'
                        AS ID_CONTENT,
                    {topics_sql}
                        AS TOPICS_LLM,
                    {concepts_sql}
                        AS CONCEPTS_LLM
                )
                """
            )

        query_bq(
            f"""
            MERGE `{TABLE_CONTENT}` target

            USING (
                SELECT *
                FROM UNNEST([
                    {",".join(values)}
                ])
            ) source

            ON
                target.ID_CONTENT =
                source.ID_CONTENT

            WHEN MATCHED THEN
                UPDATE SET
                    TOPICS_LLM =
                        source.TOPICS_LLM,
                    CONCEPTS_LLM =
                        source.CONCEPTS_LLM
            """
        )

        # ----------------------------------------------------
        # TOPIC RELATIONS
        # ----------------------------------------------------

        topic_relations = []

        for item in batch:

            for label in item["topics"]:

                id_topic = topic_map.get(
                    label
                )

                if not id_topic:
                    continue

                topic_relations.append(
                    f"""
                    STRUCT(
                        '{item["id_content"]}'
                            AS ID_CONTENT,
                        '{id_topic}'
                            AS ID_TOPIC
                    )
                    """
                )

        if topic_relations:

            query_bq(
                f"""
                INSERT INTO
                    `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC`
                    (
                        ID_CONTENT,
                        ID_TOPIC
                    )

                SELECT
                    source.ID_CONTENT,
                    source.ID_TOPIC

                FROM UNNEST([
                    {",".join(topic_relations)}
                ]) source

                WHERE NOT EXISTS (

                    SELECT 1

                    FROM
                        `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_TOPIC`
                        existing

                    WHERE
                        existing.ID_CONTENT =
                        source.ID_CONTENT

                    AND
                        existing.ID_TOPIC =
                        source.ID_TOPIC
                )
                """
            )

        # ----------------------------------------------------
        # CONCEPT RELATIONS
        # ----------------------------------------------------

        concept_relations = []

        for item in batch:

            for label in item[
                "concepts"
            ]:

                id_concept = concept_map.get(
                    label
                )

                if not id_concept:
                    continue

                concept_relations.append(
                    f"""
                    STRUCT(
                        '{item["id_content"]}'
                            AS ID_CONTENT,
                        '{id_concept}'
                            AS ID_CONCEPT
                    )
                    """
                )

        if concept_relations:

            query_bq(
                f"""
                INSERT INTO
                    `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT`
                    (
                        ID_CONTENT,
                        ID_CONCEPT
                    )

                SELECT
                    source.ID_CONTENT,
                    source.ID_CONCEPT

                FROM UNNEST([
                    {",".join(concept_relations)}
                ]) source

                WHERE NOT EXISTS (

                    SELECT 1

                    FROM
                        `{BQ_PROJECT}.{BQ_DATASET}.RATECARD_CONTENT_CONCEPT`
                        existing

                    WHERE
                        existing.ID_CONTENT =
                        source.ID_CONTENT

                    AND
                        existing.ID_CONCEPT =
                        source.ID_CONCEPT
                )
                """
            )

        print(
            "[TOPICS CONCEPTS FLUSH]",
            len(batch),
            "contents",
        )

    # ========================================================
    # GENERATE
    # ========================================================

    batch = []

    processed = 0
    failed = 0
    errors = []

    for row in rows:

        id_content = row[
            "ID_CONTENT"
        ]

        try:

            result = generate_topics_concepts(
                source_id=row.get(
                    "SOURCE_ID"
                ),
                source_text=row.get(
                    "RAW_TEXT"
                ) or "",
            )

            batch.append(
                {
                    "id_content":
                        id_content,

                    "topics":
                        result.get(
                            "topics_llm"
                        )
                        or [],

                    "concepts":
                        result.get(
                            "concepts_llm"
                        )
                        or [],
                }
            )

            print(
                "[TOPICS CONCEPTS GENERATED]",
                id_content,
            )

            # ------------------------------------------------
            # FLUSH EVERY N CONTENTS
            # ------------------------------------------------

            if len(batch) >= batch_size:

                flush_batch(
                    batch,
                )

                processed += len(
                    batch
                )

                batch = []

                print(
                    "[TOPICS CONCEPTS PROGRESS]",
                    processed,
                    "/",
                    len(rows),
                )

        except Exception as e:

            failed += 1

            errors.append(
                {
                    "id_content":
                        id_content,

                    "error":
                        str(e),
                }
            )

            print(
                "[TOPICS CONCEPTS ERROR]",
                id_content,
                str(e),
            )

    # ========================================================
    # FINAL BATCH
    # ========================================================

    if batch:

        flush_batch(
            batch,
        )

        processed += len(
            batch
        )

    # ========================================================
    # REMAINING
    # ========================================================

    remaining_rows = query_bq(
        f"""
        SELECT
            COUNT(*) AS total

        FROM `{TABLE_CONTENT}`

        WHERE
            CREATED_AT >= TIMESTAMP('2026-08-23')

            AND (
                TOPICS_LLM IS NULL
                OR ARRAY_LENGTH(TOPICS_LLM) = 0
            )

            AND (
                CONCEPTS_LLM IS NULL
                OR ARRAY_LENGTH(CONCEPTS_LLM) = 0
            )
        """
    )

    remaining = (
        remaining_rows[0]["total"]
        if remaining_rows
        else 0
    )

    return {
        "status":
            "ok"
            if failed == 0
            else "partial",

        "processed":
            processed,

        "failed":
            failed,

        "remaining":
            remaining,

        "errors":
            errors,

        "message":
            (
                f"{processed} contents backfilled"
                f" · {failed} failed"
                f" · {remaining} remaining"
            ),
    }


# ============================================================
# DATASET COPY
# ============================================================

def _copy_dataset(
    source_dataset: str,
    target_dataset: str,
):

    copied = []

    for table in BACKUP_TABLES:

        source_table = (
            f"{BQ_PROJECT}."
            f"{source_dataset}."
            f"{table}"
        )

        target_table = (
            f"{BQ_PROJECT}."
            f"{target_dataset}."
            f"{table}"
        )

        print(
            "[DATASET COPY]",
            source_table,
            "→",
            target_table,
        )

        # La table cible est supprimée pour éviter les conflits
        # de partitionnement et de clustering.
        query_bq(
            f"""
            DROP TABLE IF EXISTS `{target_table}`
            """
        )

        # CLONE conserve la structure physique de la source :
        # schéma, partitionnement et clustering.
        query_bq(
            f"""
            CREATE TABLE `{target_table}`
            CLONE `{source_table}`
            """
        )

        copied.append(table)

        print(
            "[DATASET COPY OK]",
            table,
        )

    return copied


# ============================================================
# BACKUP PROD
# ============================================================

def backup_prod():

    _copy_dataset(
        DATASET_PROD,
        DATASET_BACKUP,
    )

    return {
        "status": "ok",
        "message": "Production backed up.",
    }

# ============================================================
# SYNC PROD → DEV
# ============================================================

def sync_prod_to_dev():

    _copy_dataset(
        DATASET_PROD,
        DATASET_DEV,
    )

    return {
        "status": "ok",
        "message": "Development synchronized.",
    }

# ============================================================
# RESTART DESTOCK
# ============================================================

def restart_destock():

    sql = f"""
    UPDATE `{TABLE_CONTENT_RAW}`
    SET STATUS = 'STORED'

    WHERE STATUS = 'STOPPED'

    AND DATE_SOURCE BETWEEN
        DATE '2026-01-01'
        AND DATE '2026-05-06'
    """

    return _run_operation(
        sql,
        "Destock restarted.",
    )


