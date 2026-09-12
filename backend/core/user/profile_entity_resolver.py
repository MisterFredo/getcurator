import re
import unicodedata

from typing import (
    Dict,
    List,
    Optional,
    Tuple,
)

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from core.user.profile_models import (
    ProfileEntityReference,
    StructuredUserProfile,
)

from utils.bigquery_utils import (
    query_bq,
)


# ============================================================
# TABLES
# ============================================================

TABLE_COMPANY = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_COMPANY"
)

TABLE_COMPANY_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_COMPANY_ALIAS"
)

TABLE_SOLUTION = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_SOLUTION"
)

TABLE_SOLUTION_ALIAS = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_SOLUTION_ALIAS"
)

TABLE_TOPIC = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_TOPIC"
)

TABLE_CONCEPT = (
    f"{BQ_PROJECT}.{BQ_DATASET}."
    "RATECARD_CONCEPT"
)


# ============================================================
# TYPES
# ============================================================

CatalogEntry = Dict[
    str,
    str,
]

CatalogIndex = Dict[
    str,
    List[CatalogEntry],
]

Catalogs = Dict[
    str,
    CatalogIndex,
]


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_entity_label(
    value: Optional[str],
) -> str:

    if not value:

        return ""

    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    normalized = (
        normalized
        .casefold()
        .strip()
    )

    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


# ============================================================
# INDEX HELPERS
# ============================================================

def add_catalog_entry(
    index: CatalogIndex,
    lookup_label: Optional[str],
    entity_id: Optional[str],
    canonical_label: Optional[str],
    entity_type: str,
) -> None:

    normalized_label = normalize_entity_label(
        lookup_label
    )

    if (
        not normalized_label
        or not entity_id
        or not canonical_label
    ):

        return

    entry: CatalogEntry = {
        "entity_id": entity_id,
        "canonical_label": canonical_label,
        "entity_type": entity_type,
    }

    existing_entries = index.setdefault(
        normalized_label,
        [],
    )

    already_exists = any(
        existing_entry["entity_id"]
        == entity_id

        for existing_entry
        in existing_entries
    )

    if not already_exists:

        existing_entries.append(
            entry
        )


# ============================================================
# LOAD COMPANIES
# ============================================================

def load_company_index() -> CatalogIndex:

    index: CatalogIndex = {}

    company_rows = query_bq(
        f"""
        SELECT
            ID_COMPANY,
            NAME
        FROM `{TABLE_COMPANY}`
        WHERE IS_ACTIVE = TRUE
        """,
        {},
    )

    for row in company_rows:

        add_catalog_entry(
            index=index,
            lookup_label=row.get("NAME"),
            entity_id=row.get("ID_COMPANY"),
            canonical_label=row.get("NAME"),
            entity_type="company",
        )

    alias_rows = query_bq(
        f"""
        SELECT
            alias_table.ALIAS,
            company.ID_COMPANY,
            company.NAME
        FROM `{TABLE_COMPANY_ALIAS}`
            AS alias_table
        INNER JOIN `{TABLE_COMPANY}`
            AS company
            ON company.ID_COMPANY =
               alias_table.ID_COMPANY
        WHERE
            alias_table.MATCH_STATUS = 'MATCH'
            AND alias_table.ID_COMPANY IS NOT NULL
            AND company.IS_ACTIVE = TRUE
        """,
        {},
    )

    for row in alias_rows:

        add_catalog_entry(
            index=index,
            lookup_label=row.get("ALIAS"),
            entity_id=row.get("ID_COMPANY"),
            canonical_label=row.get("NAME"),
            entity_type="company",
        )

    return index


# ============================================================
# LOAD SOLUTIONS
# ============================================================

def load_solution_index() -> CatalogIndex:

    index: CatalogIndex = {}

    solution_rows = query_bq(
        f"""
        SELECT
            ID_SOLUTION,
            NAME
        FROM `{TABLE_SOLUTION}`
        WHERE IS_ACTIVE = TRUE
        """,
        {},
    )

    for row in solution_rows:

        add_catalog_entry(
            index=index,
            lookup_label=row.get("NAME"),
            entity_id=row.get("ID_SOLUTION"),
            canonical_label=row.get("NAME"),
            entity_type="solution",
        )

    alias_rows = query_bq(
        f"""
        SELECT
            alias_table.ALIAS,
            solution.ID_SOLUTION,
            solution.NAME
        FROM `{TABLE_SOLUTION_ALIAS}`
            AS alias_table
        INNER JOIN `{TABLE_SOLUTION}`
            AS solution
            ON solution.ID_SOLUTION =
               alias_table.ID_SOLUTION
        WHERE
            alias_table.MATCH_STATUS = 'MATCH'
            AND alias_table.ID_SOLUTION IS NOT NULL
            AND solution.IS_ACTIVE = TRUE
        """,
        {},
    )

    for row in alias_rows:

        add_catalog_entry(
            index=index,
            lookup_label=row.get("ALIAS"),
            entity_id=row.get("ID_SOLUTION"),
            canonical_label=row.get("NAME"),
            entity_type="solution",
        )

    return index


# ============================================================
# LOAD TOPICS
# ============================================================

def load_topic_index() -> CatalogIndex:

    index: CatalogIndex = {}

    rows = query_bq(
        f"""
        SELECT
            ID_TOPIC,
            LABEL
        FROM `{TABLE_TOPIC}`
        WHERE IS_ACTIVE = TRUE
        """,
        {},
    )

    for row in rows:

        add_catalog_entry(
            index=index,
            lookup_label=row.get("LABEL"),
            entity_id=row.get("ID_TOPIC"),
            canonical_label=row.get("LABEL"),
            entity_type="topic",
        )

    return index


