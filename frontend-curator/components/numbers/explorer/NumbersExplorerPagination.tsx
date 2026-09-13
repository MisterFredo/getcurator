"use client";

import {
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

import type {
  PublicNumbersPagination,
} from "@/types/numbers";


/* ============================================================
   PROPS
============================================================ */

type Props = {

  pagination:
    PublicNumbersPagination;

  loading?: boolean;

  onPrevious: () => void;

  onNext: () => void;

};


/* ============================================================
   COMPONENT
============================================================ */

export default function NumbersExplorerPagination({

  pagination,

  loading = false,

  onPrevious,

  onNext,

}: Props) {

  const {
    total,
    limit,
    offset,
    has_more: hasMore,
  } = pagination;

  if (total === 0) {
    return null;
  }

  const firstItem =
    offset + 1;

  const lastItem = Math.min(
    offset + limit,
    total,
  );

  const currentPage =
    Math.floor(
      offset / limit,
    ) + 1;

  const totalPages = Math.max(
    1,
    Math.ceil(
      total / limit,
    ),
  );

  const hasPrevious =
    offset > 0;


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <div
      className="
        flex
        flex-col
        gap-3
        rounded-xl
        border
        border-gray-200
        bg-white
        px-4
        py-3
        sm:flex-row
        sm:items-center
        sm:justify-between
      "
    >

      {/* ================================================= */}
      {/* RANGE */}
      {/* ================================================= */}

      <div
        className="
          text-xs
          text-gray-500
        "
      >
        Showing{" "}
        <span className="font-medium text-gray-800">
          {firstItem}
        </span>
        {" – "}
        <span className="font-medium text-gray-800">
          {lastItem}
        </span>
        {" of "}
        <span className="font-medium text-gray-800">
          {total}
        </span>
        {" Numbers"}
      </div>


      {/* ================================================= */}
      {/* CONTROLS */}
      {/* ================================================= */}

      <div
        className="
          flex
          items-center
          gap-3
        "
      >

        <span
          className="
            text-xs
            text-gray-400
          "
        >
          Page {currentPage} of {totalPages}
        </span>

        <div
          className="
            flex
            items-center
            overflow-hidden
            rounded-lg
            border
            border-gray-200
          "
        >

          <button
            type="button"
            disabled={
              loading
              || !hasPrevious
            }
            onClick={onPrevious}
            aria-label="Previous page"
            className="
              inline-flex
              items-center
              gap-1
              border-r
              border-gray-200
              bg-white
              px-3
              py-2
              text-xs
              font-medium
              text-gray-600
              transition
              hover:bg-gray-50
              disabled:cursor-not-allowed
              disabled:text-gray-300
            "
          >
            <ChevronLeft size={14} />

            Previous
          </button>

          <button
            type="button"
            disabled={
              loading
              || !hasMore
            }
            onClick={onNext}
            aria-label="Next page"
            className="
              inline-flex
              items-center
              gap-1
              bg-white
              px-3
              py-2
              text-xs
              font-medium
              text-gray-600
              transition
              hover:bg-gray-50
              disabled:cursor-not-allowed
              disabled:text-gray-300
            "
          >
            Next

            <ChevronRight size={14} />
          </button>

        </div>

      </div>

    </div>

  );

}
