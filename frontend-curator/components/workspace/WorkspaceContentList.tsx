"use client";

/* ========================================================= */

type Props = {
  items: any[];
  onRemove: (id: string) => void;
};

/* ========================================================= */

export default function WorkspaceContentList({
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
        Contenus
      </div>

      {items.map((item) => (
        <div
          key={item.id}
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
              onRemove(item.id)
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
            {item.title}
          </div>

          {item.excerpt && (
            <div
              className="
                text-xs
                text-gray-700
                mt-1
                line-clamp-3
              "
            >
              {item.excerpt}
            </div>
          )}

        </div>
      ))}

    </div>
  );
}
