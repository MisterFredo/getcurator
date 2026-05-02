"use client";

import { useState } from "react";

import NumbersManualCreate from "@/components/admin/numbers/NumbersManualCreate";
import NumbersAdminList from "@/components/admin/numbers/NumbersAdminList";
import NumbersBacklogExplorer from "@/components/admin/numbers/NumbersBacklogExplorer";

/* ========================================================= */

export default function NumbersPage() {

  const [tab, setTab] = useState<"content" | "official">("content");

  return (

    <div className="space-y-6">

      {/* HEADER */}
      <div className="flex items-center justify-between">

        <h1 className="text-2xl font-semibold text-ratecard-blue">
          Numbers
        </h1>

      </div>

      {/* TABS */}
      <div className="flex gap-4">

        <button
          onClick={() => setTab("content")}
          className={`px-3 py-1 rounded ${
            tab === "content"
              ? "bg-ratecard-blue text-white"
              : "bg-gray-200"
          }`}
        >
          Content Numbers
        </button>

        <button
          onClick={() => setTab("official")}
          className={`px-3 py-1 rounded ${
            tab === "official"
              ? "bg-ratecard-blue text-white"
              : "bg-gray-200"
          }`}
        >
          Official Numbers
        </button>

      </div>

      {/* CONTENT */}

      {tab === "content" && (
        <NumbersBacklogExplorer />
      )}

      {tab === "official" && (
        <div className="space-y-6">
          <NumbersManualCreate />
          <NumbersAdminList />
        </div>
      )}

    </div>
  );
}
