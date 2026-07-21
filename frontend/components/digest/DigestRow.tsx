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

        {digest.user_id}

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
