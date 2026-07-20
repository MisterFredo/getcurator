"use client";

/* ========================================================= */

type Props = {

  onCreate?: () => void;

  onPrepare?: () => void;

  onGenerate?: () => void;

  onSend?: () => void;

};

/* ========================================================= */

export default function BatchToolbar({

  onCreate,

  onPrepare,

  onGenerate,

  onSend,

}: Props) {

  return (

    <div className="flex items-center justify-between rounded-lg border bg-white px-6 py-4">

      {/* ================================================ */}
      {/* LEFT */}
      {/* ================================================ */}

      <div>

        <div className="text-sm font-medium">

          Batch Actions

        </div>

        <div className="text-xs text-gray-500">

          Create, generate and distribute digest batches.

        </div>

      </div>

      {/* ================================================ */}
      {/* ACTIONS */}
      {/* ================================================ */}

      <div className="flex items-center gap-3">

        <button
          onClick={onCreate}
          className="rounded-md border px-4 py-2 text-sm hover:bg-gray-50"
        >
          Create
        </button>

        <button
          onClick={onPrepare}
          className="rounded-md border px-4 py-2 text-sm hover:bg-gray-50"
        >
          Prepare
        </button>

        <button
          onClick={onGenerate}
          className="rounded-md bg-ratecard-blue px-4 py-2 text-sm text-white hover:opacity-90"
        >
          Generate
        </button>

        <button
          onClick={onSend}
          className="rounded-md bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
        >
          Send
        </button>

      </div>

    </div>

  );

}
