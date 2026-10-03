"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";


type Props = {
  expertId: string | null;
  disabled?: boolean;
  onBusyChange: (busy: boolean) => void;
};

type Preparation = {
  status: string;
  prepared_count: number;
  skipped_count: number;
  failed_count: number;
  editions: Array<{
    edition_id: string;
    period_start: string;
    status: string;
    error?: string;
  }>;
};


/* =========================================================
   PREPARE ONE EXPERT'S MONTHLY CORPORA
========================================================= */

export default function TouchExpertMonthlyActions({
  expertId,
  disabled = false,
  onBusyChange,
}: Props) {
  const [loading, setLoading] = useState<1 | 3 | null>(null);
  const [result, setResult] = useState<Preparation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const runningRef = useRef(false);

  useEffect(() => {
    setResult(null);
    setError(null);
  }, [expertId]);

  async function prepare(monthsCount: 1 | 3) {
    if (!expertId || disabled || runningRef.current) return;

    runningRef.current = true;
    setLoading(monthsCount);
    setResult(null);
    setError(null);
    onBusyChange(true);

    try {
      const response: {
        status: string;
        preparation: Preparation;
      } = await api.post(
        "/touch/editions/prepare",
        {
          expert_id: expertId,
          months_count: monthsCount,
        },
      );
      setResult(response.preparation);
    } catch (exception) {
      setError(
        exception instanceof Error
          ? exception.message
          : "Unable to prepare monthly editions.",
      );
    } finally {
      runningRef.current = false;
      setLoading(null);
      onBusyChange(false);
    }
  }

  if (!expertId) return null;

  return (
    <div className="mt-4 border-t border-gray-100 pt-4">
      <p className="text-sm font-medium text-gray-900">
        Monthly expert editions
      </p>
      <p className="mt-1 text-xs text-gray-500">
        Prepare complete calendar months for manual corpus review.
        Existing editions are preserved.
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={disabled || loading !== null}
          onClick={() => void prepare(3)}
          className="rounded-lg bg-ratecard-blue px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading === 3 ? "Preparing…" : "Prepare last 3 months"}
        </button>
        <button
          type="button"
          disabled={disabled || loading !== null}
          onClick={() => void prepare(1)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 disabled:opacity-50"
        >
          {loading === 1 ? "Preparing…" : "Prepare latest complete month"}
        </button>
      </div>

      {loading !== null && (
        <p className="mt-3 text-sm text-blue-700" role="status">
          Preparing the research corpora. This may take several minutes.
        </p>
      )}

      {error && (
        <p className="mt-3 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      {result && (
        <div
          className={
            "mt-3 rounded-lg border p-3 text-sm "
            + (result.failed_count > 0
              ? "border-amber-200 bg-amber-50 text-amber-800"
              : "border-green-200 bg-green-50 text-green-800")
          }
          role="status"
        >
          <p>
            {result.prepared_count} editions ready for review
            {" · "}
            {result.skipped_count} existing editions preserved
            {" · "}
            {result.failed_count} failed
          </p>

          {result.editions.map(edition => (
            <p key={edition.edition_id} className="mt-1 text-xs">
              {edition.period_start.slice(0, 7)}
              {" — "}
              {edition.status === "TO_REVIEW"
                ? "Ready for review"
                : edition.status === "BUILDING"
                  ? "Preparation in progress"
                  : edition.status === "GENERATED"
                    ? "Report generated"
                    : edition.status}
              {edition.error ? ` — ${edition.error}` : ""}
            </p>
          ))}

          <Link
            href="/admin/touch/reports"
            className="mt-3 inline-block font-medium underline"
          >
            View reports and editions
          </Link>
        </div>
      )}
    </div>
  );
}
