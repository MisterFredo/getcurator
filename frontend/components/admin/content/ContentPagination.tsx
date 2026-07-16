"use client";

/* ========================================================= */

type Props = {
  page: number;
  totalPages: number;
  totalResults: number;
  pageSize?: number;

  onPageChange: (page: number) => void;
};

/* ========================================================= */

export default function ContentPagination({
  page,
  totalPages,
  totalResults,
  pageSize = 100,
  onPageChange,
}: Props) {

  if (totalResults === 0) {
    return null;
  }

  const first =
    (page - 1) * pageSize + 1;

  const last =
    Math.min(
      page * pageSize,
      totalResults
    );

  return (
    <div className="flex items-center justify-between border rounded-lg bg-white px-5 py-4">

      <div className="text-sm text-gray-500">
        {first}–{last} of {totalResults} contents
      </div>

      <div className="flex items-center gap-3">

        <button
          onClick={() =>
            onPageChange(page - 1)
          }
          disabled={page <= 1}
          className="px-3 py-2 border rounded disabled:opacity-40"
        >
          Previous
        </button>

        <span className="text-sm font-medium">
          Page {page} / {totalPages}
        </span>

        <button
          onClick={() =>
            onPageChange(page + 1)
          }
          disabled={page >= totalPages}
          className="px-3 py-2 border rounded disabled:opacity-40"
        >
          Next
        </button>

      </div>

    </div>
  );

}
