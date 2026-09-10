"use client";

import type {
  PublicNumber,
} from "@/types/numbers";


/* ============================================================
   PROPS
============================================================ */

type Props = {

  item: PublicNumber;

};


/* ============================================================
   SCALE
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
   UNIT
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

      PERCENTAGE_POINTS: "percentage points",

      EUR: "€",

      USD: "$",

      GBP: "£",

      USERS: "users",

      PEOPLE: "people",

      ACCOUNTS: "accounts",

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
   NUMBER VALUE
============================================================ */

function formatNumericValue(
  value?: number | null,
) {

  if (
    value === null
    || value === undefined
  ) {

    return "";

  }

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
   VALUE
============================================================ */

function formatValue(
  item: PublicNumber,
) {

  let rawValue = "";

  if (
    item.value_min !== null
    && item.value_min !== undefined
    && item.value_max !== null
    && item.value_max !== undefined
  ) {

    rawValue = [
      formatNumericValue(
        item.value_min,
      ),

      formatNumericValue(
        item.value_max,
      ),
    ].join(
      " – ",
    );

  } else {

    rawValue = formatNumericValue(
      item.value,
    );

  }

  const scale = formatScale(
    item.scale,
  );

  const unit = formatUnit(
    item.unit,
  );

  /*
   * Currency is displayed before the value.
   */

  if (
    unit === "€"
    || unit === "$"
    || unit === "£"
  ) {

    return [
      unit,
      rawValue,
      scale,
    ]
      .filter(
        Boolean,
      )
      .join(" ");

  }

  return [
    rawValue,
    scale,
    unit,
  ]
    .filter(
      Boolean,
    )
    .join(" ");

}


/* ============================================================
   PERIOD
============================================================ */

function formatPeriod(
  period?: string | null,
) {

  if (
    !period
    || period === "UNKNOWN"
  ) {

    return null;

  }

  return period;

}


/* ============================================================
   ZONE
============================================================ */

function formatZone(
  zone?: string | null,
) {

  if (
    !zone
    || zone === "UNKNOWN"
  ) {

    return null;

  }

  return zone;

}


/* ============================================================
   VALUE STATUS
============================================================ */

function formatValueStatus(
  status?: string | null,
) {

  switch (
    status
  ) {

    case "FORECAST":

      return "Forecast";

    case "TARGET":

      return "Target";

    case "ACTUAL":

      return "Actual";

    default:

      return null;

  }

}


/* ============================================================
   ENTITY COLORS
============================================================ */

function getEntityClasses(
  entityType: string,
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

export default function ValidatedNumberCard({

  item,

}: Props) {

  const period = formatPeriod(
    item.period_label,
  );

  const zone = formatZone(
    item.zone,
  );

  const valueStatus =
    formatValueStatus(
      item.value_status,
    );

  const sourceTitle =
    item.content?.title
    || null;


  return (

    <article

      className="
        flex
        h-full
        flex-col
        overflow-hidden
        rounded-2xl
        border
        border-gray-200
        bg-white
        transition
        hover:border-gray-300
        hover:shadow-md
      "

    >

      {/* ================================================= */}
      {/* VALUE */}
      {/* ================================================= */}

      <div

        className="
          flex
          min-h-28
          items-center
          justify-center
          bg-gray-50
          px-5
          py-6
          text-center
        "

      >

        <div>

          <div

            className="
              text-2xl
              font-semibold
              tracking-tight
              text-gray-950
            "

          >

            {formatValue(
              item,
            )}

          </div>

          {valueStatus && (

            <div

              className="
                mt-2
                text-[10px]
                font-semibold
                uppercase
                tracking-wide
                text-gray-400
              "

            >

              {valueStatus}

            </div>

          )}

        </div>

      </div>


      {/* ================================================= */}
      {/* CONTENT */}
      {/* ================================================= */}

      <div

        className="
          flex
          flex-1
          flex-col
          p-4
        "

      >

        <div

          className="
            text-sm
            font-medium
            leading-5
            text-gray-800
          "

        >

          {item.label}

        </div>


        {/* ================================================= */}
        {/* METADATA */}
        {/* ================================================= */}

        {(zone || period) && (

          <div

            className="
              mt-2
              text-xs
              text-gray-400
            "

          >

            {[
              zone,
              period,
            ]
              .filter(
                Boolean,
              )
              .join(" · ")}

          </div>

        )}


        {/* ================================================= */}
        {/* ENTITIES */}
        {/* ================================================= */}

        {item.entities.length > 0 && (

          <div

            className="
              mt-4
              flex
              flex-wrap
              gap-1.5
            "

          >

            {item.entities.map(
              entity => (

                <span

                  key={
                    [
                      entity.entity_type,
                      entity.entity_id,
                    ].join(":")
                  }

                  className={`
                    rounded-full
                    px-2
                    py-1
                    text-[10px]
                    font-medium
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


        {/* ================================================= */}
        {/* SOURCE */}
        {/* ================================================= */}

        {sourceTitle && (

          <div

            className="
              mt-auto
              border-t
              border-gray-100
              pt-4
            "

          >

            <div

              className="
                text-[10px]
                font-semibold
                uppercase
                tracking-wide
                text-gray-300
              "

            >

              Source

            </div>

            <div

              className="
                mt-1
                line-clamp-2
                text-xs
                leading-4
                text-gray-500
              "

            >

              {sourceTitle}

            </div>

          </div>

        )}

      </div>

    </article>

  );

}
