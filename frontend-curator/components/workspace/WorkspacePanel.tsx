"use client";

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

  /* ========================================================= */

  if (!panelOpen) {
    return null;
  }

  /* ========================================================= */

  const totalCount =
    selectedContentItems.length +
    selectedNumberItems.length;

  /* ========================================================= */

  async function generateOutput(
    outputType:
      | "key_points"
      | "structure"
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

        {/* CONTENT */}
        <div
          className="
            flex-1
            overflow-auto
            p-4
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

          {/* ANALYSIS */}
          <WorkspaceAnalysis
            loading={loading}
            analysis={analysis}
          />

        </div>

      </div>

    </div>
  );
}
