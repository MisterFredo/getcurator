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
  input_mode?: "pdf" | "json";
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

function isRunning(
  job: Job | null,
): boolean {
  return Boolean(
    job
    && ["queued", "in_progress"].includes(
      job.status,
    ),
  );
}

function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "Une erreur est survenue.";
}

function remember(
  job: Job,
) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(job),
    );
  } catch {
    // Keep the running job visible even without storage.
  }
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

  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  window.setTimeout(
    () => URL.revokeObjectURL(url),
    1000,
  );
}


export default function ProductionPdfTestPage() {
  const [productionId, setProductionId] =
    useState(
      "f9831d4b-0141-4ab1-b65d-f83e08c636ba",
    );

  const [prototype, setPrototype] =
    useState<File | null>(null);

  const [job, setJob] =
    useState<Job | null>(null);

  const [busy, setBusy] =
    useState(false);

  const [ready, setReady] =
    useState(false);

  const [paused, setPaused] =
    useState(false);

  const [error, setError] =
    useState("");

  const submitting =
    useRef(false);

  const running = isRunning(job);

  const jobId = job?.id;
  const jobStatus = job?.status;

  useEffect(() => {
    try {
      const saved =
        localStorage.getItem(
          STORAGE_KEY,
        );

      if (saved) {
        const parsed: unknown =
          JSON.parse(saved);

        if (
          parsed
          && typeof parsed === "object"
          && "id" in parsed
          && "status" in parsed
          && typeof parsed.id === "string"
          && typeof parsed.status === "string"
        ) {
          setJob(parsed as Job);
        }
      }
    } catch {
      // Storage is optional.
    }

    setReady(true);
  }, []);

  useEffect(() => {
    if (
      !jobId
      || !jobStatus
      || !["queued", "in_progress"].includes(
        jobStatus,
      )
      || paused
    ) {
      return;
    }

    let stopped = false;

    let timer:
      ReturnType<typeof setTimeout>
      | undefined;

    const responseId = jobId;

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

        setJob(response.job);
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
    jobId,
    jobStatus,
    paused,
  ]);

  async function generate() {
    if (
      submitting.current
      || running
    ) {
      return;
    }

    setError("");

    const id = productionId.trim();

    if (!id || !prototype) {
      setError(
        "Renseigne la production "
        + "et sélectionne le prototype PDF.",
      );
      return;
    }

    if (
      !/\.pdf$/i.test(
        prototype.name,
      )
    ) {
      setError(
        "Le prototype doit être un PDF.",
      );
      return;
    }

    if (prototype.size > MAX_BYTES) {
      setError(
        "Le prototype dépasse 20 Mo.",
      );
      return;
    }

    submitting.current = true;
    setBusy(true);

    try {
      const form = new FormData();

      form.append(
        "prototype",
        prototype,
      );

      const headers:
        Record<string, string> = {};

      try {
        const userId =
          localStorage.getItem(
            "user_id",
          );

        if (userId) {
          headers["x-user-id"] =
            userId;
        }
      } catch {
        // Cookie authentication may still be available.
      }

      const response = await fetch(
        `${BASE_URL}/production/`
        + encodeURIComponent(id)
        + "/pdf-test/jobs",
        {
          method: "POST",
          headers,
          credentials: "include",
          body: form,
        },
      );

      const raw =
        await response.text();

      let data: {
        detail?: unknown;
        job?: Job;
      };

      try {
        data = JSON.parse(raw);
      } catch {
        throw new Error(
          "Réponse serveur non JSON "
          + `(HTTP ${response.status}). `
          + "L'acceptation de la génération "
          + "n'est pas confirmée.",
        );
      }

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(
                data.detail ?? data,
              ),
        );
      }

      if (
        !data.job
        || typeof data.job.id !== "string"
        || typeof data.job.status !== "string"
      ) {
        throw new Error(
          "Identifiant de génération absent. "
          + "Consulte les logs avant de relancer.",
        );
      }

      setJob(data.job);
      remember(data.job);
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
          Essai depuis les rapports sauvegardés
        </h1>

        <p className="mt-2 text-gray-600">
          Les trois rapports sont récupérés
          directement depuis la production.
          Importe uniquement le prototype PDF.
        </p>
      </div>

      <div className="rounded-xl border bg-white p-6 space-y-5">
        <label className="block space-y-2">
          <span className="block font-medium">
            Identifiant de la production
          </span>

          <input
            type="text"
            value={productionId}
            disabled={busy || running}
            onChange={event => {
              setProductionId(
                event.target.value,
              );
            }}
            className="w-full rounded-lg border px-3 py-2"
          />

          <span className="block text-sm text-gray-500">
            La production Audio est préremplie.
            Ses trois rapports figés serviront
            de sources factuelles.
          </span>
        </label>

        <label className="block space-y-2">
          <span className="block font-medium">
            Prototype de référence — PDF
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

              setError("");
            }}
          />
        </label>

        <button
          type="button"
          disabled={
            !ready
            || busy
            || running
            || !productionId.trim()
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
            ? "Préparation de l’essai…"
            : running
              ? "Génération en cours…"
              : "Générer depuis les rapports sauvegardés"}
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
              Dernière génération
            </h2>

            <p className="text-sm text-gray-600">
              État : {job.status}
              {" · "}
              Modèle : {job.model}

              {job.input_mode && (
                <>
                  {" · "}
                  Sources :
                  {" "}
                  {job.input_mode.toUpperCase()}
                </>
              )}
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
                est partiel.
              </p>

              <pre className="mt-2 whitespace-pre-wrap break-words text-xs">
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
              {" "}
              {job.refusal?.join(" ")}
            </p>
          )}

          {job.text && (
            <>
              <button
                type="button"
                className="rounded border px-4 py-2"
                onClick={() => {
                  const mode =
                    job.input_mode || "pdf";

                  const suffix =
                    job.status === "completed"
                      ? ""
                      : "-partiel";

                  download(
                    `plan-audio-${mode}${suffix}.md`,
                    job.text,
                    "text/markdown;charset=utf-8",
                  );
                }}
              >
                {job.status === "completed"
                  ? "Télécharger le plan"
                  : "Télécharger le texte partiel"}
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
                "diagnostic-production.json",
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

              <pre className="mt-2 whitespace-pre-wrap break-words text-xs">
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
