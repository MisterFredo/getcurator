"use client";

type Props = {
  page: number;
  totalPages: number;
  totalResults: number;

  onPageChange: (page: number) => void;
};

export default function ContentPagination({
  page,
  totalPages,
  totalResults,
  onPageChange,
}: Props) {

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className="flex items-center justify-between border rounded-lg bg-white px-5 py-4">

      <div className="text-sm text-gray-500">
        {totalResults} results
      </div>

      <div className="flex items-center gap-2">

        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-2 border rounded disabled:opacity-40"
        >
          Previous
        </button>

        <span className="text-sm font-medium">
          Page {page} / {totalPages}
        </span>

        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-2 border rounded disabled:opacity-40"
        >
          Next
        </button>

      </div>

    </div>
  );
}
