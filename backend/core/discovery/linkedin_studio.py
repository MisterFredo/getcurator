import re

import hashlib

from config import (
    BQ_PROJECT,
    BQ_DATASET,
)

from utils.bigquery_utils import (
    query_bq,
)

from datetime import (
    datetime,
    timedelta,
)

from typing import (
    Dict,
    List,
    Optional,
)

from core.acquisition.storage_service import (
    insert_raw_rows,
)


# ============================================================
# PATTERNS
# ============================================================

ACTIVITY_PATTERN = re.compile(
    r"(?P<author>.+?)"
    r"\s+"
    r"(?P<activity>"
    r"shared a post|"
    r"reshared a post"
    r")"
    r"\s+"
    r"(?P<relative_date>"
    r"\d+\s*"
    r"(?:"
    r"hours?|hrs?|"
    r"days?|"
    r"weeks?|wks?|"
    r"months?|mos?|"
    r"h|d|w|mo"
    r")"
    r"(?:\s+ago)?"
    r")",
    re.IGNORECASE,
)


REACTIONS_PATTERN = re.compile(
    r"(?P<count>[\d,.\s]+)"
    r"\s+reactions?"
    r"\b",
    re.IGNORECASE,
)


COMMENTS_PATTERN = re.compile(
    r"(?P<count>[\d,.\s]+)"
    r"\s+comments?"
    r"\b",
    re.IGNORECASE,
)


NO_COMMENTS_PATTERN = re.compile(
    r"\bno comments?\b",
    re.IGNORECASE,
)


# ============================================================
# NORMALIZE TEXT
# ============================================================

def normalize_text(
    text: str,
) -> str:

    if not text:
        return ""

    text = (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\u00a0", " ")
    )

    text = re.sub(
        r"\n[ \t]*\n+",
        "\n",
        text,
    )

    return text.strip()


# ============================================================
# CLEAN AUTHOR
# ============================================================

def clean_author(
    author: str,
) -> str:

    if not author:
        return ""

    author = re.sub(
        r"\s+",
        " ",
        author,
    ).strip()

    previous_activity = re.search(
        r"(?:shared|reshared) a post"
        r"\s*(.+)$",
        author,
        re.IGNORECASE,
    )

    if previous_activity:

        candidate = (
            previous_activity
            .group(1)
            .strip()
        )

        if candidate:

            author = candidate

    # Artefact possible du body Swagger
    # ou du copier-coller.

    author = re.sub(
        r"^string",
        "",
        author,
        flags=re.IGNORECASE,
    ).strip()

    return author


# ============================================================
# NORMALIZE RELATIVE DATE
# ============================================================

def normalize_relative_date(
    value: str,
) -> str:

    if not value:
        return ""

    normalized = (
        value
        .strip()
        .lower()
    )

    normalized = re.sub(
        r"\s+ago$",
        "",
        normalized,
    ).strip()

    match = re.match(
        r"^(?P<value>\d+)\s*"
        r"(?P<unit>"
        r"hours?|hrs?|"
        r"days?|"
        r"weeks?|wks?|"
        r"months?|mos?|"
        r"h|d|w|mo"
        r")$",
        normalized,
        re.IGNORECASE,
    )

    if not match:
        return value.strip()

    amount = match.group(
        "value"
    )

    unit = (
        match
        .group(
            "unit"
        )
        .lower()
    )

    if unit in {
        "hour",
        "hours",
        "hr",
        "hrs",
        "h",
    }:
        short_unit = "h"

    elif unit in {
        "day",
        "days",
        "d",
    }:
        short_unit = "d"

    elif unit in {
        "week",
        "weeks",
        "wk",
        "wks",
        "w",
    }:
        short_unit = "w"

    elif unit in {
        "month",
        "months",
        "mo",
        "mos",
    }:
        short_unit = "mo"

    else:
        return value.strip()

    return (
        f"{amount}"
        f"{short_unit} ago"
    )

# ============================================================
# PARSE COUNT
# ============================================================

