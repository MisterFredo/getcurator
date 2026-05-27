// app/(admin)/admin/digest/page.tsx

"use client";

import { useState } from "react";

export default function DigestPage() {

  const [loading] =
    useState(false);

  return (

    <div className="space-y-4">

      {/* HEADER */}

      <div className="flex items-center justify-between">

        <h1 className="text-lg font-semibold tracking-tight">
          Digest
        </h1>

      </div>

      {/* TEMP PLACEHOLDER */}

      <div className="border border-gray-200 rounded-lg bg-white p-6">

        <div className="text-sm font-medium text-gray-900">
          Digest en cours de migration
        </div>

        <div className="mt-2 text-sm text-gray-500">
          La nouvelle architecture Digest basée sur
          RATECARD_CONTENT est en cours de mise en place.
        </div>

        {loading && (
          <div className="mt-4 text-xs text-gray-400">
            Chargement...
          </div>
        )}

      </div>

    </div>
  );
}
