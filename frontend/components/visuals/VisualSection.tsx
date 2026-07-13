// frontend/components/visuals/VisualSection.tsx

"use client";

import { useState } from "react";

import { api } from "@/lib/api";

/* ========================================================= */

export type EntityType =
  | "company"
  | "solution"
  | "topic";

/* ========================================================= */

type Props = {
  entityId: string;

  entityType: EntityType;

  squareUrl?: string | null;

  rectUrl: string | null;

  onUpdated: () => void;
};

/* ========================================================= */

export default function VisualSection({

  entityId,

  entityType,

  squareUrl = null,

  rectUrl,

  onUpdated,

}: Props) {

  const [
    loading,
    setLoading,
  ] = useState(false);

  /* =======================================================
     FILE -> BASE64
  ======================================================= */

  function fileToBase64(
    file: File,
  ): Promise<string> {

    return new Promise(
      (
        resolve,
        reject,
      ) => {

        const reader =
          new FileReader();

        reader.onerror =
          reject;

        reader.onload =
          () => {

            const result =
              reader.result?.toString() || "";

            resolve(
              result.replace(
                /^data:image\/\w+;base64,/,
                "",
              ),
            );

          };

        reader.readAsDataURL(
          file,
        );

      },
    );

  }

  /* =======================================================
     LABELS
  ======================================================= */

  const labels = {

    company:
      "company",

    solution:
      "solution",

    topic:
      "topic",

  };

  const label =
    labels[entityType];

  /* =======================================================
     UPLOAD
  ======================================================= */

  async function upload(

    file: File,

    format?:
      | "square"
      | "rectangle",

  ) {

    setLoading(true);

    try {

      const base64 =
        await fileToBase64(
          file,
        );

      const payload: any = {

        base64_image:
          base64,

      };

      payload[
        `id_${entityType}`
      ] = entityId;

      if (
        entityType ===
        "topic"
      ) {

        payload.format =
          format;

      }

      const res =
        await api.post(

          `/visuals/${entityType}/upload`,

          payload,

        );

      if (
        res.status !==
        "ok"
      ) {

        throw new Error(
          "Upload failed",
        );

      }

      onUpdated();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Error uploading visual",
      );

    } finally {

      setLoading(false);

    }

  }

  /* =======================================================
     RESET TOPIC
  ======================================================= */

  async function resetTopicVisuals() {

    if (
      !window.confirm(
        "Delete all topic visuals?",
      )
    ) {
      return;
    }

    try {

      setLoading(true);

      const res =
        await api.post(
          "/visuals/topic/reset",
          {
            id_topic:
              entityId,
          },
        );

      if (
        res.status !==
        "ok"
      ) {

        throw new Error(
          "Reset failed",
        );

      }

      onUpdated();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Error resetting visuals",
      );

    } finally {

      setLoading(false);

    }

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="p-4 border rounded bg-white space-y-6">

      <div>

        <h2 className="text-xl font-semibold text-ratecard-blue">

          Visuals

        </h2>

        <p className="text-sm text-gray-600">

          Upload the visuals associated with this {label}.

        </p>

      </div>

      {loading && (

        <p className="text-sm text-gray-500">

          Processing...

        </p>

      )}

      {/* =================================================== */}
      {/* TOPIC SQUARE */}
      {/* =================================================== */}

      {entityType ===
        "topic" && (

        <div className="space-y-2">

          <p className="text-sm font-medium">

            Square

          </p>

          {squareUrl ? (

            <div className="border rounded p-4 w-fit bg-white">

              <img
                src={squareUrl}
                alt="Square"
                className="w-24 h-24 object-contain"
              />

            </div>

          ) : (

            <div className="w-24 h-24 border rounded bg-gray-100 flex items-center justify-center text-xs text-gray-500">

              None

            </div>

          )}

          <input
            type="file"
            accept="image/*"
            onChange={(e) => {

              const file =
                e.target.files?.[0];

              if (file) {

                upload(
                  file,
                  "square",
                );

              }

            }}
          />

        </div>

      )}

      {/* =================================================== */}
      {/* RECTANGLE */}
      {/* =================================================== */}

      <div className="space-y-2">

        <p className="text-sm font-medium">

          {entityType ===
          "topic"
            ? "Rectangle"
            : "Logo"}

        </p>

        {rectUrl ? (

          <div className="max-w-xl border rounded bg-white p-8 flex items-center justify-center">

            <img
              src={rectUrl}
              alt={label}
              className="max-h-40 w-auto object-contain"
            />

          </div>

        ) : (

          <div className="max-w-xl h-40 bg-gray-100 border rounded flex items-center justify-center text-sm text-gray-500">

            No visual

          </div>

        )}

        <input
          type="file"
          accept="image/*"
          onChange={(e) => {

            const file =
              e.target.files?.[0];

            if (!file) {
              return;
            }

            upload(

              file,

              entityType ===
              "topic"
                ? "rectangle"
                : undefined,

            );

          }}
        />

      </div>

      {/* =================================================== */}
      {/* RESET */}
      {/* =================================================== */}

      {entityType ===
        "topic" && (

        <button
          type="button"
          onClick={
            resetTopicVisuals
          }
          className="px-4 py-2 rounded bg-red-600 text-white text-sm"
        >

          Reset visuals

        </button>

      )}

    </div>

  );

}
