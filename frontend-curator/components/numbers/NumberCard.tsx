"use client";

type Props = {
  item: any;
  onClick: () => void;
  selected?: boolean;
};

/* ========================================================= */

function formatValue(item: any) {

  if (
    item.VALUE === null ||
    item.VALUE === undefined
  ) {
    return "";
  }

  const scaleRaw =
    (item.SCALE || "")
      .toString()
      .toLowerCase();

  const scaleMap: any = {
    thousand: "K",
    thousands: "K",

    million: "M",
    millions: "M",

    billion: "Md",
    billions: "Md",

    trillion: "T",
    trillions: "T",
  };

  const scale =
    scaleMap[scaleRaw] ||
    item.SCALE ||
    "";

  const unit =
    item.UNIT || "";

  return [
    item.VALUE,
    scale,
    unit,
  ]
    .filter(Boolean)
    .join(" ");
}

/* ========================================================= */

function dedupeEntities(
  arr: any[]
) {

  const map =
    new Map();

  arr.forEach((e) => {

    const key =
      `${e.ENTITY_TYPE}_${e.ENTITY_LABEL}`;

    if (!map.has(key)) {
      map.set(key, e);
    }
  });

  return Array.from(
    map.values()
  );
}

/* ========================================================= */

export default function NumberCard({
  item,
  onClick,
  selected,
}: Props) {

  const entities =
    dedupeEntities(
      item.ENTITIES || []
    );

  const companies =
    entities.filter(
      (e: any) =>
        e.ENTITY_TYPE ===
        "company"
    );

  const topics =
    entities.filter(
      (e: any) =>
        e.ENTITY_TYPE ===
        "topic"
    );

  const solutions =
    entities.filter(
      (e: any) =>
        e.ENTITY_TYPE ===
        "solution"
    );

  /* ========================================================= */

  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={`
        group
        cursor-pointer
        rounded-xl
        border
        transition
        overflow-hidden
        relative

        ${
          selected
            ? "border-teal-500 bg-teal-50 shadow-sm"
            : `
              border-gray-200
              bg-white
              hover:border-gray-300
              hover:shadow-md
            `
        }
      `}
    >

      {/* =====================================================
          CATEGORY (OPTIONAL)
      ===================================================== */}

      {item.CATEGORY && (
        <div
          className="
            absolute
            top-2
            left-2
            z-10
          "
        >

          <span
            className="
              text-[9px]
              px-2
              py-[2px]
              rounded-full
              bg-gray-50
              text-gray-400
              uppercase
            "
          >
            {item.CATEGORY}
          </span>

        </div>
      )}

      {/* =====================================================
          VALUE BLOCK
      ===================================================== */}

      <div
        className="
          h-16
          flex
          items-center
          justify-center
          bg-gray-50
          text-gray-900
          text-sm
          font-semibold
          px-2
          text-center
        "
      >
        {formatValue(item)}
      </div>

      {/* =====================================================
          CONTENT
      ===================================================== */}

      <div
        className="
          p-3
          space-y-1
          text-center
        "
      >

        {/* LABEL */}
        <div
          className="
            text-xs
            text-gray-700
            line-clamp-2
            group-hover:text-gray-900
          "
        >
          {item.LABEL}
        </div>

        {/* META */}
        {(item.ZONE ||
          item.PERIOD) && (
          <div
            className="
              text-[10px]
              text-gray-400
            "
          >
            {[
              item.ZONE,
              item.PERIOD,
            ]
              .filter(Boolean)
              .join(" — ")}
          </div>
        )}

        {/* ENTITIES */}
        <div
          className="
            mt-2
            flex
            flex-wrap
            justify-center
            gap-1
          "
        >

          {/* COMPANIES */}
          {companies.map(
            (c: any) => (
              <span
                key={
                  c.ENTITY_ID
                }
                className="
                  text-[10px]
                  px-2
                  py-[2px]
                  rounded-full
                  bg-blue-50
                  text-blue-600
                "
              >
                {
                  c.ENTITY_LABEL
                }
              </span>
            )
          )}

          {/* SOLUTIONS */}
          {solutions.map(
            (s: any) => (
              <span
                key={
                  s.ENTITY_ID
                }
                className="
                  text-[10px]
                  px-2
                  py-[2px]
                  rounded-full
                  bg-purple-50
                  text-purple-600
                "
              >
                {
                  s.ENTITY_LABEL
                }
              </span>
            )
          )}

          {/* TOPICS */}
          {topics.map(
            (t: any) => (
              <span
                key={
                  t.ENTITY_ID
                }
                className="
                  text-[10px]
                  px-2
                  py-[2px]
                  rounded-full
                  bg-gray-100
                  text-gray-600
                "
              >
                {
                  t.ENTITY_LABEL
                }
              </span>
            )
          )}

        </div>

      </div>

      {/* =====================================================
          HOVER OVERLAY
      ===================================================== */}

      <div
        className="
          absolute
          inset-0
          bg-black/0
          group-hover:bg-black/[0.02]
          transition
          pointer-events-none
        "
      />

    </div>
  );
}
