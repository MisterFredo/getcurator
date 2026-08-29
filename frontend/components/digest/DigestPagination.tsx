"use client";


/* =========================================================
   TYPES
========================================================= */

type Props = {

  total: number;

  limit: number;

  offset: number;

  loading?: boolean;

  onChange: (
    offset: number,
  ) => void;

};


/* =========================================================
   COMPONENT
========================================================= */

export default function DigestPagination({

  total,

  limit,

  offset,

  loading = false,

  onChange,

}: Props) {

  /* =====================================================
     VALUES
  ===================================================== */

  if (total <= 0) {

    return null;

  }

  const currentPage =
    Math.floor(
      offset / limit,
    ) + 1;

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        total / limit,
      ),
    );

  const firstResult =
    offset + 1;

  const lastResult =
    Math.min(
      offset + limit,
      total,
    );

  const canGoPrevious =
    offset > 0;

  const canGoNext =
    offset + limit < total;


  /* =====================================================
     PREVIOUS
  ===================================================== */

  function goPrevious() {

    if (
      !canGoPrevious
      || loading
    ) {

      return;

    }

    onChange(
      Math.max(
        0,
        offset - limit,
      ),
    );

  }


  /* =====================================================
     NEXT
  ===================================================== */

  function goNext() {

    if (
      !canGoNext
      || loading
    ) {

      return;

    }

    onChange(
      offset + limit,
    );

  }


  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div
      className="
        flex
        flex-col
        gap-3
        rounded-lg
        border
        bg-white
        px-4
        py-3
        sm:flex-row
        sm:items-center
        sm:justify-between
      "
    >

      <div
        className="
          text-sm
          text-gray-500
        "
      >
        Showing{" "}

        <span
          className="
            font-medium
            text-gray-900
          "
        >
          {firstResult}
        </span>

        {" "}to{" "}

        <span
          className="
            font-medium
            text-gray-900
          "
        >
          {lastResult}
        </span>

        {" "}of{" "}

        <span
          className="
            font-medium
            text-gray-900
          "
        >
          {total}
        </span>

        {" "}Digests
      </div>


      <div
        className="
          flex
          items-center
          gap-3
        "
      >

        <span
          className="
            text-sm
            text-gray-500
          "
        >
          Page{" "}

          <span
            className="
              font-medium
              text-gray-900
            "
          >
            {currentPage}
          </span>

          {" "}of{" "}

          <span
            className="
              font-medium
              text-gray-900
            "
          >
            {totalPages}
          </span>
        </span>


        <div
          className="
            flex
            items-center
            gap-2
          "
        >

          <button
            type="button"
            disabled={
              !canGoPrevious
              || loading
            }
            onClick={
              goPrevious
            }
            className="
              rounded-md
              border
              border-gray-300
              bg-white
              px-3
              py-1.5
              text-sm
              font-medium
              text-gray-700
              transition
              hover:bg-gray-50
              disabled:cursor-not-allowed
              disabled:opacity-40
            "
          >
            Previous
          </button>

          <button
            type="button"
            disabled={
              !canGoNext
              || loading
            }
            onClick={
              goNext
            }
            className="
              rounded-md
              border
              border-gray-300
              bg-white
              px-3
              py-1.5
              text-sm
              font-medium
              text-gray-700
              transition
              hover:bg-gray-50
              disabled:cursor-not-allowed
              disabled:opacity-40
            "
          >
            Next
          </button>

        </div>

      </div>

    </div>

  );

}
