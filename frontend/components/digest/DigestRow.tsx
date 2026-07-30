"use client";

import { api } from "@/lib/api";

import { useDrawer } from "@/contexts/DrawerContext";

import type {
  Digest,
} from "@/types/digest";

type Props = {
  digest: Digest;
};

export default function DigestRow({
  digest,
}: Props) {

  const {
    openRightDrawer,
  } = useDrawer();

  async function handleGenerate() {

    await api.post(
      `/digest/digests/${digest.id}/generate`,
      {},
    );

    window.location.reload();

  }

  function handlePreview() {

    openRightDrawer(
      "digest-preview",
      digest.id,
    );

  }

  async function handleSend() {

    await api.post(
      `/digest/digests/${digest.id}/send`,
      {},
    );

    window.location.reload();

  }

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

        <div className="flex justify-end gap-2">

          <button
            onClick={handleGenerate}
            className="rounded border px-3 py-1 hover:bg-gray-50"
          >
            Generate
          </button>

          <button
            onClick={handlePreview}
            className="rounded border px-3 py-1 hover:bg-gray-50"
          >
            Preview
          </button>

          <button
            onClick={handleSend}
            className="rounded border px-3 py-1 hover:bg-gray-50"
          >
            Send
          </button>

        </div>

      </td>

    </tr>

  );

}