def parse_count(
    value: str,
) -> Optional[int]:

    if not value:
        return None

    normalized = re.sub(
        r"[^\d]",
        "",
        value,
    )

    if not normalized:
        return None

    try:

        return int(
            normalized
        )

    except ValueError:

        return None


# ============================================================
# RELATIVE DATE
# ============================================================

def parse_relative_date(
    value: str,
    reference_date: Optional[date] = None,
) -> Optional[date]:

    if not value:
        return None

    reference_date = (
        reference_date
        or date.today()
    )

    normalized = (
        value
        .strip()
        .lower()
        .replace(" ago", "")
        .replace(" ", "")
    )

    match = re.match(
        r"^(?P<value>\d+)"
        r"(?P<unit>h|d|w|mo|mos)$",
        normalized,
    )

    if not match:
        return None

    amount = int(
        match.group(
            "value"
        )
    )

    unit = match.group(
        "unit"
    )

    if unit == "h":

        return reference_date

    if unit == "d":

        return (
            reference_date
            - timedelta(
                days=amount
            )
        )

    if unit == "w":

        return (
            reference_date
            - timedelta(
                weeks=amount
            )
        )

    if unit in {
        "mo",
        "mos",
    }:

        return (
            reference_date
            - timedelta(
                days=amount * 30
            )
        )

    return None


# ============================================================
# CLEAN CONTENT
# ============================================================

