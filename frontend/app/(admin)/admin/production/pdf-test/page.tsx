"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import Link from "next/link";

import {
  api,
} from "@/lib/api";


type Job = {
  id: string;
  status: string;
  model: string;
  text: string;
  usage: Record<string, unknown> | null;
  error: unknown;
  incomplete_details: unknown;
  refusal: string[];
};

const STORAGE_KEY =
  "getcurator-production-pdf-test";

const BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL
  || "https://ratecard.onrender.com/api"
).replace(/\/+$/, "");

const MAX_BYTES = 20_000_000;

function isRunning(job: Job | null): boolean {
  return Boolean(
    job
    && ["queued", "in_progress"].includes(
      job.status,
    ),
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Une erreur est survenue.";
}

function download(
  filename: string,
  content: string,
  type: string,
) {
  const url = URL.createObjectURL(
    new Blob(
      [content],
      { type },
    ),
  );

  const anchor =
    document.createElement("a");

  anchor.href = url;
  anchor.download = filename;
  anchor.click();

  window.setTimeout(
    () => URL.revokeObjectURL(url),
    1000,
  );
}


export default function ProductionPdfTestPage() {
  const [sources, setSources] =
    useState<File[]>([]);

  const [prototype, setPrototype] =
    useState<File | null>(null);

  const [job, setJob] =
    useState<Job | null>(null);

  const [busy, setBusy] =
    useState(false);

  const [error, setError] =
    useState("");

  const [paused, setPaused] =
    useState(false);

  const [ready, setReady] =
    useState(false);

  const submitting =
    useRef(false);

  useEffect(() => {
    try {
      const saved =
        localStorage.getItem(
          STORAGE_KEY,
        );

      if (saved) {
        const parsed =
          JSON.parse(saved) as Job;

        if (
          typeof parsed.id === "string"
          && typeof parsed.status === "string"
        ) {
          setJob(parsed);
        }
      }
    } catch {
      // The page remains usable if storage is unavailable.
    }

    setReady(true);
  }, []);

  function remember(nextJob: Job) {
    setJob(nextJob);

    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(nextJob),
      );
    } catch {
      // Storage failure must not hide a started job.
    }
  }

  useEffect(() => {
    if (
      !job
      || !isRunning(job)
      || paused
    ) {
      return;
    }

    let stopped = false;
    let timer:
      ReturnType<typeof setTimeout>
      | undefined;

    const responseId = job.id;

    async function poll() {
      try {
        const response: {
          status: string;
          job: Job;
        } = await api.get(
          "/production/pdf-test/jobs/"
          + encodeURIComponent(
            responseId,
          ),
        );

        if (stopped) {
          return;
        }

        remember(response.job);

        if (isRunning(response.job)) {
          timer = setTimeout(
            poll,
            4000,
          );
        }
      } catch (err) {
        if (!stopped) {
          setError(
            errorMessage(err),
          );

          setPaused(true);
        }
      }
    }

    void poll();

    return () => {
      stopped = true;

      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [
    job?.id,
    job?.status,
    paused,
  ]);

  async function generate() {
    if (submitting.current) {
      return;
    }

    setError("");

    if (
      sources.length !== 3
      || !prototype
    ) {
      setError(
        "Sélectionne trois rapports "
        + "et un prototype.",
      );
      return;
    }

    const total = [
      ...sources,
      prototype,
    ].reduce(
      (sum, file) => sum + file.size,
      0,
    );

    if (total > MAX_BYTES) {
      setError(
        "Les quatre PDF doivent totaliser "
        + "au maximum 20 Mo.",
      );
      return;
    }

    submitting.current = true;
    setBusy(true);

    try {
      const form = new FormData();

      sources.forEach(file => {
        form.append(
          "sources",
          file,
        );
      });

      form.append(
        "prototype",
        prototype,
      );

      const userId =
        localStorage.getItem(
          "user_id",
        );

      const headers:
        Record<string, string> = {};

      if (userId) {
        headers["x-user-id"] =
          userId;
      }

      const response = await fetch(
        `${BASE_URL}/production/pdf-test/jobs`,
        {
          method: "POST",
          headers,
          credentials: "include",
          body: form,
        },
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data),
        );
      }

      remember(data.job as Job);
      setPaused(false);
    } catch (err) {
      setError(
        errorMessage(err)
        + " Aucune relance automatique "
        + "n'a été effectuée.",
      );
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  const running = isRunning(job);

  return (
    <div className="max-w-5xl space-y-6">
      <Link
        href="/admin/production"
        className="text-sm underline"
      >
        Retour aux productions
      </Link>

      <div>
        <h1 className="text-2xl font-semibold">
          Essai de production à partir des PDF
        </h1>

        <p className="mt-2 text-gray-600">
          Trois rapports apportent les faits.
          Le prototype sert de référence éditoriale.
        </p>
      </div>

      <div className="rounded-xl border bg-white p-6 space-y-5">
        <label className="block space-y-2">
          <span className="block font-medium">
            Les trois rapports sources
          </span>

          <input
            type="file"
            accept=".pdf,application/pdf"
            multiple
            disabled={busy || running}
            onChange={event => {
              setSources(
                Array.from(
                  event.target.files || [],
                ),
              );
            }}
          />

          <span className="block text-sm text-gray-500">
            {sources.length} rapport(s) sélectionné(s)
          </span>
        </label>

        {sources.length > 0 && (
          <ul className="text-sm text-gray-600 space-y-1">
            {sources.map((file, index) => (
              <li key={`${file.name}-${index}`}>
                {index + 1}. {file.name}
              </li>
            ))}
          </ul>
        )}

        <label className="block space-y-2">
          <span className="block font-medium">
            Prototype de référence
          </span>

          <input
            type="file"
            accept=".pdf,application/pdf"
            disabled={busy || running}
            onChange={event => {
              setPrototype(
                event.target.files?.[0]
                || null,
              );
            }}
          />
        </label>

        <button
          type="button"
          disabled={
            !ready
            || busy
            || running
            || sources.length !== 3
            || !prototype
          }
          onClick={() => void generate()}
          className="
            rounded-lg bg-ratecard-blue
            px-5 py-3 text-white
            disabled:opacity-50
          "
        >
          {busy
            ? "Envoi des PDF…"
            : running
              ? "Génération en cours…"
              : "Générer un nouveau plan"}
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800"
        >
          <p>{error}</p>

          {paused && running && (
            <button
              type="button"
              className="mt-3 underline"
              onClick={() => {
                setError("");
                setPaused(false);
              }}
            >
              Reprendre le suivi sans relancer
              la génération
            </button>
          )}
        </div>
      )}

      {job && (
        <section className="rounded-xl border bg-white p-6 space-y-4">
          <div>
            <h2 className="text-lg font-semibold">
              Résultat de l’essai
            </h2>

            <p className="text-sm text-gray-600">
              État : {job.status}
              {" · "}
              Modèle : {job.model}
            </p>

            <p className="mt-1 break-all text-xs text-gray-500">
              Identifiant : {job.id}
            </p>
          </div>

          {running && (
            <p>
              Le traitement continue en arrière-plan.
              Le résultat apparaîtra automatiquement.
            </p>
          )}

          {!running && job.status !== "completed" && (
            <div className="rounded bg-amber-50 p-4">
              <p>
                La génération n’est pas terminée
                correctement. Le texte éventuel
                peut être partiel.
              </p>

              <pre className="mt-2 whitespace-pre-wrap text-xs">
                {JSON.stringify(
                  job.error
                  || job.incomplete_details
                  || job.refusal,
                  null,
                  2,
                )}
              </pre>
            </div>
          )}

          {job.status === "completed" && !job.text && (
            <p className="text-red-700">
              Aucun plan exploitable retourné.
              {job.refusal?.join(" ")}
            </p>
          )}

          {job.text && (
            <>
              <button
                type="button"
                className="rounded border px-4 py-2"
                onClick={() => {
                  download(
                    "plan-audio-pdf.md",
                    job.text,
                    "text/markdown;charset=utf-8",
                  );
                }}
              >
                Télécharger le plan
              </button>

              <pre className="
                whitespace-pre-wrap
                break-words font-sans
                text-sm leading-7
              ">
                {job.text}
              </pre>
            </>
          )}

          <button
            type="button"
            className="text-sm underline"
            onClick={() => {
              download(
                "diagnostic-production-pdf.json",
                JSON.stringify(
                  job,
                  null,
                  2,
                ),
                "application/json",
              );
            }}
          >
            Télécharger le diagnostic
          </button>

          {job.usage && (
            <details>
              <summary className="cursor-pointer text-sm">
                Consommation de tokens
              </summary>

              <pre className="mt-2 whitespace-pre-wrap text-xs">
                {JSON.stringify(
                  job.usage,
                  null,
                  2,
                )}
              </pre>
            </details>
          )}
        </section>
      )}
    </div>
  );
}
