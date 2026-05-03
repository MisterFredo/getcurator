"use client";

type Props = {
  item: any;
  onClick: () => void;
  selected?: boolean;
};

/* ========================================================= */

function formatValue(item: any) {
  if (!item.VALUE) return "";

  const scaleMap: any = {
    millions: "M",
    billion: "Md",
    billions: "Md",
  };

  const scale = scaleMap[item.SCALE || ""] || "";
  const unit = item.UNIT || "";

  return [item.VALUE, scale, unit]
    .filter(Boolean)
    .join(" ");
}

/* ========================================================= */

export default function NumberCard({ item, onClick, selected }: Props) {

  const entities = item.ENTITIES || [];

  const companies = entities.filter((e: any) => e.ENTITY_TYPE === "company");
  const topics = entities.filter((e: any) => e.ENTITY_TYPE === "topic");
  const solutions = entities.filter((e: any) => e.ENTITY_TYPE === "solution");

  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={`
        group cursor-pointer rounded-xl
        border transition overflow-hidden relative
        ${
          selected
            ? "border-teal-500 bg-teal-50 shadow-sm"
            : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-md"
        }
      `}
    >
      {/* =====================================================
          BADGES (TOP)
      ===================================================== */}
      {(item.TYPE || item.CATEGORY) && (
        <div className="absolute top-2 left-2 flex gap-1 z-10">

          {item.TYPE && (
            <span className="
              text-[9px] px-2 py-[2px] rounded-full
              bg-gray-100 text-gray-600 uppercase
            ">
              {item.TYPE}
            </span>
          )}

          {item.CATEGORY && (
            <span className="
              text-[9px] px-2 py-[2px] rounded-full
              bg-gray-50 text-gray-400 uppercase
            ">
              {item.CATEGORY}
            </span>
          )}

        </div>
      )}

      {/* =====================================================
          VALUE BLOCK (VISUAL ANCHOR)
      ===================================================== */}
      <div className="
        h-16 flex items-center justify-center
        bg-gray-50 text-gray-900
        text-sm font-semibold
        px-2 text-center
      ">
        {formatValue(item)}
      </div>

      {/* =====================================================
          CONTENT
      ===================================================== */}
      <div className="p-3 space-y-1 text-center">

        {/* LABEL */}
        <div className="
          text-xs text-gray-700
          line-clamp-2
          group-hover:text-gray-900
        ">
          {item.LABEL}
        </div>

        {/* META */}
        {(item.ZONE || item.PERIOD) && (
          <div className="text-[10px] text-gray-400">
            {[item.ZONE, item.PERIOD].filter(Boolean).join(" — ")}
          </div>
        )}

        {/* ENTITIES */}
        <div className="mt-2 flex flex-wrap justify-center gap-1">

          {companies.map((c: any) => (
            <span
              key={c.ENTITY_ID}
              className="text-[10px] px-2 py-[2px] rounded-full bg-blue-50 text-blue-600"
            >
              {c.ENTITY_LABEL}
            </span>
          ))}

          {solutions.map((s: any) => (
            <span
              key={s.ENTITY_ID}
              className="text-[10px] px-2 py-[2px] rounded-full bg-purple-50 text-purple-600"
            >
              {s.ENTITY_LABEL}
            </span>
          ))}

          {topics.map((t: any) => (
            <span
              key={t.ENTITY_ID}
              className="text-[10px] px-2 py-[2px] rounded-full bg-gray-100 text-gray-600"
            >
              {t.ENTITY_LABEL}
            </span>
          ))}

        </div>

      </div>

      {/* =====================================================
          HOVER OVERLAY (léger)
      ===================================================== */}
      <div className="
        absolute inset-0
        bg-black/0 group-hover:bg-black/[0.02]
        transition pointer-events-none
      " />
    </div>
  );
}