# ============================================================
# LOAD CONCEPTS
# ============================================================

def load_concept_index() -> CatalogIndex:

    index: CatalogIndex = {}

    rows = query_bq(
        f"""
        SELECT
            ID_CONCEPT,
            LABEL
        FROM `{TABLE_CONCEPT}`
        WHERE IS_ACTIVE = TRUE
        """,
        {},
    )

    for row in rows:

        add_catalog_entry(
            index=index,
            lookup_label=row.get("LABEL"),
            entity_id=row.get("ID_CONCEPT"),
            canonical_label=row.get("LABEL"),
            entity_type="concept",
        )

    return index


# ============================================================
# LOAD ALL CATALOGS
# ============================================================

def load_entity_catalogs() -> Catalogs:

    return {
        "company": load_company_index(),
        "solution": load_solution_index(),
        "topic": load_topic_index(),
        "concept": load_concept_index(),
    }


# ============================================================
# FIND UNIQUE ENTRY
# ============================================================

def find_unique_entry(
    index: CatalogIndex,
    label: str,
) -> Optional[CatalogEntry]:

    normalized_label = normalize_entity_label(
        label
    )

    if not normalized_label:

        return None

    entries = index.get(
        normalized_label,
        [],
    )

    unique_entries = {
        (
            entry["entity_id"],
            entry["canonical_label"],
            entry["entity_type"],
        )
        for entry in entries
    }

    if len(unique_entries) != 1:

        return None

    (
        entity_id,
        canonical_label,
        entity_type,
    ) = next(
        iter(unique_entries)
    )

    return {
        "entity_id": entity_id,
        "canonical_label": canonical_label,
        "entity_type": entity_type,
    }


# ============================================================
# FIND CROSS-TYPE ENTRY
# ============================================================

def find_unique_cross_type_entry(
    catalogs: Catalogs,
    label: str,
) -> Optional[CatalogEntry]:

    matches: List[CatalogEntry] = []

    for index in catalogs.values():

        match = find_unique_entry(
            index=index,
            label=label,
        )

        if match:

            matches.append(
                match
            )

    unique_matches = {
        (
            match["entity_id"],
            match["canonical_label"],
            match["entity_type"],
        )
        for match in matches
    }

    if len(unique_matches) != 1:

        return None

    (
        entity_id,
        canonical_label,
        entity_type,
    ) = next(
        iter(unique_matches)
    )

    return {
        "entity_id": entity_id,
        "canonical_label": canonical_label,
        "entity_type": entity_type,
    }


# ============================================================
# RESOLVE ONE ENTITY
# ============================================================

def resolve_entity_reference(
    reference: ProfileEntityReference,
    catalogs: Catalogs,
) -> Tuple[
    ProfileEntityReference,
    Optional[str],
]:

    resolved_reference = (
        reference.copy(
            deep=True
        )
    )

    declared_type = (
        resolved_reference.entity_type
    )

    declared_index = catalogs.get(
        declared_type,
        {},
    )

    match = find_unique_entry(
        index=declared_index,
        label=resolved_reference.label,
    )

    warning = None

    if not match:

        cross_type_match = (
            find_unique_cross_type_entry(
                catalogs=catalogs,
                label=resolved_reference.label,
            )
        )

        if cross_type_match:

            match = cross_type_match

            warning = (
                "Type corrigé pour "
                f"'{resolved_reference.label}' : "
                f"{declared_type} → "
                f"{match['entity_type']}"
            )

    if not match:

        resolved_reference.canonical_label = None

        resolved_reference.entity_id = None

        resolved_reference.resolution_status = (
            "UNRESOLVED"
        )

        return (
            resolved_reference,
            (
                "Entité non résolue : "
                f"'{resolved_reference.label}' "
                f"({declared_type})"
            ),
        )

    resolved_reference.entity_type = (
        match["entity_type"]
    )

    resolved_reference.canonical_label = (
        match["canonical_label"]
    )

    resolved_reference.entity_id = (
        match["entity_id"]
    )

    resolved_reference.resolution_status = (
        "RESOLVED"
    )

    return (
        resolved_reference,
        warning,
    )


# ============================================================
# RESOLVE STRUCTURED PROFILE
# ============================================================

def resolve_structured_profile_entities(
    structured_profile: StructuredUserProfile,
) -> Tuple[
    StructuredUserProfile,
    List[str],
]:

    catalogs = load_entity_catalogs()

    resolved_profile = (
        structured_profile.copy(
            deep=True
        )
    )

    warnings: List[str] = []

    for watch_instruction in (
        resolved_profile.watch_instructions
    ):

        resolved_entities = []

        for entity in (
            watch_instruction.entities
        ):

            (
                resolved_entity,
                warning,
            ) = resolve_entity_reference(
                reference=entity,
                catalogs=catalogs,
            )

            resolved_entities.append(
                resolved_entity
            )

            if warning:

                warnings.append(
                    warning
                )

        watch_instruction.entities = (
            resolved_entities
        )

    for decision_lens in (
        resolved_profile.decision_lenses
    ):

        resolved_entities = []

        for entity in (
            decision_lens.related_entities
        ):

            (
                resolved_entity,
                warning,
            ) = resolve_entity_reference(
                reference=entity,
                catalogs=catalogs,
            )

            resolved_entities.append(
                resolved_entity
            )

            if warning:

                warnings.append(
                    warning
                )

        decision_lens.related_entities = (
            resolved_entities
        )

    warnings = list(
        dict.fromkeys(
            warnings
        )
    )

    return (
        resolved_profile,
        warnings,
    )
