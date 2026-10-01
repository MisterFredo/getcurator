import re

from datetime import (
    date,
    timedelta,
)

from typing import (
    Dict,
    List,
    Optional,
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
    r"(?:h|d|w|mo|mos)"
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

    # LinkedIn / Sales Navigator peut produire
    # plusieurs lignes vides consécutives.

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

    # Le copier-coller Sales Navigator peut
    # concaténer la fin de l'activité précédente
    # avec le nom de l'activité suivante.
    #
    # Exemple :
    #
    # Malte Karstan shared a postMalte Karstan
    #
    # On conserve alors la dernière occurrence
    # correspondant au véritable auteur.

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

    return author


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

        # LinkedIn ne fournit plus ici
        # de date exacte.
        #
        # On conserve une approximation
        # suffisante pour le test V2.

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

    # Le copier-coller peut laisser le compteur
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

    # Les copier-coller Sales Navigator
    # aplatisent souvent le post sur une seule ligne.
    #
    # On utilise donc le début du contenu comme titre.

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

    # Évite autant que possible
    # de couper au milieu d'un mot.

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
# FIND ACTIVITY MATCHES
# ============================================================

def find_activity_matches(
    text: str,
):

    matches = list(
        ACTIVITY_PATTERN.finditer(
            text
        )
    )

    return matches


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

        relative_date = (
            match
            .group(
                "relative_date"
            )
            .strip()
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
            reactions,
            comments,
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
                "reactions": reactions,
                "comments": comments,
            }
        )

    return posts
