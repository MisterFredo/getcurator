"use client";

import type { Campaign } from "@/types/digest";

import CampaignRow from "./CampaignRow";

type Props = {
  campaigns: Campaign[];
};

export default function CampaignTable({
  campaigns,
}: Props) {
  return (
    <div className="overflow-hidden rounded-lg border bg-white">

      <table className="min-w-full text-sm">

        <thead className="bg-gray-50">

          <tr>

            <th className="px-4 py-3 text-left">
              Frequency
            </th>

            <th className="px-4 py-3 text-left">
              Audience
            </th>

            <th className="px-4 py-3 text-left">
              Period
            </th>

            <th className="px-4 py-3 text-left">
              Status
            </th>

            <th className="px-4 py-3 text-right">
              Digests
            </th>

            <th className="px-4 py-3 text-right">
              Generated
            </th>

            <th className="px-4 py-3 text-right">
              Sent
            </th>

            <th className="px-4 py-3">
            </th>

          </tr>

        </thead>

        <tbody>

          {campaigns.map(
            (campaign) => (
              <CampaignRow
                key={campaign.id}
                campaign={campaign}
              />
            ),
          )}

        </tbody>

      </table>

    </div>
  );
}
