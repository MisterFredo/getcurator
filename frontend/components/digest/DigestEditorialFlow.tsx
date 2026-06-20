// frontend/components/digest/DigestEditorialFlow.tsx

"use client";

import {
  useMemo,
  useState,
} from "react";

import { api } from "@/lib/api";

import type {
  DigestContentItem,
  DigestEditorialItem,
} from "@/types/digest";

/* ========================================================= */

type Props = {
  selectedUserId?: string;

  editorialOrder: DigestEditorialItem[];

  contents: DigestContentItem[];

  editorialHtml: string;

  setEditorialHtml: React.Dispatch<
    React.SetStateAction<string>
  >;

  summary: string;

  setSummary: React.Dispatch<
    React.SetStateAction<string>
  >;

  implications: string;

  setImplications: React.Dispatch<
    React.SetStateAction<string>
  >;

  setEditorialOrder: React.Dispatch<
    React.SetStateAction<
      DigestEditorialItem[]
    >
  >;
};

/* ========================================================= */

export default function DigestEditorialFlow({
  selectedUserId,

  editorialOrder,

  contents,

  editorialHtml,

  setEditorialHtml,

  summary,

  setSummary,

  implications,

  setImplications,

  setEditorialOrder,
}: Props) {

  /* =======================================================
     STATE
  ======================================================= */

  const [
    generating,
    setGenerating,
  ] = useState(false);

  /* =======================================================
     INDEX MAPS
  ======================================================= */

  const contentsMap =
    useMemo(
      () =>
        Object.fromEntries(
          contents.map(
            (c) => [c.id, c]
          )
        ),
      [contents]
    );

  /* =======================================================
     RESOLVE SOURCE
  ======================================================= */

  function resolveSource(
    item: DigestEditorialItem
  ) {

    switch (
      item.type
    ) {

      case "content":
        return contentsMap[
          item.id
        ];

      default:
        return null;
    }
  }

  /* =======================================================
     LABEL
  ======================================================= */

  function getLabel(
    type:
      DigestEditorialItem["type"]
  ) {

    switch (
      type
    ) {

      case "content":
        return "content";

      default:
        return type;
    }
  }

  /* =======================================================
     TITLE
  ======================================================= */

  function getTitle(
    source: any
  ) {

    if (!source) {
      return "";
    }

    return (
      source.title ||
      ""
    );
  }

  /* =======================================================
     GENERATE ANALYSIS
  ======================================================= */

  async function generateAnalysis() {

    try {

      setGenerating(
        true
      );

      const contentIds =
        editorialOrder

          .filter(
            (i) =>
              i.type ===
              "content"
          )

          .map(
            (i) => i.id
          );

      if (
        !selectedUserId
      ) {

        alert(
          "No user selected."
        );

        return;
      }

      if (
        contentIds.length === 0
      ) {

        alert(
          "No content selected."
        );

        return;
      }

      const res =
        await api.post(
          "/digest/generate-analysis",
          {
            user_id:
              selectedUserId,

            content_ids:
              contentIds,
          }
        );

      const result =
        res?.result || {};

      setSummary(
        result.summary ||
        ""
      );

      setImplications(
        result.implications ||
        ""
      );

    } catch (e) {

      console.error(
        "Digest analysis error",
        e
      );

      alert(
        "Unable to generate analysis."
      );

    } finally {

      setGenerating(
        false
      );
    }
  }

  /* =======================================================
     ACTIONS
  ======================================================= */

  function moveUp(
    index: number
  ) {

    if (
      index === 0
    ) {
      return;
    }

    setEditorialOrder(
      (prev) => {

        const updated = [
          ...prev,
        ];

        [
          updated[
            index - 1
          ],

          updated[index],
        ] = [
          updated[index],

          updated[
            index - 1
          ],
        ];

        return updated;
      }
    );
  }

  function moveDown(
    index: number
  ) {

    if (
      index ===
      editorialOrder.length - 1
    ) {
      return;
    }

    setEditorialOrder(
      (prev) => {

        const updated = [
          ...prev,
        ];

        [
          updated[
            index + 1
          ],

          updated[index],
        ] = [
          updated[index],

          updated[
            index + 1
          ],
        ];

        return updated;
      }
    );
  }

  function removeItem(
    index: number
  ) {

    setEditorialOrder(
      (prev) =>
        prev.filter(
          (_, i) =>
            i !== index
        )
    );
  }

  /* =======================================================
     EMPTY STATE
  ======================================================= */

  if (
    editorialOrder.length === 0
  ) {

    return (

      <section className="space-y-2">

        <div className="flex items-center justify-between">

          <h2 className="text-sm font-semibold tracking-tight">
            Editorial Flow
          </h2>

        </div>

        <div className="border border-gray-200 rounded-lg bg-white px-4 py-4 text-xs text-gray-400 text-center">

          No content selected

        </div>

      </section>
    );
  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <section className="space-y-3">

      {/* HEADER */}

      <div className="flex items-center justify-between">

        <h2 className="text-sm font-semibold tracking-tight">
          Editorial Flow
        </h2>

        <button
          onClick={
            generateAnalysis
          }
          disabled={
            generating
          }
          className="
            px-3 py-1.5
            rounded-md
            border border-gray-200
            bg-white
            text-xs
            font-medium
            text-gray-700
            hover:bg-gray-50
            disabled:opacity-50
          "
        >

          {generating
            ? "Generating..."
            : "Generate Analysis"}

        </button>

      </div>

      {/* SUMMARY */}

      {summary && (

        <div className="
          border border-gray-200
          rounded-xl
          bg-white
          p-4
        ">

          <div className="
            text-[11px]
            uppercase
            tracking-[0.14em]
            text-gray-400
            font-semibold
            mb-3
          ">
            Executive Summary
          </div>

          <div className="
            text-[14px]
            leading-7
            text-gray-800
            whitespace-pre-wrap
          ">

            {summary}

          </div>

        </div>

      )}

      {/* IMPLICATIONS */}

      {implications && (

        <div className="
          border border-gray-200
          rounded-xl
          bg-white
          p-4
        ">

          <div className="
            text-[11px]
            uppercase
            tracking-[0.14em]
            text-gray-400
            font-semibold
            mb-3
          ">
            Key Implications
          </div>

          <div className="
            text-[14px]
            leading-7
            text-gray-800
            whitespace-pre-wrap
          ">

            {implications}

          </div>

        </div>

      )}

      {/* LEGACY EDITORIAL */}

      {editorialHtml && (

        <div className="
          border border-gray-200
          rounded-xl
          bg-white
          p-4
        ">

          <div className="
            text-[11px]
            uppercase
            tracking-[0.14em]
            text-gray-400
            font-semibold
            mb-3
          ">
            Editorial
          </div>

          <div className="
            text-[14px]
            leading-7
            text-gray-800
            whitespace-pre-wrap
          ">

            {editorialHtml}

          </div>

        </div>

      )}

      {/* FLOW */}

      <div className="border border-gray-200 rounded-lg bg-white divide-y">

        {editorialOrder.map(
          (
            item,
            index
          ) => {

            const source =
              resolveSource(
                item
              );

            if (!source) {
              return null;
            }

            return (

              <div
                key={`${item.type}-${item.id}`}
                className="flex items-center justify-between px-3 py-2 text-sm"
              >

                <div className="flex items-start gap-2 min-w-0">

                  <span className="text-[10px] uppercase tracking-wide text-gray-400 shrink-0">

                    {getLabel(
                      item.type
                    )}

                  </span>

                  <span className="text-gray-900 font-medium truncate">

                    {getTitle(
                      source
                    )}

                  </span>

                </div>

                <div className="flex items-center gap-1 text-xs">

                  <button
                    onClick={() =>
                      moveUp(
                        index
                      )
                    }
                    className="px-1.5 py-0.5 border border-gray-200 rounded hover:bg-gray-50"
                  >
                    ↑
                  </button>

                  <button
                    onClick={() =>
                      moveDown(
                        index
                      )
                    }
                    className="px-1.5 py-0.5 border border-gray-200 rounded hover:bg-gray-50"
                  >
                    ↓
                  </button>

                  <button
                    onClick={() =>
                      removeItem(
                        index
                      )
                    }
                    className="px-1.5 py-0.5 border border-gray-200 rounded text-red-600 hover:bg-red-50"
                  >
                    ✕
                  </button>

                </div>

              </div>
            );
          }
        )}

      </div>

    </section>
  );
}
