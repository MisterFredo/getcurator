// frontend/components/digest/delivery/DigestPreview.tsx

"use client";

import { useMemo, useRef, useState } from "react";

import {
  buildDigestEmail,
} from "./email/buildDigestEmail";

import {
  buildDigestEmailGmail,
} from "./email/buildDigestEmailGmail";

import type {
  DigestContentItem,
} from "@/types/digest";

import type {
  HeaderConfig,
} from "@/types/newsletter";

/* ========================================================= */

type Props = {
  headerConfig: HeaderConfig;

  editorialHtml?: string;

  summary?: string;

  implications?: string;

  contents: DigestContentItem[];
};

/* ========================================================= */

export default function DigestPreview({
  headerConfig,
  editorialHtml,
  summary,
  implications,
  contents,
}: Props)

  const [mode, setMode] = useState<
    "brevo" | "gmail"
  >("brevo");

  /* =======================================================
     HTML
  ======================================================= */

  const html = useMemo(() => {

    if (mode === "gmail") {

      return buildDigestEmailGmail({
        headerConfig,

        editorialHtml,

        contents,
      });
    }

    return buildDigestEmail({
      headerConfig,

      editorialHtml,

      contents,
    });

  }, [
    mode,

    headerConfig,

    editorialHtml,

    contents,
  ]);

  /* =======================================================
     COPY
  ======================================================= */

  const hiddenRef =
    useRef<HTMLDivElement>(
      null
    );

  function copyHtml() {

    navigator.clipboard.writeText(
      html
    );

    alert(
      mode === "gmail"
        ? "HTML Gmail copié."
        : "HTML Digest copié."
    );
  }

  function copyForGmail() {

    if (!hiddenRef.current) {
      return;
    }

    const container =
      hiddenRef.current;

    container.innerHTML =
      html;

    const range =
      document.createRange();

    range.selectNodeContents(
      container
    );

    const selection =
      window.getSelection();

    selection?.removeAllRanges();

    selection?.addRange(
      range
    );

    document.execCommand(
      "copy"
    );

    selection?.removeAllRanges();

    container.innerHTML =
      "";

    alert(
      "Version collable Gmail copiée."
    );
  }

  /* =======================================================
     UI
  ======================================================= */

  return (

    <section className="space-y-4">

      {/* HEADER */}

      <div className="flex items-center justify-between">

        <h2 className="text-sm font-semibold">
          Preview Digest
        </h2>

        <div className="flex items-center gap-3">

          {/* MODE SWITCH */}

          <div className="flex border rounded overflow-hidden text-xs">

            <button
              onClick={() =>
                setMode(
                  "brevo"
                )
              }
              className={`px-3 py-1.5 ${
                mode ===
                "brevo"
                  ? "bg-gray-900 text-white"
                  : "bg-white text-gray-600"
              }`}
            >
              Digest
            </button>

            <button
              onClick={() =>
                setMode(
                  "gmail"
                )
              }
              className={`px-3 py-1.5 border-l ${
                mode ===
                "gmail"
                  ? "bg-gray-900 text-white"
                  : "bg-white text-gray-600"
              }`}
            >
              Gmail
            </button>

          </div>

          {/* ACTIONS */}

          <button
            onClick={
              copyHtml
            }
            className="px-3 py-1.5 rounded bg-gray-900 text-white text-xs"
          >
            Copier HTML
          </button>

          {mode ===
            "gmail" && (

            <button
              onClick={
                copyForGmail
              }
              className="px-3 py-1.5 rounded bg-white border border-gray-300 text-xs"
            >
              Copier pour Gmail
            </button>

          )}

        </div>

      </div>

      {/* PREVIEW */}

      <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">

        <iframe
          title="Digest preview"
          srcDoc={html}
          className="w-full h-[760px]"
        />

      </div>

      {/* HIDDEN COPY CONTAINER */}

      <div
        ref={hiddenRef}
        style={{
          position:
            "absolute",

          left: "-9999px",

          top: 0,
        }}
      />

    </section>
  );
}
