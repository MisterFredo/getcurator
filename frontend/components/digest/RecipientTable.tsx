"use client";

import type {
  DigestBatchItem,
} from "@/types/digest";

/* ========================================================= */

type Props = {

  recipients: DigestBatchItem[];

  selectedRecipient: DigestBatchItem | null;

  onSelect: (
    recipient: DigestBatchItem,
  ) => void;

};

/* ========================================================= */

export default function RecipientTable({

  recipients,

  selectedRecipient,

  onSelect,

}: Props) {

  return (

    <div className="rounded-xl border bg-white">

      <div className="border-b px-6 py-4">

        <h3 className="font-semibold">

          Recipients

        </h3>

        <p className="mt-1 text-sm text-gray-500">

          Review individual personalized digests before distribution.

        </p>

      </div>

      {!recipients.length ? (

        <div className="p-10 text-center text-sm text-gray-500">

          No recipients available.

        </div>

      ) : (

        <table className="w-full">

          <thead className="border-b bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">

            <tr>

              <th className="px-6 py-3">

                Recipient

              </th>

              <th className="px-6 py-3">

                Selected Articles

              </th>

              <th className="px-6 py-3">

                Status

              </th>

              <th className="px-6 py-3">

                Generated

              </th>

            </tr>

          </thead>

          <tbody>

            {recipients.map((recipient) => {

              const selected =
                selectedRecipient?.id ===
                recipient.id;

              return (

                <tr

                  key={recipient.id}

                  onClick={() =>
                    onSelect(
                      recipient,
                    )
                  }

                  className={`cursor-pointer border-b transition hover:bg-gray-50 ${
                    selected
                      ? "bg-blue-50"
                      : ""
                  }`}

                >

                  <td className="px-6 py-4">

                    <div className="font-medium">

                      {recipient.user_id}

                    </div>

                  </td>

                  <td className="px-6 py-4">

                    {recipient.selected_contents}

                  </td>

                  <td className="px-6 py-4">

                    <span className="rounded-full bg-gray-100 px-2 py-1 text-xs capitalize">

                      {recipient.status}

                    </span>

                  </td>

                  <td className="px-6 py-4">

                    {recipient.generated_at
                      ? new Date(
                          recipient.generated_at,
                        ).toLocaleString()
                      : "-"}

                  </td>

                </tr>

              );

            })}

          </tbody>

        </table>

      )}

    </div>

  );

}
