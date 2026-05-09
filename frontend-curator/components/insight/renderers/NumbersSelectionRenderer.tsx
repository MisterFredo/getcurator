"use client";

export default function NumbersSelectionRenderer({
  selectedItems,
  onRemove,
}: any) {

  return (
    <div className="space-y-3">

      {selectedItems.map((n: any) => (
        <div
          key={n.ID_NUMBER}
          className="relative p-3 border rounded bg-gray-50"
        >

          {/* REMOVE */}
          <button
            onClick={() => onRemove(n.ID_NUMBER)}
            className="absolute top-2 right-2 text-xs text-gray-400 hover:text-red-500"
          >
            ✕
          </button>

          <div className="text-sm font-semibold">
            {n.VALUE} {n.UNIT}
          </div>

          <div className="text-xs text-gray-700">
            {n.LABEL}
          </div>

          <div className="text-[10px] text-gray-400 mt-1">
            {n.TYPE} • {n.CATEGORY}
          </div>

          <div className="text-[10px] text-gray-400">
            {n.ENTITY_LABEL}
          </div>

        </div>
      ))}

    </div>
  );
}
