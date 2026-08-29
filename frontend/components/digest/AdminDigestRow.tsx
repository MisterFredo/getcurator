"use client";

import {
  useState,
} from "react";

import {
  deleteDigest,
  generateDigest,
  sendDigest,
} from "@/lib/digest";

import {
  useDrawer,
} from "@/contexts/DrawerContext";

import type {
  DigestHistoryItem,
  DigestStatus,
} from "@/types/digest";


/* =========================================================
   TYPES
========================================================= */

type DigestAction =
  | "generate"
  | "send"
  | "delete";

type Props = {

  digest: DigestHistoryItem;

  onChanged: () => void;

};


/* =========================================================
   COMPONENT
========================================================= */

export default function AdminDigestRow({

  digest,

  onChanged,

}: Props) {

  const {
    openRightDrawer,
  } = useDrawer();

  const [
    loadingAction,
    setLoadingAction,
  ] = useState<
    DigestAction | null
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

    || digest.status === "sending"

    || digest.status === "sent"

  );

  const canSend = (
    digest.status === "generated"
  );

  const canDelete = (

    digest.status !== "generating"

    && digest.status !== "sending"

  );

  const loading =
    loadingAction !== null;


  /* =====================================================
     LABELS
  ===================================================== */

  const recipientName = (

    digest.display_name

    || digest.name

    || digest.email

    || digest.user_id

  );

  const profileLabel = (

    digest.profile_type

    || digest.audience

  );


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

      await generateDigest(
        digest.id,
      );

      onChanged();

    } catch (error) {

      console.error(
        "Unable to generate Digest",
        error,
      );

      window.alert(
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

    if (
      !canPreview
      || loading
    ) {

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

      await sendDigest(
        digest.id,
      );

      onChanged();

    } catch (error) {

      console.error(
        "Unable to send Digest",
        error,
      );

      window.alert(
        "Unable to send Digest.",
      );

    } finally {

      setLoadingAction(
        null,
      );

    }

  }


  /* =====================================================
     DELETE
  ===================================================== */

  async function handleDelete() {

    if (
      !canDelete
      || loading
    ) {

      return;

    }

    const period =
      formatPeriod(
        digest.period_start,
        digest.period_end,
      );

    const confirmed =
      window.confirm(
        (
          `Delete the Digest for `
          + `${recipientName} covering `
          + `${period}?`
        ),
      );

    if (!confirmed) {

      return;

    }

    try {

      setLoadingAction(
        "delete",
      );

      await deleteDigest(
        digest.id,
      );

      onChanged();

    } catch (error) {

      console.error(
        "Unable to delete Digest",
        error,
      );

      window.alert(
        "Unable to delete Digest.",
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

    <tr
      className="
        border-t
        align-middle
        transition
        hover:bg-gray-50
      "
    >

      {/* ================================================= */}
      {/* RECIPIENT */}
      {/* ================================================= */}

      <td className="px-4 py-3">

        <div className="flex flex-col">

          <span
            className="
              font-medium
              text-gray-900
            "
          >
            {recipientName}
          </span>

          {digest.email && (

            <span
              className="
                text-xs
                text-gray-500
              "
            >
              {digest.email}
            </span>

          )}

          {digest.company && (

            <span
              className="
                text-xs
                text-gray-400
              "
            >
              {digest.company}
            </span>

          )}

        </div>

      </td>


      {/* ================================================= */}
      {/* PROFILE */}
      {/* ================================================= */}

      <td
        className="
          px-4
          py-3
          capitalize
          text-gray-700
        "
      >
        {profileLabel}
      </td>


      {/* ================================================= */}
      {/* PERIOD */}
      {/* ================================================= */}

      <td
        className="
          whitespace-nowrap
          px-4
          py-3
          text-gray-700
        "
      >
        {formatPeriod(
          digest.period_start,
          digest.period_end,
        )}
      </td>


      {/* ================================================= */}
      {/* STATUS */}
      {/* ================================================= */}

      <td className="px-4 py-3">

        <DigestStatusBadge
          status={
            digest.status
          }
        />

        {digest.error && (

          <div
            title={
              digest.error
            }
            className="
              mt-1
              max-w-48
              truncate
              text-xs
              text-red-500
            "
          >
            {digest.error}
          </div>

        )}

      </td>


      {/* ================================================= */}
      {/* CONTENTS */}
      {/* ================================================= */}

      <td
        className="
          whitespace-nowrap
          px-4
          py-3
          text-right
          tabular-nums
          text-gray-700
        "
      >
        {digest.analyzed_contents}
        {" / "}
        {digest.total_contents}
      </td>


      {/* ================================================= */}
      {/* GENERATED */}
      {/* ================================================= */}

      <td
        className="
          whitespace-nowrap
          px-4
          py-3
          text-gray-500
        "
      >
        {formatDateTime(
          digest.generated_at,
        )}
      </td>


      {/* ================================================= */}
      {/* ACTIONS */}
      {/* ================================================= */}

      <td className="px-4 py-3">

        <div
          className="
            flex
            items-center
            justify-end
            gap-2
          "
        >

          {canGenerate && (

            <button
              type="button"
              disabled={
                loading
              }
              onClick={
                handleGenerate
              }
              className="
                rounded-md
                border
                border-blue-200
                bg-blue-50
                px-3
                py-1.5
                text-xs
                font-medium
                text-blue-700
                transition
                hover:bg-blue-100
                disabled:cursor-not-allowed
                disabled:opacity-40
              "
            >
              {loadingAction === "generate"
                ? "Generating..."
                : "Generate"}
            </button>

          )}

          {canPreview && (

            <button
              type="button"
              disabled={
                loading
              }
              onClick={
                handlePreview
              }
              className="
                rounded-md
                border
                border-gray-300
                bg-white
                px-3
                py-1.5
                text-xs
                font-medium
                text-gray-700
                transition
                hover:bg-gray-100
                disabled:cursor-not-allowed
                disabled:opacity-40
              "
            >
              Preview
            </button>

          )}

          {canSend && (

            <button
              type="button"
              disabled={
                loading
              }
              onClick={
                handleSend
              }
              className="
                rounded-md
                border
                border-green-200
                bg-green-50
                px-3
                py-1.5
                text-xs
                font-medium
                text-green-700
                transition
                hover:bg-green-100
                disabled:cursor-not-allowed
                disabled:opacity-40
              "
            >
              {loadingAction === "send"
                ? "Sending..."
                : "Send"}
            </button>

          )}

          {canDelete && (

            <button
              type="button"
              disabled={
                loading
              }
              onClick={
                handleDelete
              }
              className="
                rounded-md
                border
                border-red-200
                bg-white
                px-3
                py-1.5
                text-xs
                font-medium
                text-red-600
                transition
                hover:bg-red-50
                disabled:cursor-not-allowed
                disabled:opacity-40
              "
            >
              {loadingAction === "delete"
                ? "Deleting..."
                : "Delete"}
            </button>

          )}

        </div>

      </td>

    </tr>

  );

}


/* =========================================================
   STATUS BADGE
========================================================= */

function DigestStatusBadge({
  status,
}: {
  status: DigestStatus;
}) {

  const colors: Record<
    DigestStatus,
    string
  > = {

    created:
      "bg-gray-100 text-gray-700",

    generating:
      "bg-blue-100 text-blue-700",

    generated:
      "bg-indigo-100 text-indigo-700",

    sending:
      "bg-amber-100 text-amber-700",

    sent:
      "bg-green-100 text-green-700",

    failed:
      "bg-red-100 text-red-700",

  };

  return (

    <span
      className={`
        inline-flex
        rounded-full
        px-2.5
        py-1
        text-xs
        font-medium
        capitalize
        ${colors[status]}
      `}
    >
      {status}
    </span>

  );

}


/* =========================================================
   FORMAT PERIOD
========================================================= */

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


/* =========================================================
   FORMAT DATE
========================================================= */

function formatDateTime(
  value?: string | null,
): string {

  if (!value) {

    return "—";

  }

  const date =
    new Date(
      value,
    );

  return date.toLocaleDateString(
    "en-US",
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    },
  );

}
