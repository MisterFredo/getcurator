"use client";

import {
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import type {
  Digest,
} from "@/types/digest";


/* ========================================================= */

type Props = {

  digest: Digest;

};


/* ========================================================= */

export default function AdminDigestRow({
  digest,
}: Props) {

  const {
    openRightDrawer,
  } = useDrawer();

  const [
    loadingAction,
    setLoadingAction,
  ] = useState<
    "generate" | "send" | null
  >(null);


  /* =====================================================
     ACTION AVAILABILITY
  ===================================================== */

  const canGenerate = (

    digest.status === "created"

    || digest.status === "failed"

  );

  const canPreview = (

    digest.status === "generated"

    || digest.status === "sent"

  );

  const canSend = (
    digest.status === "generated"
  );

  const loading =
    loadingAction !== null;


  /* =====================================================
     GENERATE
  ===================================================== */

  async function handleGenerate() {

    if (
      !canGenerate
      || loading
    ) {

      return;

    }

    try {

      setLoadingAction(
        "generate",
      );

      await api.post(
        `/digest/digests/${digest.id}/generate`,
        {},
      );

      window.location.reload();

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Unable to generate Digest.",
      );

    } finally {

      setLoadingAction(
        null,
      );

    }

  }


  /* =====================================================
     PREVIEW
  ===================================================== */

  function handlePreview() {

    if (!canPreview) {

      return;

    }

    openRightDrawer(
      "digest-preview",
      digest.id,
    );

  }


  /* =====================================================
     SEND
  ===================================================== */

  async function handleSend() {

    if (
      !canSend
      || loading
    ) {

      return;

    }

    try {

      setLoadingAction(
        "send",
      );

      await api.post(
        `/digest/digests/${digest.id}/send`,
        {},
      );

      window.location.reload();

    } catch (error) {

      console.error(
        error,
      );

      alert(
        "Unable to send Digest.",
      );

    } finally {

      setLoadingAction(
        null,
      );

    }

  }


  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <tr className="border-t">

      <td className="px-4 py-3">

        <div className="flex flex-col">

          <span className="font-medium">

            {digest.user_name
              ?? digest.user_id}

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
            type="button"
            disabled={
              !canGenerate
              || loading
            }
            onClick={handleGenerate}
            className="rounded border px-3 py-1 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
          >

            {loadingAction === "generate"
              ? "Generating..."
              : "Generate"}

          </button>

          <button
            type="button"
            disabled={
              !canPreview
              || loading
            }
            onClick={handlePreview}
            className="rounded border px-3 py-1 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Preview
          </button>

          <button
            type="button"
            disabled={
              !canSend
              || loading
            }
            onClick={handleSend}
            className="rounded border px-3 py-1 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
          >

            {loadingAction === "send"
              ? "Sending..."
              : "Send"}

          </button>

        </div>

      </td>

    </tr>

  );

}
