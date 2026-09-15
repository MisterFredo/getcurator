"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  buildTouchBrief,
} from "@/lib/touch";

import type {
  TouchBriefStructure,
  TouchCorpusNotebook,
} from "@/types/touch";

import TouchNotebookPreview from "@/components/admin/touch/TouchNotebookPreview";
import TouchBriefPreview from "@/components/admin/touch/TouchBriefPreview";


/* =========================================================
   TYPES
========================================================= */

type TouchOutputMode =
  | "DOCUMENTARY"
  | "INTERPRETATION";


type Props = {
  notebook: TouchCorpusNotebook;

  sourceContentIds: string[];

  brief:
    TouchBriefStructure | null;

  onBriefChange: (
    brief: TouchBriefStructure | null
  ) => void;
};


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchOutputChoice({
  notebook,
  sourceContentIds,
  brief,
  onBriefChange,
}: Props) {

  const [
    mode,
    setMode,
  ] = useState<TouchOutputMode>(
    "DOCUMENTARY",
  );

  const [
    editorialInstruction,
    setEditorialInstruction,
  ] = useState("");

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

  /* =======================================================
     INVALIDATE INTERPRETATION
  ======================================================= */

  useEffect(() => {

    onBriefChange(
      null,
    );

    setError(
      null,
    );

  }, [
    notebook,
    onBriefChange,
  ]);

  /* =======================================================
     GENERATE INTERPRETATION
  ======================================================= */

  async function handleGenerateInterpretation() {

    if (loading) {
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
        await buildTouchBrief({

          notebook,

          requested_brief_type:
            "AUTO",

          editorial_instruction:
            editorialInstruction.trim(),

          output_language:
            "fr",

        });

      if (
        outcome.status !== "GENERATED"
        || !outcome.brief
      ) {

        throw new Error(
          outcome.error
          || "Unable to create the interpretation.",
        );

      }

      onBriefChange(
        outcome.brief,
      );

    } catch (exception) {

      console.error(
        "Touch interpretation error",
        exception,
      );

      onBriefChange(
        null,
      );

      setError(

        exception instanceof Error

          ? exception.message

          : "Unable to create the interpretation.",

      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <section className="space-y-6">

      {/* ================================================= */}
      {/* OUTPUT MODE */}
      {/* ================================================= */}

      <div>

        <h2 className="text-xl font-semibold text-gray-900">
          Choose the output
        </h2>

        <p className="mt-1 text-sm text-gray-500">
          Use the consolidated notebook directly or ask
          GetCurator to provide an assisted interpretation.
        </p>

      </div>

      <div
        className="
          grid
          gap-4
          lg:grid-cols-2
        "
      >

        {/* ================================================= */}
        {/* DOCUMENTARY */}
        {/* ================================================= */}

        <button
          type="button"
          onClick={() =>
            setMode(
              "DOCUMENTARY",
            )
          }
          className={`
            rounded-xl
            border
            p-5
            text-left
            transition
            ${
              mode === "DOCUMENTARY"
                ? (
                    "border-ratecard-blue "
                    + "bg-blue-50 "
                    + "ring-1 "
                    + "ring-ratecard-blue"
                  )
                : (
                    "border-gray-200 "
                    + "bg-white "
                    + "hover:bg-gray-50"
                  )
            }
          `}
        >

          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >

            <div>

              <h3 className="font-semibold text-gray-900">
                Organised notes
              </h3>

              <p
                className="
                  mt-2
                  text-sm
                  leading-6
                  text-gray-600
                "
              >
                Present the consolidated facts,
                mechanisms, numbers, chronology,
                uncertainties and sources without adding
                an interpretation.
              </p>

            </div>

            <span
              className={`
                flex
                h-5
                w-5
                shrink-0
                items-center
                justify-center
                rounded-full
                border
                ${
                  mode === "DOCUMENTARY"
                    ? (
                        "border-ratecard-blue "
                        + "bg-ratecard-blue"
                      )
                    : "border-gray-300"
                }
              `}
            >

              {mode === "DOCUMENTARY" && (

                <span
                  className="
                    h-2
                    w-2
                    rounded-full
                    bg-white
                  "
                />

              )}

            </span>

          </div>

          <div
            className="
              mt-4
              flex
              flex-wrap
              gap-2
            "
          >

            <span
              className="
                rounded-full
                bg-white
                px-2.5
                py-1
                text-xs
                text-gray-600
              "
            >
              Source-based
            </span>

            <span
              className="
                rounded-full
                bg-white
                px-2.5
                py-1
                text-xs
                text-gray-600
              "
            >
              No added interpretation
            </span>

          </div>

        </button>

        {/* ================================================= */}
        {/* INTERPRETATION */}
        {/* ================================================= */}

        <button
          type="button"
          onClick={() =>
            setMode(
              "INTERPRETATION",
            )
          }
          className={`
            rounded-xl
            border
            p-5
            text-left
            transition
            ${
              mode === "INTERPRETATION"
                ? (
                    "border-violet-500 "
                    + "bg-violet-50 "
                    + "ring-1 "
                    + "ring-violet-500"
                  )
                : (
                    "border-gray-200 "
                    + "bg-white "
                    + "hover:bg-gray-50"
                  )
            }
          `}
        >

          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >

            <div>

              <h3 className="font-semibold text-gray-900">
                Assisted interpretation
              </h3>

              <p
                className="
                  mt-2
                  text-sm
                  leading-6
                  text-gray-600
                "
              >
                Ask GetCurator to select, connect and
                organise the notebook notes around a
                central reading.
              </p>

            </div>

            <span
              className={`
                flex
                h-5
                w-5
                shrink-0
                items-center
                justify-center
                rounded-full
                border
                ${
                  mode === "INTERPRETATION"
                    ? (
                        "border-violet-600 "
                        + "bg-violet-600"
                      )
                    : "border-gray-300"
                }
              `}
            >

              {mode === "INTERPRETATION" && (

                <span
                  className="
                    h-2
                    w-2
                    rounded-full
                    bg-white
                  "
                />

              )}

            </span>

          </div>

          <div
            className="
              mt-4
              flex
              flex-wrap
              gap-2
            "
          >

            <span
              className="
                rounded-full
                bg-white
                px-2.5
                py-1
                text-xs
                text-gray-600
              "
            >
              AI-assisted
            </span>

            <span
              className="
                rounded-full
                bg-white
                px-2.5
                py-1
                text-xs
                text-gray-600
              "
            >
              Optional
            </span>

          </div>

        </button>

      </div>

      {/* ================================================= */}
      {/* DOCUMENTARY OUTPUT */}
      {/* ================================================= */}

      {mode === "DOCUMENTARY" && (

        <div className="space-y-4">

          <div
            className="
              rounded-xl
              border
              border-blue-200
              bg-blue-50
              p-4
            "
          >

            <p className="text-sm font-medium text-blue-800">
              Documentary edition
            </p>

            <p className="mt-1 text-sm text-blue-700">
              The notebook is displayed without an
              additional interpretative layer.
            </p>

          </div>

          <TouchNotebookPreview
            notebook={notebook}
            sourceContentIds={
              sourceContentIds
            }
          />

        </div>

      )}

      {/* ================================================= */}
      {/* INTERPRETATION OUTPUT */}
      {/* ================================================= */}

      {mode === "INTERPRETATION" && (

        <div className="space-y-4">

          <div
            className="
              rounded-xl
              border
              border-gray-200
              bg-white
              p-5
            "
          >

            <label
              htmlFor="touch-editorial-instruction"
              className="
                text-sm
                font-medium
                text-gray-800
              "
            >
              Optional editorial direction
            </label>

            <p className="mt-1 text-sm text-gray-500">
              Indicate a point to emphasise without changing
              the underlying notebook.
            </p>

            <textarea
              id="touch-editorial-instruction"
              value={
                editorialInstruction
              }
              onChange={event =>
                setEditorialInstruction(
                  event.target.value,
                )
              }
              rows={3}
              placeholder={
                "Example: emphasise the respective roles "
                + "of Amazon and OpenAI."
              }
              className="
                mt-3
                w-full
                rounded-lg
                border
                border-gray-300
                px-3
                py-2
                text-sm
                text-gray-900
                outline-none
                focus:border-violet-500
                focus:ring-1
                focus:ring-violet-500
              "
            />

            <div
              className="
                mt-4
                flex
                justify-end
              "
            >

              <button
                type="button"
                onClick={
                  handleGenerateInterpretation
                }
                disabled={loading}
                className="
                  rounded-lg
                  bg-violet-600
                  px-4
                  py-2.5
                  text-sm
                  font-semibold
                  text-white
                  transition
                  hover:bg-violet-700
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                {loading
                  ? "Creating interpretation…"
                  : brief
                    ? "Rebuild interpretation"
                    : "Create interpretation"
                }
              </button>

            </div>

          </div>

          {error && (

            <div
              className="
                rounded-xl
                border
                border-red-200
                bg-red-50
                p-4
              "
            >

              <p className="text-sm font-medium text-red-800">
                Interpretation failed
              </p>

              <p className="mt-1 text-sm text-red-700">
                {error}
              </p>

            </div>

          )}

         {brief && (

          <TouchBriefPreview
            brief={brief}
            notebook={notebook}
            sourceContentIds={
              sourceContentIds
            }
          />
        
        )}
        </div>

      )}

    </section>

  );

}
