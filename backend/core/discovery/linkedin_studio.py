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
    r"^(?P<author>.+?) "
    r"(?P<activity>"
    r"shared a post|"
    r"reshared a post"
    r")$",
    re.IGNORECASE,
)


RELATIVE_DATE_PATTERN = re.compile(
    r"^(?P<value>\d+)"
    r"(?P<unit>[hdwmo]+)"
    r"(?: ago)?$",
    re.IGNORECASE,
)


REACTIONS_PATTERN = re.compile(
    r"^(?P<count>[\d,.\s]+)"
    r"\s+reactions?$",
    re.IGNORECASE,
)


COMMENTS_PATTERN = re.compile(
    r"^(?P<count>[\d,.\s]+)"
    r"\s+comments?$",
    re.IGNORECASE,
)


# ============================================================
# NORMALIZE LINES
# ============================================================

def normalize_lines(
    text: str,
) -> List[str]:

    lines = []

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        line = re.sub(
            r"\s+",
            " ",
            line,
        )

        lines.append(
            line
        )

    return lines


# ============================================================
# PARSE NUMBER
# ============================================================

def parse_count(
    value: str,
) -> Optional[int]:

    if not value:
        return None

    normalized = (
        value
        .replace(" ", "")
        .replace(",", "")
        .replace(".", "")
    )

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
    )

    match = RELATIVE_DATE_PATTERN.match(
        normalized
    )

    if not match:
        return None

    amount = int(
        match.group("value")
    )

    unit = match.group(
        "unit"
    ).lower()

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
# FIND RELATIVE DATE
# ============================================================

def find_relative_date(
    lines: List[str],
) -> tuple[
    Optional[str],
    Optional[int],
]:

    for index, line in enumerate(
        lines
    ):

        normalized = (
            line
            .lower()
            .replace(" ago", "")
        )

        if RELATIVE_DATE_PATTERN.match(
            normalized
        ):

            return (
                line,
                index,
            )

    return (
        None,
        None,
    )


# ============================================================
# EXTRACT METRICS
# ============================================================

def extract_metrics(
    lines: List[str],
) -> tuple[
    Optional[int],
    Optional[int],
]:

    reactions = None
    comments = None

    for line in lines:

        reaction_match = (
            REACTIONS_PATTERN.match(
                line
            )
        )

        if reaction_match:

            reactions = parse_count(
                reaction_match.group(
                    "count"
                )
            )

            continue

        comment_match = (
            COMMENTS_PATTERN.match(
                line
            )
        )

        if comment_match:

            comments = parse_count(
                comment_match.group(
                    "count"
                )
            )

    return (
        reactions,
        comments,
    )


# ============================================================
# IS METADATA LINE
# ============================================================

def is_metadata_line(
    line: str,
) -> bool:

    normalized = (
        line
        .lower()
        .strip()
    )

    if REACTIONS_PATTERN.match(
        line
    ):

        return True

    if COMMENTS_PATTERN.match(
        line
    ):

        return True

    if normalized in {
        "like",
        "comment",
        "share",
        "send",
    }:

        return True

    return False


# ============================================================
# BUILD TITLE
# ============================================================

def build_title(
    raw_text: str,
    max_length: int = 180,
) -> str:

    if not raw_text:

        return "LinkedIn post"

    first_line = (
        raw_text
        .splitlines()[0]
        .strip()
    )

    if not first_line:

        return "LinkedIn post"

    if len(first_line) <= max_length:

        return first_line

    return (
        first_line[
            :max_length - 1
        ].rstrip()
        + "…"
    )


# ============================================================
# PARSE ACTIVITY BLOCK
# ============================================================

def parse_activity_block(
    lines: List[str],
    reference_date: Optional[date] = None,
) -> Optional[Dict]:

    if not lines:
        return None

    activity_match = (
        ACTIVITY_PATTERN.match(
            lines[0]
        )
    )

    if not activity_match:

        return None

    author = (
        activity_match
        .group("author")
        .strip()
    )

    activity_label = (
        activity_match
        .group("activity")
        .lower()
    )

    activity_type = (
        "RESHARED"
        if activity_label
        == "reshared a post"
        else "SHARED"
    )

    (
        relative_date,
        date_index,
    ) = find_relative_date(
        lines[1:]
    )

    if date_index is not None:

        # find_relative_date()
        # travaille sur lines[1:].

        date_index += 1

    reactions, comments = (
        extract_metrics(
            lines
        )
    )

    content_lines = []

    start_index = (
        date_index + 1
        if date_index is not None
        else 1
    )

    for line in lines[
        start_index:
    ]:

        if is_metadata_line(
            line
        ):
            continue

        content_lines.append(
            line
        )

    raw_text = "\n".join(
        content_lines
    ).strip()

    if not raw_text:

        return None

    date_source = (
        parse_relative_date(
            relative_date,
            reference_date=reference_date,
        )
        if relative_date
        else None
    )

    return {
        "author": author,
        "activity_type": activity_type,
        "relative_date": relative_date,
        "date_source": date_source,
        "title": build_title(
            raw_text
        ),
        "raw_text": raw_text,
        "reactions": reactions,
        "comments": comments,
    }


# ============================================================
# SPLIT ACTIVITY BLOCKS
# ============================================================

def split_activity_blocks(
    lines: List[str],
) -> List[List[str]]:

    blocks = []

    current_block = []

    for line in lines:

        if ACTIVITY_PATTERN.match(
            line
        ):

            if current_block:

                blocks.append(
                    current_block
                )

            current_block = [
                line
            ]

            continue

        if current_block:

            current_block.append(
                line
            )

    if current_block:

        blocks.append(
            current_block
        )

    return blocks


# ============================================================
# PARSE LINKEDIN ACTIVITY
# ============================================================

def parse_linkedin_activity(
    text: str,
    reference_date: Optional[date] = None,
) -> List[Dict]:

    if not text:
        return []

    lines = normalize_lines(
        text
    )

    blocks = split_activity_blocks(
        lines
    )

    posts = []

    for block in blocks:

        post = parse_activity_block(
            block,
            reference_date=reference_date,
        )

        if not post:
            continue

        posts.append(
            post
        )

    return posts
