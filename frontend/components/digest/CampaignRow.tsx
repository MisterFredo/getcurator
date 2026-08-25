"use client";

import Link from "next/link";

import type {
  Campaign,
} from "@/types/digest";

import CampaignActions from "./CampaignActions";


/* ========================================================= */

type Props = {

  campaign: Campaign;

};


/* ========================================================= */

export default function CampaignRow({
  campaign,
}: Props) {

  return (

    <tr className="border-t">

      <td className="px-4 py-3 capitalize">

        {campaign.audience}

      </td>

      <td className="px-4 py-3">

        {formatPeriod(
          campaign.period_start,
          campaign.period_end,
        )}

      </td>

      <td className="px-4 py-3 capitalize">

        {campaign.status}

      </td>

      <td className="px-4 py-3 text-right">

        {campaign.digests_count}

      </td>

      <td className="px-4 py-3 text-right">

        {campaign.generated_count}

      </td>

      <td className="px-4 py-3 text-right">

        {campaign.sent_count}

      </td>

      <td className="px-4 py-3">

        <div className="flex items-center justify-end gap-2">

          <CampaignActions
            campaign={campaign}
          />

          <Link
            href={`/admin/digest/campaigns/${campaign.id}`}
            className="rounded border px-3 py-1 hover:bg-gray-50"
          >
            Open
          </Link>

        </div>

      </td>

    </tr>

  );

}


/* ========================================================= */

function formatPeriod(
  periodStart: string,
  periodEnd: string,
): string {

  const start =
    new Date(
      periodStart,
    );

  const end =
    new Date(
      periodEnd,
    );

  const startLabel =
    start.toLocaleDateString(
      "en-US",
      {
        year: "numeric",
        month: "short",
        day: "numeric",
      },
    );

  const endLabel =
    end.toLocaleDateString(
      "en-US",
      {
        year: "numeric",
        month: "short",
        day: "numeric",
      },
    );

  return `${startLabel} → ${endLabel}`;

}