def clean_content(
    content: str,
) -> str:

    if not content:
        return ""

    content = content.strip()

    # ========================================================
    # THUMBNAIL IMAGE
    # ========================================================

    content = re.sub(
        r"^\s*Thumbnail image\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # ========================================================
    # BROKEN "DAY AGO" FRAGMENT
    # ========================================================

    # La représentation accessibilité de Sales Navigator
    # peut être découpée ainsi :
    #
    # relative_date = "1 d"
    # content       = "ay ago ..."
    #
    # Le "d" appartient en réalité à "day ago".
    # On retire donc le fragment résiduel.

    content = re.sub(
        r"^\s*ay\s+ago\s+",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # Même protection pour d'autres fragments éventuels.

    content = re.sub(
        r"^\s*ago\s+",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # ========================================================
    # NORMALIZE WHITESPACE
    # ========================================================

    content = re.sub(
        r"[ \t]+",
        " ",
        content,
    )

    content = re.sub(
        r"\n+",
        "\n",
        content,
    )

    return content.strip()


# ============================================================
# EXTRACT METRICS
# ============================================================

def extract_metrics(
    content: str,
) -> tuple[
    str,
    Optional[int],
    Optional[int],
]:

    if not content:

        return (
            "",
            None,
            None,
        )

    reactions = None
    comments = None

    # ========================================================
    # COMMENTS
    # ========================================================

    comment_matches = list(
        COMMENTS_PATTERN.finditer(
            content
        )
    )

    no_comment_matches = list(
        NO_COMMENTS_PATTERN.finditer(
            content
        )
    )

    last_comment_match = (
        comment_matches[-1]
        if comment_matches
        else None
    )

    last_no_comment_match = (
        no_comment_matches[-1]
        if no_comment_matches
        else None
    )

    metric_start = len(
        content
    )

    if last_comment_match:

        comments = parse_count(
            last_comment_match.group(
                "count"
            )
        )

        metric_start = min(
            metric_start,
            last_comment_match.start(),
        )

    elif last_no_comment_match:

        comments = 0

        metric_start = min(
            metric_start,
            last_no_comment_match.start(),
        )

    # ========================================================
    # REACTIONS
    # ========================================================

    reaction_matches = list(
        REACTIONS_PATTERN.finditer(
            content
        )
    )

    last_reaction_match = (
        reaction_matches[-1]
        if reaction_matches
        else None
    )

    if last_reaction_match:

        reactions = parse_count(
            last_reaction_match.group(
                "count"
            )
        )

        metric_start = min(
            metric_start,
            last_reaction_match.start(),
        )

    # ========================================================
    # REMOVE TRAILING METRICS
    # ========================================================

    if metric_start < len(
        content
    ):

        content = content[
            :metric_start
        ]

    content = content.strip()

    # LinkedIn peut laisser le compteur
    # de réactions seul sur la dernière ligne.

    content = re.sub(
        r"\n\s*\d+\s*$",
        "",
        content,
    ).strip()

    return (
        content,
        reactions,
        comments,
    )


# ============================================================
# BUILD TITLE
# ============================================================

def build_title(
    raw_text: str,
    max_length: int = 180,
) -> str:

    if not raw_text:

        return "LinkedIn post"

    normalized = re.sub(
        r"\s+",
        " ",
        raw_text,
    ).strip()

    if len(
        normalized
    ) <= max_length:

        return normalized

    cut = normalized[
        :max_length
    ]

    last_space = cut.rfind(
        " "
    )

    if last_space > 80:

        cut = cut[
            :last_space
        ]

    return (
        cut.rstrip()
        + "…"
    )


# ============================================================
# NORMALIZE CONTENT FOR DEDUP
# ============================================================

def normalize_content_for_dedup(
    raw_text: str,
) -> str:

    if not raw_text:
        return ""

    normalized = (
        raw_text
        .lower()
        .strip()
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    # On neutralise quelques différences
    # purement typographiques.

    normalized = (
        normalized
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    return normalized


# ============================================================
# POST QUALITY SCORE
# ============================================================

def post_quality_score(
    post: Dict,
) -> int:

    score = 0

    author = (
        post.get("author")
        or ""
    )

    relative_date = (
        post.get("relative_date")
        or ""
    )

    raw_text = (
        post.get("raw_text")
        or ""
    )

    # Auteur propre.

    if author:
        score += 10

    if "shared a post" not in author.lower():
        score += 10

    if not author.lower().startswith(
        "string"
    ):
        score += 5

    # Préférence explicite pour la représentation
    # standard LinkedIn : "1d ago", "2w ago", etc.

    if re.match(
        r"^\d+(?:h|d|w|mo|mos) ago$",
        relative_date,
        re.IGNORECASE,
    ):
        score += 20

    # Contenu non pollué.

    if not raw_text.lower().startswith(
        "ay ago"
    ):
        score += 10

    if not raw_text.lower().startswith(
        "thumbnail image"
    ):
        score += 10

    # Les métriques disponibles sont utiles.

    if post.get(
        "reactions"
    ) is not None:
        score += 2

    if post.get(
        "comments"
    ) is not None:
        score += 2

    return score


# ============================================================
# DEDUP POSTS
# ============================================================

def deduplicate_posts(
    posts: List[Dict],
) -> List[Dict]:

    if not posts:
        return []

    unique_posts = {}

    order = []

    for post in posts:

        raw_text = (
            post.get(
                "raw_text"
            )
            or ""
        )

        content_key = (
            normalize_content_for_dedup(
                raw_text
            )
        )

        if not content_key:
            continue

        # On combine le contenu avec le type
        # d'activité pour ne pas fusionner
        # artificiellement deux activités
        # réellement différentes.

        key = (
            post.get(
                "activity_type"
            ),
            content_key,
        )

        if key not in unique_posts:

            unique_posts[
                key
            ] = post

            order.append(
                key
            )

            continue

        current = (
            unique_posts[
                key
            ]
        )

        current_score = (
            post_quality_score(
                current
            )
        )

        candidate_score = (
            post_quality_score(
                post
            )
        )

        if candidate_score > current_score:

            unique_posts[
                key
            ] = post

    return [
        unique_posts[key]
        for key in order
    ]


# ============================================================
# FIND ACTIVITY MATCHES
# ============================================================

def find_activity_matches(
    text: str,
):

    return list(
        ACTIVITY_PATTERN.finditer(
            text
        )
    )


# ============================================================
# PARSE LINKEDIN ACTIVITY
# ============================================================

def parse_linkedin_activity(
    text: str,
    reference_date: Optional[date] = None,
) -> List[Dict]:

    if not text:
        return []

    text = normalize_text(
        text
    )

    matches = find_activity_matches(
        text
    )

    if not matches:
        return []

    posts = []

    for index, match in enumerate(
        matches
    ):

        # ====================================================
        # ACTIVITY METADATA
        # ====================================================

        author = clean_author(
            match.group(
                "author"
            )
        )

        activity_label = (
            match
            .group(
                "activity"
            )
            .lower()
        )

        activity_type = (
            "RESHARED"
            if activity_label
            == "reshared a post"
            else "SHARED"
        )

        original_relative_date = (
            match
            .group(
                "relative_date"
            )
            .strip()
        )

        relative_date = (
            normalize_relative_date(
                original_relative_date
            )
        )

        # ====================================================
        # CONTENT BOUNDARIES
        # ====================================================

        content_start = (
            match.end()
        )

        if index + 1 < len(
            matches
        ):

            content_end = (
                matches[
                    index + 1
                ].start()
            )

        else:

            content_end = len(
                text
            )

        content = text[
            content_start:
            content_end
        ]

        # ====================================================
        # CLEAN CONTENT
        # ====================================================
        
        content = clean_content(
            content
        )
        
        (
            raw_text,
            _,
            _,
        ) = extract_metrics(
            content
        )
        
        raw_text = clean_content(
            raw_text
        )
        
        if not raw_text:
            continue
        # ====================================================
        # DATE
        # ====================================================

        date_source = (
            parse_relative_date(
                relative_date,
                reference_date=reference_date,
            )
        )

        # ====================================================
        # RESULT
        # ====================================================

        posts.append(
            {
                "author": author,
                "activity_type": (
                    activity_type
                ),
                "relative_date": (
                    relative_date
                ),
                "date_source": (
                    date_source
                ),
                "title": build_title(
                    raw_text
                ),
                "raw_text": raw_text,
            }
        )

    # ========================================================
    # SALES NAVIGATOR DUPLICATES
    # ========================================================

    posts = deduplicate_posts(
        posts
    )

    return posts


# ============================================================
# NORMALIZE RAW TEXT FOR HASH
# ============================================================

def normalize_raw_text_for_hash(
    raw_text: str,
) -> str:

    if not raw_text:
        return ""

    normalized = (
        raw_text
        .strip()
        .lower()
        .replace("\u00a0", " ")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


# ============================================================
# BUILD CONTENT HASH
# ============================================================

def build_content_hash(
    raw_text: str,
) -> str:

    normalized = (
        normalize_raw_text_for_hash(
            raw_text
        )
    )

    return hashlib.sha256(
        normalized.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# GET EXISTING LINKEDIN RAW HASHES
# ============================================================

def get_existing_linkedin_raw_hashes(
    source_id: str,
) -> set[str]:

    if not source_id:
        return set()

    table = (
        f"`{BQ_PROJECT}."
        f"{BQ_DATASET}."
        "RATECARD_CONTENT_RAW`"
    )

    sql = f"""
        SELECT
            RAW_TEXT
        FROM {table}
        WHERE SOURCE_ID = @source_id
          AND IMPORT_TYPE = 'LINKEDIN'
          AND RAW_TEXT IS NOT NULL
          AND TRIM(RAW_TEXT) != ''
    """

    rows = query_bq(
        sql,
        params={
            "source_id": source_id,
        },
    )

    hashes = set()

    for row in rows:

        raw_text = (
            row.get(
                "RAW_TEXT"
            )
            or ""
        )

        if not raw_text:
            continue

        hashes.add(
            build_content_hash(
                raw_text
            )
        )

    return hashes


# ============================================================
# ANALYZE LINKEDIN ACTIVITY
# ============================================================

def analyze_linkedin_activity(
    source_id: str,
    text: str,
) -> Dict:

    # ========================================================
    # PARSE
    # ========================================================

    posts = parse_linkedin_activity(
        text
    )

    # ========================================================
    # EXISTING RAW
    # ========================================================

    existing_hashes = (
        get_existing_linkedin_raw_hashes(
            source_id
        )
    )

    # ========================================================
    # CLASSIFY
    # ========================================================

    analyzed_posts = []

    existing_count = 0
    new_count = 0

    seen_hashes = set()

    for post in posts:

        raw_text = (
            post.get(
                "raw_text"
            )
            or ""
        )

        content_hash = (
            build_content_hash(
                raw_text
            )
        )

        # Duplicate inside the current paste.
        #
        # Normally the parser has already removed
        # Sales Navigator duplicates, but this is
        # an additional safety net.

        duplicate_in_paste = (
            content_hash
            in seen_hashes
        )

        seen_hashes.add(
            content_hash
        )

        exists_in_raw = (
            content_hash
            in existing_hashes
        )

        is_existing = (
            exists_in_raw
            or duplicate_in_paste
        )

        if is_existing:

            existing_count += 1

        else:

            new_count += 1

        analyzed_posts.append(
            {
                **post,
                "content_hash": (
                    content_hash
                ),
                "is_existing": (
                    is_existing
                ),
                "exists_in_raw": (
                    exists_in_raw
                ),
                "duplicate_in_paste": (
                    duplicate_in_paste
                ),
            }
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "detected": len(
            posts
        ),
        "existing": (
            existing_count
        ),
        "new": (
            new_count
        ),
        "posts": (
            analyzed_posts
        ),
    }

# ============================================================
# STORE LINKEDIN POSTS
# ============================================================

def store_linkedin_posts(
    source_id: str,
    posts: List[Dict],
) -> Dict:

    if not source_id:
        raise ValueError(
            "source_id manquant"
        )

    if not posts:
        return {
            "requested": 0,
            "stored": 0,
            "skipped": 0,
        }

    # ========================================================
    # EXISTING RAW
    # ========================================================

    existing_hashes = (
        get_existing_linkedin_raw_hashes(
            source_id
        )
    )

    # ========================================================
    # FILTER
    # ========================================================

    rows_to_store = []

    seen_hashes = set()

    skipped = 0

    for post in posts:

        raw_text = (
            post.get(
                "raw_text"
            )
            or ""
        ).strip()

        if not raw_text:
            skipped += 1
            continue

        content_hash = (
            build_content_hash(
                raw_text
            )
        )

        # Already stored for this source.

        if (
            content_hash
            in existing_hashes
        ):
            skipped += 1
            continue

        # Duplicate inside this store request.

        if (
            content_hash
            in seen_hashes
        ):
            skipped += 1
            continue

        seen_hashes.add(
            content_hash
        )

        # ====================================================
        # DATE
        # ====================================================

        date_source = (
            post.get(
                "date_source"
            )
        )

        if date_source:

            try:

                date_source = (
                    datetime.strptime(
                        date_source,
                        "%Y-%m-%d",
                    )
                )

            except ValueError:

                date_source = None

        # ====================================================
        # RAW ROW
        # ====================================================

        rows_to_store.append(
            {
                "TITLE": (
                    post.get(
                        "title"
                    )
                    or build_title(
                        raw_text
                    )
                ),
                "DATE_SOURCE": (
                    date_source
                ),
                "RAW_TEXT": (
                    raw_text
                ),
                "SOURCE_URL": None,
            }
        )

    # ========================================================
    # NOTHING TO STORE
    # ========================================================

    if not rows_to_store:

        return {
            "requested": len(
                posts
            ),
            "stored": 0,
            "skipped": (
                skipped
            ),
        }

    # ========================================================
    # INSERT RAW
    # ========================================================

    insert_raw_rows(
        rows=rows_to_store,
        id_source=source_id,
        import_type="LINKEDIN",
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "requested": len(
            posts
        ),
        "stored": len(
            rows_to_store
        ),
        "skipped": (
            skipped
        ),
    }
