"use client";

/* ========================================================= */

type Props = {
  items: any[];
  onRemove: (id: string) => void;
};

/* ========================================================= */

export default function WorkspaceNumbersList({
  items,
  onRemove,
}: Props) {

  if (!items.length) {
    return null;
  }

  return (
    <div
      className="
        space-y-3
      "
    >

      <div
        className="
          text-[10px]
          uppercase
          tracking-wide
          text-gray-400
        "
      >
        Chiffres
      </div>

      {items.map((item) => (
        <div
          key={item.ID_NUMBER}
          className="
            relative
            p-3
            border
            rounded
            bg-gray-50
          "
        >

          <button
            onClick={() =>
              onRemove(
                item.ID_NUMBER
              )
            }
            className="
              absolute
              top-2
              right-2
              text-xs
              text-gray-400
              hover:text-red-500
            "
          >
            ✕
          </button>

          <div
            className="
              text-sm
              font-semibold
              text-gray-900
            "
          >
            {item.VALUE}{" "}
            {item.UNIT}
          </div>

          <div
            className="
              text-xs
              text-gray-700
            "
          >
            {item.LABEL}
          </div>

          <div
            className="
              text-[10px]
              text-gray-400
              mt-1
            "
          >
            {item.TYPE}
          </div>

        </div>
      ))}

    </div>
  );
}
