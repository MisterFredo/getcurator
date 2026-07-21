"use client";

import type {
  Digest,
} from "@/types/digest";

import DigestRow from "./DigestRow";

type Props = {
  digests: Digest[];
};

export default function DigestList({
  digests,
}: Props) {

  return (

    <div className="overflow-hidden rounded-lg border bg-white">

      <table className="min-w-full text-sm">

        <thead className="bg-gray-50">

          <tr>

            <th className="px-4 py-3 text-left">
              User
            </th>

            <th className="px-4 py-3 text-left">
              Status
            </th>

            <th className="px-4 py-3 text-right">
              Contents
            </th>

            <th className="px-4 py-3 text-right">
              Analysed
            </th>

            <th className="px-4 py-3">
            </th>

          </tr>

        </thead>

        <tbody>

          {digests.map(
            (digest) => (
              <DigestRow
                key={digest.id}
                digest={digest}
              />
            ),
          )}

        </tbody>

      </table>

    </div>

  );

}
