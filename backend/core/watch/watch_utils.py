from api.expertise.models import (
    ExpertiseContent,
)

# ============================================================
# PAGINATION
# ============================================================

def paginate(
    contents: list[ExpertiseContent],
    limit: int,
    offset: int,
) -> list[ExpertiseContent]:

    return contents[
        offset : offset + limit
    ]


# ============================================================
# BADGES
# ============================================================

def build_badges(
    content: ExpertiseContent,
) -> list[dict]:

    badges = []

    # ========================================================
    # TOPICS
    # ========================================================

    for topic in content.topics:

        badges.append({

            "type": "topic",

            "id": topic.get(
                "id_topic"
            ),

            "label": topic.get(
                "label"
            ),

        })

    # ========================================================
    # CONCEPTS
    # ========================================================

    for concept in content.concepts:

        badges.append({

            "type": "concept",

            "id": concept.get(
                "id_concept"
            ),

            "label": concept.get(
                "label"
            ),

        })

    # ========================================================
    # COMPANIES
    # ========================================================

    for company in content.companies:

        badges.append({

            "type": "company",

            "id": company.get(
                "id_company"
            ),

            "label": company.get(
                "name"
            ),

        })

    # ========================================================
    # SOLUTIONS
    # ========================================================

    for solution in content.solutions:

        badges.append({

            "type": "solution",

            "id": solution.get(
                "id_solution"
            ),

            "label": solution.get(
                "name"
            ),

        })

    # ========================================================
    # UNIVERSES
    # ========================================================

    for universe in content.universes:

        badges.append({

            "type": "universe",

            "id": universe.get(
                "id_universe"
            ),

            "label": universe.get(
                "label"
            ),

        })

    return badges


# ============================================================
# SERIALIZE CONTENT
# ============================================================

def serialize_content(
    content: ExpertiseContent,
) -> dict:

    data = content.model_dump()

    data["badges"] = build_badges(
        content,
    )

    data["primary_company_logo"] = (
        content.primary_company_logo
    )

    return data

# ============================================================
# SERIALIZE CONTENTS
# ============================================================

def serialize_contents(
    contents: list[ExpertiseContent],
) -> list[dict]:

    return [

        serialize_content(
            content
        )

        for content in contents

    ]
