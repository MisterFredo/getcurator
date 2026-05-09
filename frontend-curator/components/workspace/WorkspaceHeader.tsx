"use client";

/* ========================================================= */

type Props = {
  totalCount: number;
  onClose: () => void;
};

/* ========================================================= */

export default function WorkspaceHeader({
  totalCount,
  onClose,
}: Props) {

  return (
    <div
      className="
        flex
        items-center
        justify-between
        px-4
        py-3
        border-b
        bg-gray-50
      "
    >

      <div>

        <div
          className="
            text-sm
            font-semibold
            text-gray-900
          "
        >
          Workspace
        </div>

        <div
          className="
            text-xs
            text-gray-400
          "
        >
          {totalCount} élément(s)
        </div>

      </div>

      <button
        onClick={onClose}
        className="
          text-xs
          text-gray-400
          hover:text-gray-600
        "
      >
        ✕
      </button>

    </div>
  );
}
