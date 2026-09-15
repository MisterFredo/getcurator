"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  buildTouchNotebook,
} from "@/lib/touch";

import type {
  TouchCorpusNotebook,
} from "@/types/touch";

import TouchNotebookPreview from "@/components/admin/touch/TouchNotebookPreview";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  subject: string;
  objective: string;

  selectedContentIds: string[];

  outputLanguage?: string;
};


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchNotebookBuilder({
  subject,
  objective,
  selectedContentIds,
  outputLanguage = "fr",
}: Props) {

  const [
    notebook,
    setNotebook,
  ] = useState<
    TouchCorpusNotebook | null
  >(null);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    sourceCount,
    setSourceCount,
  ] = useState(0);

  const selectionSignature =
    selectedContentIds.join(
      "|",
    );

  /* =======================================================
     INVALIDATE NOTEBOOK WHEN CORPUS CHANGES
  ======================================================= */

  useEffect(() => {

    setNotebook(
      null,
    );

    setSourceCount(
      0,
    );

    setError(
      null,
    );

  }, [
    selectionSignature,
    subject,
    objective,
    outputLanguage,
  ]);

  /* =======================================================
     BUILD NOTEBOOK
  ======================================================= */

  async function handleBuildNotebook() {

    if (
      loading
      || selectedContentIds.length === 0
    ) {

      return;

    }

    const normalizedSubject =
      subject.trim();

    if (!normalizedSubject) {

      setError(
        "A research subject is required.",
      );

      return;

    }

    try {

      setLoading(
        true,
      );

      setError(
        null,
      );

      const outcome =
        await buildTouchNotebook({

          subject:
            normalizedSubject,

          objective:
            objective.trim(),

          content_ids:
            selectedContentIds,

          output_language:
            outputLanguage,

        });

      if (
        outcome.status
        !== "GENERATED"
        || !outcome.notebook
      ) {

        throw new Error(
          outcome.error
          || "Unable to build the editorial notebook.",
        );

      }

      setNotebook(
        outcome.notebook,
      );

      setSourceCount(
        outcome.source_count,
      );

    } catch (exception) {

      console.error(
        "Touch notebook error",
        exception,
      );

      setNotebook(
        null,
      );

      setSourceCount(
        0,
      );

      setError(

        exception instanceof Error

          ? exception.message

          : "Unable to build the editorial notebook.",

      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  /* =======================================================
     EMPTY CORPUS
  ======================================================= */

  if (
    selectedContentIds.length === 0
  ) {

    return (

      <div
        className="
          rounded-xl
          border
          border-dashed
          border-gray-300
          bg-white
          px-6
          py-10
          text-center
        "
      >

        <p className="text-sm font-medium text-gray-700">
          The editorial corpus is empty
        </p>

        <p className="mt-1 text-sm text-gray-500">
          Select contents before building the notebook.
        </p>

      </div>

    );

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <section className="space-y-6">

      {/* ================================================= */}
      {/* ACTION */}
      {/* ================================================= */}

      <div
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-5
        "
      >

        <div
          className="
            flex
            flex-wrap
            items-center
            justify-between
            gap-4
          "
        >

          <div>

            <h2 className="text-lg font-semibold text-gray-900">
              Editorial notebook
            </h2>

            <p className="mt-1 text-sm text-gray-500">

              Consolidate the evidence contained in
              {" "}
              {selectedContentIds.length}
              {" "}
              selected sources before creating the
              editorial plan.

            </p>

          </div>

          <button
            type="button"
            onClick={
              handleBuildNotebook
            }
            disabled={
              loading
              || !subject.trim()
            }
            className="
              rounded-lg
              bg-ratecard-blue
              px-4
              py-2.5
              text-sm
              font-semibold
              text-white
              transition
              hover:opacity-90
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >

            {loading
              ? "Building notebook…"
              : notebook
                ? "Rebuild notebook"
                : "Build editorial notebook"
            }

          </button>

        </div>

        {loading && (

          <div
            className="
              mt-4
              rounded-lg
              border
              border-blue-100
              bg-blue-50
              p-4
            "
          >

            <p className="text-sm font-medium text-blue-800">
              Analysing the selected corpus…
            </p>

            <p className="mt-1 text-sm text-blue-700">
              The contents are being processed in batches,
              then consolidated into one evidence notebook.
            </p>

          </div>

        )}

        {error && (

          <div
            className="
              mt-4
              rounded-lg
              border
              border-red-200
              bg-red-50
              p-4
            "
          >

            <p className="text-sm font-medium text-red-800">
              Notebook generation failed
            </p>

            <p className="mt-1 text-sm text-red-700">
              {error}
            </p>

          </div>

        )}

        {notebook && !loading && (

          <div
            className="
              mt-4
              rounded-lg
              border
              border-emerald-200
              bg-emerald-50
              p-4
            "
          >

            <p className="text-sm font-medium text-emerald-800">
              Editorial notebook ready
            </p>

            <p className="mt-1 text-sm text-emerald-700">

              {sourceCount}
              {" "}
              sources were analysed and consolidated into
              {" "}
              {notebook.notes.length}
              {" "}
              evidence notes.

            </p>

          </div>

        )}

      </div>

      {/* ================================================= */}
      {/* NOTEBOOK */}
      {/* ================================================= */}

      {notebook && (

        <TouchNotebookPreview
          notebook={notebook}
        />

      )}

    </section>

  );

}
