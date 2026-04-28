"use client";

import { useState } from "react";

import NumbersManualCreate from "@/components/admin/numbers/NumbersManualCreate";
import NumbersAssistantCreate from "@/components/admin/numbers/NumbersAssistantCreate";
import NumbersAdminList from "@/components/admin/numbers/NumbersAdminList";
import NumbersRawExplorer from "@/components/admin/numbers/NumbersRawExplorer";

/* ========================================================= */

export default function NumbersPage() {

  const [tab, setTab] = useState<"raw" | "assistant" | "manual" | "admin">("raw");

  /* ========================================================= */

  return (

    <div className="space-y-6">

      {/* HEADER */}
      <h1 className="text-2xl font-semibold text-ratecard-blue">
        Numbers
      </h1>

      {/* TABS */}
      <div className="flex gap-4">

        <button
          onClick={() => setTab("raw")}
          className={`px-3 py-1 rounded ${
            tab === "raw"
              ? "bg-ratecard-blue text-white"
              : "bg-gray-200"
          }`}
        >
          Raw
        </button>

        <button
          onClick={() => setTab("assistant")}
          className={`px-3 py-1 rounded ${
            tab === "assistant"
              ? "bg-ratecard-blue text-white"
              : "bg-gray-200"
          }`}
        >
          Assistant
        </button>

        <button
          onClick={() => setTab("manual")}
          className={`px-3 py-1 rounded ${
            tab === "manual"
              ? "bg-ratecard-blue text-white"
              : "bg-gray-200"
          }`}
        >
          Manual
        </button>

        <button
          onClick={() => setTab("admin")}
          className={`px-3 py-1 rounded ${
            tab === "admin"
              ? "bg-ratecard-blue text-white"
              : "bg-gray-200"
          }`}
        >
          Admin
        </button>

      </div>

      {/* CONTENT */}

      {tab === "raw" && <NumbersRawExplorer />}

      {tab === "assistant" && <NumbersAssistantCreate />}

      {tab === "manual" && <NumbersManualCreate />}

      {tab === "admin" && <NumbersAdminList />}

    </div>
  );
}
