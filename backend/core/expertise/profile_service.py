from typing import Dict, Any

from core.user.user_keyword_service import (
    get_user_keywords,
)

from core.user.user_profile_service import (
    get_user_profile,
)

from .user_repository import (
    load_user,
    load_user_preferences,
)


# ============================================================
# LOAD PROFILE
# ============================================================

def load_profile(
    user_id: str,
) -> Dict[str, Any]:

    user = (
        load_user(user_id)
        or {}
    )

    preferences = (
        load_user_preferences(user_id)
        or {}
    )

    keywords = (
        get_user_keywords(user_id)
        or []
    )

    profile = (
        get_user_profile(user_id)
        or {}
    )

    geographies = [
        geography
        for geography in (
            profile.get("geography_1"),
            profile.get("geography_2"),
            profile.get("geography_3"),
        )
        if geography
    ]

    return {

        "id":
            user_id,

        "language":
            (
                user.get("LANGUAGE")
                or "fr"
            ).lower(),

        "preferences":
            preferences,

        "keywords":
            keywords,

        "geographies":
            geographies,

        "profile_text":
            profile.get(
                "profile_text"
            )
            or "",
    }


# ============================================================
# LOAD USER
# ============================================================

def load_user(
    user_id: str,
) -> Dict[str, Any]:

    sql = f"""

    SELECT
        ID_USER,
        EMAIL,
        NAME,
        COMPANY,
        LANGUAGE

    FROM `{TABLE_USER}`

    WHERE ID_USER = @user_id

    LIMIT 1

    """

    rows = query_bq(
        sql,

        params={
            "user_id": user_id,
        },
    )

    print("LOAD USER")
    print(rows)

    if not rows:
        return {}

    return rows[0]

# ============================================================
# LOAD USER PREFERENCES
# ============================================================

def load_user_preferences(
    user_id: str,
) -> Dict[str, List[str]]:

    sql = f"""

    SELECT
        TYPE,
        VALUE_ID

    FROM `{TABLE_USER_PREFERENCES}`

    WHERE ID_USER = @user_id

    """

    rows = query_bq(
        sql,

        params={
            "user_id": user_id,
        },
    )

    print("USER PREFS ROWS")
    print(rows)

    company_ids = []
    solution_ids = []
    topic_ids = []

    for row in rows:

        pref_type = (
            row.get("TYPE")
            or ""
        ).upper()

        value_id = row.get(
            "VALUE_ID"
        )

        print("PREF ROW")
        print(pref_type)
        print(value_id)

        if not value_id:
            continue

        # ====================================================
        # COMPANY
        # ====================================================

        if pref_type == "COMPANY":

            company_ids.append(
                value_id
            )

        # ====================================================
        # SOLUTION
        # ====================================================

        elif pref_type == "SOLUTION":

            solution_ids.append(
                value_id
            )

        # ====================================================
        # TOPIC
        # ====================================================

        elif pref_type == "TOPIC":

            topic_ids.append(
                value_id
            )

    result = {
        "companies":
            company_ids,

        "solutions":
            solution_ids,

        "topics":
            topic_ids,
    }

    print("USER PREFS RESULT")
    print(result)

    return result

# ============================================================
# USER CONTEXT
# ============================================================

def load_user_context(
    user_id: str,
) -> Dict[str, Any]:

    user = load_user(
        user_id
    )

    preferences = (
        load_user_preferences(
            user_id
        )
    )

    keywords = (
        get_user_keywords(
            user_id
        )
        or []
    )

    profile = (
        get_user_profile(
            user_id
        )
        or {}
    )

    geographies = [
        g
        for g in [
            profile.get(
                "geography_1"
            ),
            profile.get(
                "geography_2"
            ),
            profile.get(
                "geography_3"
            ),
        ]
        if g
    ]

    return {
        "user": user,

        "preferences":
            preferences,

        "keywords":
            keywords,

        "geographies":
            geographies,

        "profile_text":
            profile.get(
                "profile_text"
            ),
    }
