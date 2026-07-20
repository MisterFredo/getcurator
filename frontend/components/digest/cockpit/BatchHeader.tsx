"use client";

type Props = {
  onRefresh: () => void;
};

/* ========================================================= */

export default function BatchHeader({
  onRefresh,
}: Props) {

  return (

    <div className="border rounded-lg bg-white px-6 py-4">

      <div className="flex items-center justify-between">

        {/* ================================================= */}
        {/* TITLE */}
        {/* ================================================= */}

        <div>

          <h1 className="text-2xl font-semibold">

            Digest Cockpit

          </h1>

          <p className="mt-1 text-sm text-gray-500">

            Manage weekly and monthly digest production.

          </p>

        </div>

        {/* ================================================= */}
        {/* ACTIONS */}
        {/* ================================================= */}

        <div className="flex items-center gap-3">

          <button
            onClick={onRefresh}
            className="rounded-md border px-4 py-2 text-sm hover:bg-gray-50"
          >
            Refresh
          </button>

          <button
            className="rounded-md bg-ratecard-blue px-4 py-2 text-sm text-white hover:opacity-90"
          >
            Create Batch
          </button>

        </div>

      </div>

    </div>

  );

}
