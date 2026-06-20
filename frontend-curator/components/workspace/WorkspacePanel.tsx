"use client";

import { useState } from "react";

import { api } from "@/lib/api";

import { useWorkspace } from "@/contexts/WorkspaceContext";

import WorkspaceHeader from "./WorkspaceHeader";
import WorkspaceActions from "./WorkspaceActions";
import WorkspaceContentList from "./WorkspaceContentList";
import WorkspaceNumbersList from "./WorkspaceNumbersList";
import WorkspaceAnalysis from "./WorkspaceAnalysis";

/* ========================================================= */

export default function WorkspacePanel() {

  const {
    /* CONTENT */
    selectedContentItems,
    removeContent,

    /* NUMBERS */
    selectedNumberItems,
    removeNumber,

    /* PANEL */
    panelOpen,
    setPanelOpen,

    /* ANALYSIS */
    analysis,
    setAnalysis,

    loading,
    setLoading,
  } = useWorkspace();

  /* =========================================================
     TABS
  ========================================================= */

  const [tab, setTab] =
    useState<
      "context" | "output"
    >("context");

  /* ========================================================= */

  if (!panelOpen) {
    return null;
  }

  /* ========================================================= */

  const totalCount =
    selectedContentItems.length +
    selectedNumberItems.length;

  /* =========================================================
     GENERATE OUTPUT
  ========================================================= */

  async function generateOutput(
    outputType:
      | "key_points"
      | "structure"
      | "implications"
  ) {

    if (
      !selectedContentItems.length &&
      !selectedNumberItems.length
    ) {
      return;
    }

    setLoading(true);

    try {

      const res: any =
        await api.post(
          "/workspace/generate",
          {
            output_type:
              outputType,

            content_ids:
              selectedContentItems.map(
                (i) => i.id
              ),

            number_ids:
              selectedNumberItems.map(
                (i) =>
                  i.ID_NUMBER
              ),
          }
        );

      setAnalysis(
        res.result || ""
      );

      // 🔥 AUTO SWITCH
      setTab("output");

    } catch (e) {

      console.error(
        "❌ workspace generate error",
        e
      );

    } finally {

      setLoading(false);

    }
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="h-full">

      <div
        className="
          h-full
          flex
          flex-col
          bg-white
          border
          rounded-xl
          overflow-hidden
          shadow-sm
        "
      >

        {/* HEADER */}
        <WorkspaceHeader
          totalCount={totalCount}
          onClose={() =>
            setPanelOpen(false)
          }
        />

        {/* ACTIONS */}
        <WorkspaceActions
          loading={loading}
          hasContent={
            selectedContentItems.length >
            0
          }
          hasNumbers={
            selectedNumberItems.length >
            0
          }
          onGenerate={
            generateOutput
          }
        />

        {/* TABS */}
        <div
          className="
            flex
            border-b
          "
        >

          <button
            onClick={() =>
              setTab("context")
            }
            className={`
              flex-1
              py-2
              text-xs
              font-medium
              ${
                tab === "context"
                  ? "border-b-2 border-black text-black"
                  : "text-gray-400"
              }
            `}
          >
            Context
          </button>

          <button
            onClick={() =>
              setTab("output")
            }
            className={`
              flex-1
              py-2
              text-xs
              font-medium
              ${
                tab === "output"
                  ? "border-b-2 border-black text-black"
                  : "text-gray-400"
              }
            `}
          >
            Output
          </button>

        </div>

        {/* CONTENT */}
        <div
          className="
            flex-1
            overflow-auto
            p-4
          "
        >

          {/* =================================================
             CONTEXT
          ================================================= */}

          {tab === "context" && (
            <div
              className="
                space-y-6
              "
            >

              {/* CONTENTS */}
              <WorkspaceContentList
                items={
                  selectedContentItems
                }
                onRemove={
                  removeContent
                }
              />

              {/* NUMBERS */}
              <WorkspaceNumbersList
                items={
                  selectedNumberItems
                }
                onRemove={
                  removeNumber
                }
              />

            </div>
          )}

          {/* =================================================
             OUTPUT
          ================================================= */}

          {tab === "output" && (
            <WorkspaceAnalysis
              loading={loading}
              analysis={analysis}
            />
          )}

        </div>

      </div>

    </div>
  );
}
