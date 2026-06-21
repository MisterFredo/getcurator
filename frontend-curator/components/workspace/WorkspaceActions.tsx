"use client";

/* ========================================================= */

type Props = {
  loading: boolean;

  hasContent: boolean;
  hasNumbers: boolean;

  onGenerate: (
    outputType:
      | "key_points"
      | "structure"
      | "implications"
  ) => void;
};

/* ========================================================= */

export default function WorkspaceActions({
  loading,
  hasContent,
  hasNumbers,
  onGenerate,
}: Props) {

  const disabled =
    loading ||
    (!hasContent && !hasNumbers);

  return (

    <div
      className="
        p-3
        border-b
        space-y-2
      "
    >

      {/* KEY POINTS */}
      <button
        onClick={() =>
          onGenerate("key_points")
        }
        disabled={disabled}
        className="
          w-full
          py-2
          text-xs
          rounded-lg
          bg-black
          text-white
          disabled:opacity-50
        "
      >
        Summary
      </button>

      {/* STRUCTURE */}
      <button
        onClick={() =>
          onGenerate("structure")
        }
        disabled={disabled}
        className="
          w-full
          py-2
          text-xs
          rounded-lg
          bg-gray-100
          text-gray-700
          disabled:opacity-50
        "
      >
        Structure Data
      </button>

      {/* IMPLICATIONS */}
      <button
        onClick={() =>
          onGenerate("implications")
        }
        disabled={disabled}
        className="
          w-full
          py-2
          text-xs
          rounded-lg
          bg-blue-600
          text-white
          disabled:opacity-50
        "
      >
        What matters for me
      </button>

    </div>
  );
}
