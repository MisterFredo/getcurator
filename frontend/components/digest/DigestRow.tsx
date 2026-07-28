"use client";

import Link from "next/link";

import type {
  Digest,
} from "@/types/digest";

type Props = {
  digest: Digest;
};

export default function DigestRow({
  digest,
}: Props) {

  return (

    <tr className="border-t">

      <td className="px-4 py-3">

        <div className="flex flex-col">

          <span className="font-medium">

            {digest.user_name ?? digest.user_id}

          </span>

          {digest.user_email && (

            <span className="text-xs text-gray-500">

              {digest.user_email}

            </span>

          )}

        </div>

      </td>

      <td className="px-4 py-3 capitalize">

        {digest.status}

      </td>

      <td className="px-4 py-3 text-right">

        {digest.total_contents}

      </td>

      <td className="px-4 py-3 text-right">

        {digest.analyzed_contents}

      </td>

      <td className="px-4 py-3">

        <div className="flex justify-end">

          <Link
            href={`/admin/digest/digests/${digest.id}`}
            className="rounded border px-3 py-1 hover:bg-gray-50"
          >
            Preview
          </Link>

        </div>

      </td>

    </tr>

  );

}
