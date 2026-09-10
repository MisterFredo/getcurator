"use client";

import NumbersTransformation from "@/components/admin/numbers/NumbersTransformation";

/* =========================================================
   PAGE
========================================================= */

export default function NumbersPage() {

  return (

    <div className="space-y-6">

      {/* HEADER */}

      <div>

        <h1 className="text-2xl font-semibold text-ratecard-blue">
          Numbers
        </h1>

        <p className="mt-2 text-sm text-gray-600">
          Transform and validate Numbers extracted from published contents.
        </p>

      </div>

      {/* TRANSFORMATION */}

      <NumbersTransformation />

    </div>
  );
}
