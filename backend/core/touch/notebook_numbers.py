from core.touch.notebook_models import (
    TouchNotebookNumber,
)

from core.touch.notebook_utils import (
    safe_float,
)


# ============================================================
# BUILD CERTIFIED NUMBERS
# ============================================================

def build_certified_numbers(
    content_ids: list[str],
    numbers_by_content: dict[
        str,
        list[dict],
    ],
) -> list[
    TouchNotebookNumber
]:

    certified_numbers = []

    seen_number_ids = set()

    for content_id in content_ids:

        content_numbers = (
            numbers_by_content.get(
                content_id,
                [],
            )
            or []
        )

        for number in content_numbers:

            number_id = str(
                number.get(
                    "id_number"
                )
                or ""
            ).strip()

            number_content_id = str(
                number.get(
                    "id_content"
                )
                or content_id
            ).strip()

            if not number_id:

                raise ValueError(
                    "Une observation Number certifiée "
                    "ne possède pas de id_number"
                )

            if (
                number_content_id
                != content_id
            ):

                raise ValueError(
                    "Une observation Number certifiée "
                    "référence un mauvais contenu : "
                    f"{number_id}"
                )

            if number_id in seen_number_ids:

                raise ValueError(
                    "Une observation Number certifiée "
                    "est présente plusieurs fois : "
                    f"{number_id}"
                )

            seen_number_ids.add(
                number_id
            )

            certified_numbers.append(

                TouchNotebookNumber(

                    number_id=
                        number_id,

                    id_content=
                        number_content_id,

                    label=
                        number.get(
                            "label"
                        ),

                    metric_type=
                        number.get(
                            "metric_type"
                        ),

                    value=
                        number.get(
                            "value"
                        ),

                    value_min=
                        number.get(
                            "value_min"
                        ),

                    value_max=
                        number.get(
                            "value_max"
                        ),

                    unit=
                        number.get(
                            "unit"
                        ),

                    scale=
                        number.get(
                            "scale"
                        ),

                    zone=
                        number.get(
                            "zone"
                        ),

                    period_label=
                        number.get(
                            "period_label"
                        ),

                    value_status=
                        number.get(
                            "value_status"
                        ),

                    confidence=
                        safe_float(
                            number.get(
                                "confidence"
                            )
                        ),

                    entities=
                        number.get(
                            "entities"
                        )
                        or [],

                    source_content_ids=[
                        number_content_id,
                    ],

                )

            )

    return certified_numbers
