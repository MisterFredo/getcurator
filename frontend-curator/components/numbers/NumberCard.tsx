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
        e.stopPropagation();   // 🔥 FIX CRITIQUE
        onClick();
      }}
      className={`
        p-3 rounded border cursor-pointer transition
        ${
          selected
            ? "border-teal-500 bg-teal-50"
            : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
        }
      `}
    >
      {/* BADGES */}
      <div className="flex flex-wrap gap-1 mb-2">

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

      {/* VALUE */}
      <div className="text-sm font-semibold text-gray-900">
        {formatValue(item)}
      </div>

      {/* LABEL */}
      <div className="text-xs text-gray-700 mt-1 line-clamp-2">
        {item.LABEL}
      </div>

      {/* META */}
      {(item.ZONE || item.PERIOD) && (
        <div className="text-[10px] text-gray-400 mt-1">
          {[item.ZONE, item.PERIOD].filter(Boolean).join(" — ")}
        </div>
      )}

      {/* ENTITIES */}
      <div className="mt-2 flex flex-wrap gap-1">

        {/* COMPANY */}
        {companies.map((c: any) => (
          <span
            key={c.ENTITY_ID}
            className="text-[10px] px-2 py-[2px] rounded-full bg-blue-50 text-blue-600"
          >
            {c.ENTITY_LABEL}
          </span>
        ))}

        {/* SOLUTION */}
        {solutions.map((s: any) => (
          <span
            key={s.ENTITY_ID}
            className="text-[10px] px-2 py-[2px] rounded-full bg-purple-50 text-purple-600"
          >
            {s.ENTITY_LABEL}
          </span>
        ))}

        {/* TOPIC */}
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
  );
}
