"use client";

import {
  ChevronDown,
  ExternalLink,
} from "lucide-react";

import type {
  PublicNumber,
  PublicNumberEntity,
} from "@/types/numbers";


/* ============================================================
   PROPS
============================================================ */

type Props = {

  item: PublicNumber;

  expanded: boolean;

  onToggle: () => void;

  onOpenContent?: (
    contentId: string,
  ) => void;

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
  item: PublicNumber,
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
      .filter(Boolean)
      .join(" ");

  }

  return [
    numericValue,
    scale,
    unit,
  ]
    .filter(Boolean)
    .join(" ");

}


/* ============================================================
   FORMAT TECHNICAL VALUE
============================================================ */

function formatTechnicalValue(
  value?: string | null,
) {

  if (
    !value
    || value === "UNKNOWN"
  ) {

    return "—";

  }

  return value
    .replaceAll(
      "_",
      " ",
    )
    .toLowerCase()
    .replace(
      /^\w/,
      character =>
        character.toUpperCase(),
    );

}


/* ============================================================
   ENTITY COLOR
============================================================ */

function getEntityClasses(
  entityType:
    PublicNumberEntity["entity_type"],
) {

  switch (entityType) {

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

  }

}


/* ============================================================
   VALUE QUALIFIER
============================================================ */

function getValueQualifier(
  valueStatus?: string | null,
) {

  if (
    valueStatus === "FORECAST"
  ) {

    return {
      label: "Forecast",
      classes:
        "bg-amber-50 text-amber-700",
    };

  }

  if (
    valueStatus === "TARGET"
  ) {

    return {
      label: "Target",
      classes:
        "bg-blue-50 text-blue-700",
    };

  }

  return null;

}


/* ============================================================
   COMPONENT
============================================================ */

