"use client";

import {
  useState,
} from "react";

import NumbersObservations from "@/components/admin/numbers/NumbersObservations";
import NumbersTransformation from "@/components/admin/numbers/NumbersTransformation";

/* =========================================================
   TYPES
========================================================= */

type NumbersTab =
  | "transformation"
  | "observations";

/* =========================================================
   PAGE
========================================================= */

export default function NumbersPage() {

  const [
    tab,
    setTab,
  ] = useState<NumbersTab>(
    "transformation",
  );

  return (

    <div className="space-y-6">

      {/* HEADER */}

      <div>

        <h1
          className="
            text-2xl
            font-semibold
            text-ratecard-blue
          "
        >
          Numbers
        </h1>

        <p className="mt-2 text-sm text-gray-600">
          Transform, validate and moderate Numbers extracted from published
          contents.
        </p>

      </div>

      {/* TABS */}

      <div
        className="
          flex
          flex-wrap
          gap-2
          border-b
          border-gray-200
          pb-3
        "
      >

        <button
          type="button"
          onClick={() =>
            setTab(
              "transformation",
            )
          }
          className={`
            rounded-lg
            px-4
            py-2
            text-sm
            font-medium
            ${
              tab === "transformation"
                ? "bg-ratecard-blue text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }
          `}
        >
          Transformation
        </button>

        <button
          type="button"
          onClick={() =>
            setTab(
              "observations",
            )
          }
          className={`
            rounded-lg
            px-4
            py-2
            text-sm
            font-medium
            ${
              tab === "observations"
                ? "bg-ratecard-blue text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }
          `}
        >
          Observations
        </button>

      </div>

      {/* CONTENT */}

      {tab === "transformation" && (
        <NumbersTransformation />
      )}

      {tab === "observations" && (
        <NumbersObservations />
      )}

    </div>
  );
}
