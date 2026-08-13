"use client";

/* =========================================================
   TYPES
========================================================= */

type Props = {

  id: string;

  displayName: string;

  company?: string | null;

  description?: string | null;

  isSelected?: boolean;

  isSelf?: boolean;

  onSelect: (
    id: string,
  ) => void;

};

/* =========================================================
   COMPONENT
========================================================= */

export default function InterlocutorCard({

  id,

  displayName,

  company,

  description,

  isSelected = false,

  isSelf = false,

  onSelect,

}: Props) {

  return (

    <button

      type="button"

      onClick={() =>
        onSelect(
          id,
        )
      }

      className={`
        w-full
        text-left
        rounded-xl
        border
        transition
        overflow-hidden

        ${
          isSelected
            ? `
              border-gray-900
              bg-gray-50
              shadow-sm
            `
            : `
              border-ratecard-border
              bg-white
              hover:border-gray-300
              hover:shadow-sm
            `
        }
      `}

    >

      {/* =====================================================
          IDENTITY
      ===================================================== */}

      <div
        className="
          min-h-20
          px-4
          py-4
          flex
          items-center
          justify-between
          gap-3
        "
      >

        <div
          className="
            min-w-0
          "
        >

          <div
            className="
              text-sm
              font-semibold
              text-gray-900
              truncate
            "
          >
            {displayName}
          </div>

          {company && (

            <div
              className="
                mt-1
                text-xs
                text-gray-500
                truncate
              "
            >
              {company}
            </div>

          )}

        </div>

        {isSelf && (

          <div
            className="
              shrink-0
              rounded-full
              bg-gray-900
              px-2
              py-1
              text-[10px]
              font-medium
              text-white
            "
          >
            You
          </div>

        )}

      </div>

      {/* =====================================================
          DESCRIPTION
      ===================================================== */}

      {description && (

        <div
          className="
            border-t
            border-gray-100
            px-4
            py-3
            text-xs
            leading-5
            text-gray-500
            line-clamp-3
          "
        >
          {description}
        </div>

      )}

    </button>

  );

}
