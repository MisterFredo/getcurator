"use client";

import { api } from "@/lib/api";

import { useWorkspace } from "@/contexts/WorkspaceContext";

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

  if (!panelOpen) return null;

  /* ========================================================= */

  const totalCount =
    selectedContentItems.length +
    selectedNumberItems.length;

  /* =========================================================
     INSIGHT — CONTENT
  ========================================================= */

  async function generateContentInsight() {

    if (!selectedContentItems.length) {
      return;
    }

    setLoading(true);

    try {

      const res: any =
        await api.post(
          "/insight/",
          {
            ids:
              selectedContentItems.map(
                (i) => i.id
              ),
          }
        );

      setAnalysis(
        res.insight || ""
      );

    } catch (e) {

      console.error(
        "❌ insight error",
        e
      );

    } finally {

      setLoading(false);

    }
  }

  /* =========================================================
     INSIGHT — NUMBERS
  ========================================================= */

  async function generateNumbersInsight() {

    if (!selectedNumberItems.length) {
      return;
    }

    setLoading(true);

    try {

      const res: any =
        await api.post(
          "/numbers/insight",
          {
            ids:
              selectedNumberItems.map(
                (i) =>
                  i.ID_NUMBER
              ),
          }
        );

      setAnalysis(
        res.insight || ""
      );

    } catch (e) {

      console.error(
        "❌ numbers insight error",
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

      <div className="
        h-full
        flex
        flex-col
        bg-white
        border
        rounded-xl
        overflow-hidden
        shadow-sm
      ">

        {/* HEADER */}
        <div className="
          flex
          items-center
          justify-between
          px-4
          py-3
          border-b
          bg-gray-50
        ">

          <div>

            <div className="
              text-sm
              font-semibold
              text-gray-900
            ">
              Workspace
            </div>

            <div className="
              text-xs
              text-gray-400
            ">
              {totalCount} élément(s)
            </div>

          </div>

          <button
            onClick={() =>
              setPanelOpen(false)
            }
            className="
              text-xs
              text-gray-400
              hover:text-gray-600
            "
          >
            ✕
          </button>

        </div>

        {/* ACTIONS */}
        <div className="
          p-3
          border-b
          space-y-2
        ">

          <button
            onClick={
              generateContentInsight
            }
            disabled={
              loading ||
              selectedContentItems.length ===
                0
            }
            className="
              w-full
              py-2
              text-xs
              rounded-lg
              bg-black
              text-white
              disabled:opacity-50
            "
          >
            Générer points clés
          </button>

          <button
            onClick={
              generateNumbersInsight
            }
            disabled={
              loading ||
              selectedNumberItems.length ===
                0
            }
            className="
              w-full
              py-2
              text-xs
              rounded-lg
              bg-gray-100
              text-gray-700
              disabled:opacity-50
            "
          >
            Structurer les données
          </button>

        </div>

        {/* CONTENT */}
        <div className="
          flex-1
          overflow-auto
          p-4
          space-y-6
        ">

          {/* CONTENT ITEMS */}
          {selectedContentItems.length >
            0 && (
            <div className="
              space-y-3
            ">

              <div className="
                text-[10px]
                uppercase
                tracking-wide
                text-gray-400
              ">
                Contenus
              </div>

              {selectedContentItems.map(
                (item) => (
                  <div
                    key={item.id}
                    className="
                      relative
                      p-3
                      border
                      rounded
                      bg-gray-50
                    "
                  >

                    <button
                      onClick={() =>
                        removeContent(
                          item.id
                        )
                      }
                      className="
                        absolute
                        top-2
                        right-2
                        text-xs
                        text-gray-400
                        hover:text-red-500
                      "
                    >
                      ✕
                    </button>

                    <div className="
                      text-sm
                      font-semibold
                      text-gray-900
                    ">
                      {item.title}
                    </div>

                    {item.excerpt && (
                      <div className="
                        text-xs
                        text-gray-700
                        mt-1
                        line-clamp-3
                      ">
                        {
                          item.excerpt
                        }
                      </div>
                    )}

                  </div>
                )
              )}

            </div>
          )}

          {/* NUMBER ITEMS */}
          {selectedNumberItems.length >
            0 && (
            <div className="
              space-y-3
            ">

              <div className="
                text-[10px]
                uppercase
                tracking-wide
                text-gray-400
              ">
                Chiffres
              </div>

              {selectedNumberItems.map(
                (item) => (
                  <div
                    key={
                      item.ID_NUMBER
                    }
                    className="
                      relative
                      p-3
                      border
                      rounded
                      bg-gray-50
                    "
                  >

                    <button
                      onClick={() =>
                        removeNumber(
                          item.ID_NUMBER
                        )
                      }
                      className="
                        absolute
                        top-2
                        right-2
                        text-xs
                        text-gray-400
                        hover:text-red-500
                      "
                    >
                      ✕
                    </button>

                    <div className="
                      text-sm
                      font-semibold
                      text-gray-900
                    ">
                      {item.VALUE}{" "}
                      {item.UNIT}
                    </div>

                    <div className="
                      text-xs
                      text-gray-700
                    ">
                      {item.LABEL}
                    </div>

                    <div className="
                      text-[10px]
                      text-gray-400
                      mt-1
                    ">
                      {item.TYPE}
                    </div>

                  </div>
                )
              )}

            </div>
          )}

          {/* ANALYSIS */}
          <div className="
            pt-4
            border-t
          ">

            {loading && (
              <div className="
                text-xs
                text-gray-400
              ">
                Génération en cours...
              </div>
            )}

            {!loading &&
              !analysis && (
                <div className="
                  text-xs
                  text-gray-400
                ">
                  Lance une
                  génération
                </div>
              )}

            {!loading &&
              analysis && (
                <div className="
                  text-sm
                  text-gray-800
                  whitespace-pre-wrap
                  leading-relaxed
                ">
                  {analysis}
                </div>
              )}

          </div>

        </div>

      </div>

    </div>
  );
}
