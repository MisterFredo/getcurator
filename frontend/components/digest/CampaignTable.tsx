"use client";

import type {
  DigestBatch,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  campaigns: DigestBatch[];

  loading: boolean;

  selectedCampaign: DigestBatch | null;

  onSelect: (
    campaign: DigestBatch,
  ) => void;

};

/* ========================================================= */

export default function CampaignTable({

  campaigns,

  loading,

  selectedCampaign,

  onSelect,

}: Props) {

  if (loading) {

    return (

      <div className="rounded-xl border bg-white p-10 text-center text-sm text-gray-500">

        Loading campaigns...

      </div>

    );

  }

  if (!campaigns.length) {

    return (

      <div className="rounded-xl border bg-white p-10 text-center text-sm text-gray-500">

        No campaign available.

      </div>

    );

  }

  return (

    <div className="rounded-xl border bg-white">

      <div className="border-b px-6 py-4">

        <h3 className="font-semibold">

          Campaigns

        </h3>

      </div>

      <table className="w-full">

        <thead className="border-b bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">

          <tr>

            <th className="px-6 py-3">

              Campaign

            </th>

            <th className="px-6 py-3">

              Audience

            </th>

            <th className="px-6 py-3 text-right">

              Recipients

            </th>

            <th className="px-6 py-3 text-right">

              Generated

            </th>

            <th className="px-6 py-3 text-right">

              Sent

            </th>

            <th className="px-6 py-3">

              Status

            </th>

          </tr>

        </thead>

        <tbody>

          {campaigns.map((campaign) => {

            const selected =
              selectedCampaign?.id === campaign.id;

            return (

              <tr
                key={campaign.id}
                onClick={() => onSelect(campaign)}
                className={`cursor-pointer border-b transition hover:bg-gray-50 ${
                  selected
                    ? "bg-blue-50"
                    : ""
                }`}
              >

                <td className="px-6 py-4">

                  <div className="font-medium">

                    {campaign.frequency === "weekly"
                      ? "Weekly Digest"
                      : "Monthly Digest"}

                  </div>

                  <div className="text-sm text-gray-500">

                    {new Date(
                      campaign.period_start,
                    ).toLocaleDateString()}
                    {" → "}
                    {new Date(
                      campaign.period_end,
                    ).toLocaleDateString()}

                  </div>

                </td>

                <td className="px-6 py-4 capitalize">

                  {campaign.audience}

                </td>

                <td className="px-6 py-4 text-right">

                  {campaign.items_count}

                </td>

                <td className="px-6 py-4 text-right">

                  {campaign.generated_count}

                </td>

                <td className="px-6 py-4 text-right">

                  {campaign.sent_count}

                </td>

                <td className="px-6 py-4">

                  <span className="rounded-full bg-gray-100 px-2 py-1 text-xs capitalize">

                    {campaign.status}

                  </span>

                </td>

              </tr>

            );

          })}

        </tbody>

      </table>

    </div>

  );

}
