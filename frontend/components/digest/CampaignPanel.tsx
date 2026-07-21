"use client";

import type { DigestBatch } from "@/types/digest";

/* ========================================================= */

type Props = {

  campaign: DigestBatch | null;

  onNewCampaign: () => void;

  onGenerate: () => void;

  onSend: () => void;

};

/* ========================================================= */

export default function CampaignPanel({

  campaign,

  onNewCampaign,

  onGenerate,

  onSend,

}: Props) {

  const recipients =
    campaign?.items_count ?? 0;

  const generated =
    campaign?.generated_count ?? 0;

  const sent =
    campaign?.sent_count ?? 0;

  const status =
    campaign?.status ?? "-";

  return (

    <div className="rounded-xl border bg-white">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="flex items-center justify-between border-b px-6 py-5">

        <div>

          <h2 className="text-lg font-semibold">

            Digest Production

          </h2>

          <p className="mt-1 text-sm text-gray-500">

            Generate, review and distribute personalized knowledge digests.

          </p>

        </div>

        <button
          onClick={onNewCampaign}
          className="rounded-md bg-ratecard-blue px-4 py-2 text-sm text-white hover:opacity-90"
        >
          New Campaign
        </button>

      </div>

      {/* ================================================= */}
      {/* CAMPAIGN */}
      {/* ================================================= */}

      {campaign ? (

        <>

          <div className="grid grid-cols-2 gap-8 px-6 py-6 lg:grid-cols-5">

            <div>

              <div className="text-xs uppercase tracking-wide text-gray-500">

                Campaign

              </div>

              <div className="mt-2 font-medium">

                {campaign.frequency === "weekly"
                  ? "Weekly Digest"
                  : "Monthly Digest"}

              </div>

              <div className="mt-1 text-sm text-gray-500">

                {new Date(
                  campaign.period_start,
                ).toLocaleDateString()}
                {" → "}
                {new Date(
                  campaign.period_end,
                ).toLocaleDateString()}

              </div>

            </div>

            <div>

              <div className="text-xs uppercase tracking-wide text-gray-500">

                Audience

              </div>

              <div className="mt-2 font-medium capitalize">

                {campaign.audience}

              </div>

            </div>

            <div>

              <div className="text-xs uppercase tracking-wide text-gray-500">

                Recipients

              </div>

              <div className="mt-2 text-2xl font-semibold">

                {recipients}

              </div>

            </div>

            <div>

              <div className="text-xs uppercase tracking-wide text-gray-500">

                Generated

              </div>

              <div className="mt-2 text-2xl font-semibold">

                {generated}

              </div>

            </div>

            <div>

              <div className="text-xs uppercase tracking-wide text-gray-500">

                Sent

              </div>

              <div className="mt-2 text-2xl font-semibold">

                {sent}

              </div>

            </div>

          </div>

          {/* ============================================= */}

          <div className="flex items-center justify-between border-t px-6 py-4">

            <div>

              <div className="text-xs uppercase tracking-wide text-gray-500">

                Status

              </div>

              <div className="mt-1 font-medium capitalize">

                {status}

              </div>

            </div>

            <div className="flex gap-3">

              <button
                onClick={onGenerate}
                className="rounded-md border px-4 py-2 text-sm hover:bg-gray-50"
              >
                Generate Digests
              </button>

              <button
                onClick={onSend}
                className="rounded-md bg-green-600 px-4 py-2 text-sm text-white hover:bg-green-700"
              >
                Send Digests
              </button>

            </div>

          </div>

        </>

      ) : (

        <div className="px-6 py-10 text-center text-sm text-gray-500">

          No campaign selected.

          <div className="mt-2">

            Create a weekly or monthly campaign to start producing personalized digests.

          </div>

        </div>

      )}

    </div>

  );

}
