"use client";

type Props = {
  generating: boolean;
  sending: boolean;

  onGenerate: () => void;
  onSend: () => void;
};

export default function DigestCampaignActions({
  generating,
  sending,
  onGenerate,
  onSend,
}: Props) {

  return (

    <div className="bg-white border rounded-xl p-6 space-y-6">

      {/* ============================================
          REVIEW
      ============================================ */}

      <div>

        <h2 className="text-lg font-semibold text-gray-900">
          Review
        </h2>

        <p className="mt-1 text-sm text-gray-500">
          Select a user or expert to inspect the generated digest before the campaign is sent.
        </p>

      </div>

      <input
        type="text"
        placeholder="Search user or expert..."
        className="w-full rounded-lg border px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ratecard-blue"
      />

      {/* ============================================
          ACTIONS
      ============================================ */}

      <div className="border-t pt-6 flex flex-wrap gap-3">

        <button
          onClick={onGenerate}
          disabled={generating}
          className="rounded-lg bg-gray-900 text-white px-5 py-2.5 text-sm font-medium hover:bg-black disabled:opacity-50"
        >
          {generating
            ? "Generating..."
            : "Generate Campaign"}
        </button>

        <button
          onClick={onSend}
          disabled={sending}
          className="rounded-lg bg-ratecard-blue text-white px-5 py-2.5 text-sm font-medium hover:opacity-90 disabled:opacity-50"
        >
          {sending
            ? "Sending..."
            : "Send Campaign"}
        </button>

      </div>

    </div>

  );

}
