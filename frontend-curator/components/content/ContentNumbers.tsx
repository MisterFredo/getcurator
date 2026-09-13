"use client";

import type {
  ContentNumber,
  ContentNumberEntityType,
} from "@/types/watch";


/* ============================================================
   PROPS
============================================================ */

type Props = {

  numbers?: ContentNumber[];

};


/* ============================================================
   FORMAT NUMBER
============================================================ */

function formatNumber(
  value: number,
) {

  return new Intl.NumberFormat(
    "en-US",
    {
      maximumFractionDigits: 2,
    },
  ).format(
    value,
  );

}


/* ============================================================
   FORMAT SCALE
============================================================ */

function formatScale(
  scale?: string | null,
) {

  const normalizedScale = (
    scale
    || ""
  )
    .trim()
    .toUpperCase();

  const scaleMap:
    Record<string, string> = {

      NONE: "",

      THOUSAND: "K",

      MILLION: "M",

      BILLION: "Bn",

      TRILLION: "T",

  };

  return (
    scaleMap[
      normalizedScale
    ]
    ?? scale
    ?? ""
  );

}


/* ============================================================
   FORMAT UNIT
============================================================ */

function formatUnit(
  unit?: string | null,
) {

  const normalizedUnit = (
    unit
    || ""
  )
    .trim()
    .toUpperCase();

  const unitMap:
    Record<string, string> = {

      PERCENT: "%",

      PERCENTAGE_POINTS:
        "percentage points",

      EUR: "€",

      USD: "$",

      GBP: "£",

      USERS: "users",

      PEOPLE: "people",

      ACCOUNTS: "accounts",

      STORES: "stores",

      UNITS: "units",

      MINUTES: "minutes",

      HOURS: "hours",

      DAYS: "days",

      YEARS: "years",

      AREA_SQFT: "sq ft",

      POWER_KW: "kW",

      CURRENCY_UNKNOWN: "",

      OTHER: "",

  };

  return (
    unitMap[
      normalizedUnit
    ]
    ?? unit
    ?? ""
  );

}


/* ============================================================
   FORMAT VALUE
============================================================ */

function formatValue(
  item: ContentNumber,
) {

  let numericValue = "";

  if (
    item.value_min !== null
    && item.value_max !== null
  ) {

    numericValue = [
      formatNumber(
        item.value_min,
      ),

      formatNumber(
        item.value_max,
      ),
    ].join(
      " – ",
    );

  } else if (
    item.value !== null
  ) {

    numericValue = formatNumber(
      item.value,
    );

  }

  const scale = formatScale(
    item.scale,
  );

  const unit = formatUnit(
    item.unit,
  );

  if (
    unit === "€"
    || unit === "$"
    || unit === "£"
  ) {

    return [
      unit,
      numericValue,
      scale,
    ]
      .filter(
        Boolean,
      )
      .join(" ");

  }

  return [
    numericValue,
    scale,
    unit,
  ]
    .filter(
      Boolean,
    )
    .join(" ");

}


/* ============================================================
   FORMAT METADATA
============================================================ */

function formatMetadata(
  item: ContentNumber,
) {

  const values: string[] = [];

  if (
    item.zone
    && item.zone !== "UNKNOWN"
    && item.zone !== "GLOBAL"
  ) {

    values.push(
      item.zone,
    );

  }

  if (
    item.period_label
    && item.period_label !== "UNKNOWN"
  ) {

    values.push(
      item.period_label,
    );

  }

  if (
    item.value_status
    && item.value_status !== "UNKNOWN"
  ) {

    values.push(
      item.value_status.toLowerCase(),
    );

  }

  return values.join(
    " · ",
  );

}


/* ============================================================
   ENTITY COLOR
============================================================ */

function getEntityClasses(
  entityType: ContentNumberEntityType,
) {

  switch (
    entityType
  ) {

    case "company":

      return (
        "bg-blue-50 text-blue-700"
      );

    case "solution":

      return (
        "bg-purple-50 text-purple-700"
      );

    case "topic":

      return (
        "bg-emerald-50 text-emerald-700"
      );

    default:

      return (
        "bg-gray-100 text-gray-600"
      );

  }

}


/* ============================================================
   COMPONENT
============================================================ */

export default function ContentNumbers({

  numbers,

}: Props) {

  if (
    !Array.isArray(
      numbers,
    )
    || numbers.length === 0
  ) {

    return null;

  }

  return (

    <section
      className="
        border-t
        border-gray-200
        pt-8
      "
    >

      <h2
        className="
          mb-5
          text-xs
          font-semibold
          uppercase
          tracking-wide
          text-gray-500
        "
      >
        Chiffres clés
      </h2>

      <div
        className="
          grid
          grid-cols-1
          gap-3
          sm:grid-cols-2
        "
      >

        {numbers.map(
          item => {

            const metadata =
              formatMetadata(
                item,
              );

            return (

              <article
                key={
                  item.id_number
                }
                className="
                  rounded-xl
                  border
                  border-gray-200
                  bg-white
                  p-4
                "
              >

                {/* VALUE */}

                <div
                  className="
                    text-lg
                    font-semibold
                    tracking-tight
                    text-gray-950
                  "
                >
                  {formatValue(
                    item,
                  )}
                </div>


                {/* LABEL */}

                <div
                  className="
                    mt-1
                    text-sm
                    leading-5
                    text-gray-700
                  "
                >
                  {item.label}
                </div>


                {/* METADATA */}

                {metadata && (

                  <div
                    className="
                      mt-2
                      text-[11px]
                      capitalize
                      text-gray-400
                    "
                  >
                    {metadata}
                  </div>

                )}


                {/* ENTITIES */}

                {Array.isArray(
                  item.entities,
                )
                  && item.entities.length > 0
                  && (

                    <div
                      className="
                        mt-3
                        flex
                        flex-wrap
                        gap-1
                      "
                    >

                      {item.entities.map(
                        entity => (

                          <span
                            key={
                              `${entity.entity_type}:${entity.entity_id}`
                            }
                            className={`
                              rounded-full
                              px-2
                              py-0.5
                              text-[9px]
                              font-medium
                              uppercase
                              ${getEntityClasses(
                                entity.entity_type,
                              )}
                            `}
                          >
                            {entity.entity_label}
                          </span>

                        ),
                      )}

                    </div>

                  )}

              </article>

            );

          },
        )}

      </div>

    </section>

  );

}
