"use client";

import { useState } from "react";
import { api } from "@/lib/api";

import NumbersManualCreate from "@/components/admin/numbers/NumbersManualCreate";
import NumbersAssistantCreate from "@/components/admin/numbers/NumbersAssistantCreate";
import NumbersAdminList from "@/components/admin/numbers/NumbersAdminList";
import NumbersBacklogExplorer from "@/components/admin/numbers/NumbersBacklogExplorer";

/* ========================================================= */

export default function NumbersPage() {

  const [tab, setTab] = useState<"backlog" | "assistant" | "manual" | "admin">("backlog");

  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);

  /* ========================================================= */

  async function runBacklog() {

    try {

      setRunning(true);
      setResult(null);

      const res = await api.post("/numbers/backlog/run?limit=200");

      setResult(res);

    } catch (e) {
      console.error(e);
      alert("Erreur run backlog");
    }

    setRunning(false);
  }

  /* ========================================================= */

  return (

    <div className="space-y-6">

      {/* HEADER */}
      <div className="flex items-center justify-between">

        <h1 className="text-2xl font-semibold text-ratecard-blue">
          Numbers
        </h1>

        {/* 🔥 RUN BACKLOG */}
        <button
          onClick={runBacklog}
          disabled={running}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          {running ? "Running..." : "Run Backlog"}
        </button>

      </div>

      {/* RESULT */}
      {result && (
        <div className="text-sm bg-gray-100 p-3 rounded">

          <div><b>Processed:</b> {result.processed}</div>
          <div><b>Keep:</b> {result.keep}</div>
          <div><b>Reject:</b> {result.reject}</div>

        </div>
      )}

      {/* TABS */}
      <div className="flex gap-4">

        <button
          onClick={() => setTab("backlog")}
          className={`px-3 py-1 rounded ${
            tab === "backlog"
              ? "bg-ratecard-blue text-white"
              : "bg-gray-200"
          }`}
        >
          Backlog
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

      {tab === "backlog" && <NumbersBacklogExplorer />}

      {tab === "assistant" && <NumbersAssistantCreate />}

      {tab === "manual" && <NumbersManualCreate />}

      {tab === "admin" && <NumbersAdminList />}

    </div>
  );
}