export default function NumbersExplorerRow({

  item,

  expanded,

  onToggle,

  onOpenContent,

}: Props) {

  const primaryEntity =
    item.entities?.[0]
    || null;

  const additionalEntities =
    Math.max(
      0,
      (
        item.entities?.length
        || 0
      ) - 1,
    );

  const valueQualifier =
    getValueQualifier(
      item.value_status,
    );


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <div
      className="
        border-b
        border-gray-100
        last:border-b-0
      "
    >

      {/* ================================================= */}
      {/* MAIN ROW */}
      {/* ================================================= */}

      <button
        type="button"
        onClick={onToggle}
        className="
          grid
          min-w-[950px]
          w-full
          grid-cols-[180px_minmax(240px,1.8fr)_minmax(180px,1.2fr)_150px_140px_32px]
          items-center
          gap-4
          px-4
          py-3
          text-left
          transition
          hover:bg-gray-50
        "
      >

        {/* VALUE */}

        <div
          className="
            flex
            min-w-0
            items-center
            gap-2
          "
        >

          <span
            className="
              truncate
              text-sm
              font-semibold
              text-gray-950
            "
            title={formatValue(item)}
          >
            {formatValue(item)}
          </span>

          {valueQualifier && (

            <span
              className={`
                shrink-0
                rounded-full
                px-1.5
                py-0.5
                text-[8px]
                font-semibold
                uppercase
                tracking-wide
                ${valueQualifier.classes}
              `}
            >
              {valueQualifier.label}
            </span>

          )}

        </div>


        {/* INDICATOR */}

        <div className="min-w-0">

          <div
            className="
              truncate
              text-sm
              font-medium
              text-gray-800
            "
            title={item.label}
          >
            {item.label}
          </div>

          <div
            className="
              mt-0.5
              truncate
              text-[10px]
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            {formatTechnicalValue(
              item.metric_type,
            )}
          </div>

        </div>


        {/* ENTITY */}

        <div className="min-w-0">

          {primaryEntity ? (

            <div
              className="
                flex
                min-w-0
                items-center
                gap-1.5
              "
            >

              <span
                className={`
                  max-w-[160px]
                  truncate
                  rounded-full
                  px-2
                  py-1
                  text-[10px]
                  font-medium
                  ${getEntityClasses(
                    primaryEntity.entity_type,
                  )}
                `}
                title={
                  primaryEntity.entity_label
                }
              >
                {primaryEntity.entity_label}
              </span>

              {additionalEntities > 0 && (

                <span
                  className="
                    text-[10px]
                    text-gray-400
                  "
                >
                  +{additionalEntities}
                </span>

              )}

            </div>

          ) : (

            <span
              className="
                text-xs
                text-gray-300
              "
            >
              —
            </span>

          )}

        </div>


        {/* GEOGRAPHY */}

        <div
          className="
            truncate
            text-xs
            text-gray-500
          "
          title={
            formatTechnicalValue(
              item.zone,
            )
          }
        >
          {formatTechnicalValue(
            item.zone,
          )}
        </div>


        {/* PERIOD */}

        <div
          className="
            truncate
            text-xs
            text-gray-500
          "
          title={
            formatTechnicalValue(
              item.period_label,
            )
          }
        >
          {formatTechnicalValue(
            item.period_label,
          )}
        </div>


        {/* EXPAND */}

        <ChevronDown
          size={16}
          className={`
            text-gray-400
            transition-transform
            duration-200
            ${
              expanded
                ? "rotate-180"
                : ""
            }
          `}
        />

      </button>


      {/* ================================================= */}
      {/* EXPANDED DETAIL */}
      {/* ================================================= */}

      {expanded && (

        <div
          className="
            border-t
            border-gray-100
            bg-gray-50/70
            px-4
            py-4
          "
        >

          <div
            className="
              grid
              gap-6
              lg:grid-cols-[1.6fr_1fr]
            "
          >

            {/* SOURCE */}

            <div>

              <div
                className="
                  text-[10px]
                  font-semibold
                  uppercase
                  tracking-wide
                  text-gray-400
                "
              >
                Source content
              </div>

              <div
                className="
                  mt-1
                  text-sm
                  font-medium
                  text-gray-800
                "
              >
                {item.content?.title
                  || "Untitled content"}
              </div>

              {item.content?.excerpt && (

                <p
                  className="
                    mt-2
                    max-w-3xl
                    text-xs
                    leading-5
                    text-gray-500
                  "
                >
                  {item.content.excerpt}
                </p>

              )}

              {onOpenContent
                && item.id_content
                && (

                  <button
                    type="button"
                    onClick={() =>
                      onOpenContent(
                        item.id_content,
                      )
                    }
                    className="
                      mt-3
                      inline-flex
                      items-center
                      gap-1.5
                      text-xs
                      font-medium
                      text-blue-600
                      transition
                      hover:text-blue-800
                    "
                  >
                    <ExternalLink size={13} />

                    Open content
                  </button>

                )}

            </div>


            {/* DETAILS */}

            <div className="space-y-4">

              <div>

                <div
                  className="
                    text-[10px]
                    font-semibold
                    uppercase
                    tracking-wide
                    text-gray-400
                  "
                >
                  Entities
                </div>

                <div
                  className="
                    mt-2
                    flex
                    flex-wrap
                    gap-1.5
                  "
                >

                  {item.entities?.length > 0 ? (

                    item.entities.map(
                      entity => (

                        <span
                          key={
                            `${entity.entity_type}:${entity.entity_id}`
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
                    )

                  ) : (

                    <span
                      className="
                        text-xs
                        text-gray-400
                      "
                    >
                      No entity
                    </span>

                  )}

                </div>

              </div>

              <div
                className="
                  grid
                  grid-cols-2
                  gap-3
                  text-xs
                "
              >

                <div>

                  <div className="text-gray-400">
                    Metric
                  </div>

                  <div className="mt-0.5 text-gray-700">
                    {formatTechnicalValue(
                      item.metric_type,
                    )}
                  </div>

                </div>

                <div>

                  <div className="text-gray-400">
                    Confidence
                  </div>

                  <div className="mt-0.5 text-gray-700">
                    {Math.round(
                      item.confidence * 100,
                    )}%
                  </div>

                </div>

                <div>

                  <div className="text-gray-400">
                    Geography
                  </div>

                  <div className="mt-0.5 text-gray-700">
                    {formatTechnicalValue(
                      item.zone,
                    )}
                  </div>

                </div>

                <div>

                  <div className="text-gray-400">
                    Period
                  </div>

                  <div className="mt-0.5 text-gray-700">
                    {formatTechnicalValue(
                      item.period_label,
                    )}
                  </div>

                </div>

              </div>

            </div>

          </div>

        </div>

      )}

    </div>

  );

}
