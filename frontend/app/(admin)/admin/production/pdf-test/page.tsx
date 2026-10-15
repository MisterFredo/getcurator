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


/* =========================================================
   TYPES
========================================================= */

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

type JobResponse = {
  status: string;
  job: Job;
};


/* =========================================================
   CONFIGURATION
========================================================= */

const STORAGE_KEY =
  "getcurator-production-pdf-test";

const BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL
  || "https://ratecard.onrender.com/api"
).replace(/\/+$/, "");

const MAX_BYTES = 20_000_000;


/* =========================================================
   HELPERS
========================================================= */

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

function validateSources(
  sources: File[],
): string | null {
  if (sources.length === 1) {
    if (
      !/\.(json|jsonl|txt)$/i.test(
        sources[0].name,
      )
    ) {
      return (
        "Pour un seul fichier source, "
        + "sélectionne un export "
        + ".json, .jsonl ou .txt "
        + "contenant les trois rapports."
      );
    }

    return null;
  }

  if (sources.length === 3) {
    if (
      !sources.every(file =>
        /\.pdf$/i.test(file.name),
      )
    ) {
      return (
        "Pour trois fichiers sources, "
        + "sélectionne uniquement des PDF."
      );
    }

    return null;
  }

  return (
    "Sélectionne trois PDF ou un export "
    + "JSON contenant trois rapports."
  );
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

function rememberJob(
  job: Job,
) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(job),
    );
  } catch {
    // Storage failure must not hide a started job.
  }
}


/* =========================================================
   PAGE
========================================================= */

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

  const running = isRunning(job);

  const sourceError =
    validateSources(sources);

  const selectedMode =
    sources.length === 1
      ? "json"
      : sources.length === 3
        ? "pdf"
        : null;

  const totalBytes = [
    ...sources,
    ...(prototype ? [prototype] : []),
  ].reduce(
    (sum, file) => sum + file.size,
    0,
  );


  /* =======================================================
     RESTORE LAST JOB
  ======================================================= */

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
      // The page remains usable without local storage.
    }

    setReady(true);
  }, []);


  /* =======================================================
     POLL CURRENT JOB
  ======================================================= */

  const jobId = job?.id;
  const jobStatus = job?.status;

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
        const response: JobResponse =
          await api.get(
            "/production/pdf-test/jobs/"
            + encodeURIComponent(
              responseId,
            ),
          );

        if (stopped) {
          return;
        }

        setJob(response.job);
        rememberJob(response.job);

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


  /* =======================================================
     START GENERATION
  ======================================================= */

  async function generate() {
    if (
      submitting.current
      || running
    ) {
      return;
    }

    setError("");

    const validationError =
      validateSources(sources);

    if (validationError) {
      setError(validationError);
      return;
    }

    if (
      !prototype
      || !/\.pdf$/i.test(prototype.name)
    ) {
      setError(
        "Sélectionne le prototype au format PDF.",
      );
      return;
    }

    if (totalBytes > MAX_BYTES) {
      setError(
        "Les documents doivent totaliser "
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

      let userId: string | null = null;

      try {
        userId = localStorage.getItem(
          "user_id",
        );
      } catch {
        // Cookie-based authentication may still be available.
      }

      const headers:
        Record<string, string> = {};

      if (userId) {
        headers["x-user-id"] =
          userId;
      }

      // Do not set Content-Type:
      // the browser supplies the multipart boundary.
      const response = await fetch(
        `${BASE_URL}/production/pdf-test/jobs`,
        {
          method: "POST",
          headers,
          credentials: "include",
          body: form,
        },
      );

      const rawBody =
        await response.text();

      let data: {
        detail?: unknown;
        job?: Job;
      };

      try {
        data = JSON.parse(rawBody);
      } catch {
        throw new Error(
          "Le serveur a renvoyé une réponse "
          + `non JSON (HTTP ${response.status}). `
          + "Si l'envoi a été interrompu, "
          + "l'acceptation de la génération "
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
          "La réponse ne contient pas "
          + "d'identifiant de génération exploitable. "
          + "Vérifie les logs avant de relancer.",
        );
      }

      setJob(data.job);
      rememberJob(data.job);
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


  /* =======================================================
     RENDER
  ======================================================= */

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
          Essai de production — PDF ou JSON
        </h1>

        <p className="mt-2 text-gray-600">
          Les trois rapports apportent les faits.
          Le prototype PDF sert uniquement
          de référence éditoriale.
        </p>
      </div>

      <div className="rounded-xl border bg-white p-6 space-y-5">
        <label className="block space-y-2">
          <span className="block font-medium">
            Sources : trois PDF ou un export JSON
          </span>

          <p className="text-sm text-gray-600">
            Pour le test JSON, sélectionne un seul
            fichier .json, .jsonl ou .txt contenant
            les trois rapports exportés de BigQuery.
          </p>

          <input
            type="file"
            accept=".pdf,.json,.jsonl,.txt,application/pdf,application/json,text/plain"
            multiple
            disabled={busy || running}
            onChange={event => {
              setSources(
                Array.from(
                  event.target.files || [],
                ),
              );

              setError("");
            }}
          />

          <span className="block text-sm text-gray-500">
            {sources.length} fichier(s) sélectionné(s)
          </span>
        </label>

        {sources.length > 0 && (
          <div className="space-y-2">
            <ul className="text-sm text-gray-600 space-y-1">
              {sources.map((file, index) => (
                <li key={`${file.name}-${index}`}>
                  {index + 1}. {file.name}
                </li>
              ))}
            </ul>

            {sourceError ? (
              <p className="text-sm text-amber-700">
                {sourceError}
              </p>
            ) : (
              <p className="text-sm text-emerald-700">
                Mode sélectionné :
                {" "}
                {selectedMode === "json"
                  ? "export JSON des trois rapports"
                  : "trois rapports PDF"}
              </p>
            )}
          </div>
        )}

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

        <p className="text-sm text-gray-500">
          Taille totale :
          {" "}
          {(totalBytes / 1_000_000).toFixed(2)}
          {" "}
          Mo / 20 Mo
        </p>

        <button
          type="button"
          disabled={
            !ready
            || busy
            || running
            || Boolean(sourceError)
            || !prototype
            || !/\.pdf$/i.test(prototype.name)
            || totalBytes > MAX_BYTES
          }
          onClick={() => void generate()}
          className="
            rounded-lg bg-ratecard-blue
            px-5 py-3 text-white
            disabled:opacity-50
          "
        >
          {busy
            ? "Envoi des documents…"
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
                  {job.input_mode === "json"
                    ? "JSON"
                    : "PDF"}
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
                La génération ne s’est pas terminée
                correctement. Le texte éventuel
                est à considérer comme partiel.
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
              const mode =
                job.input_mode || "pdf";

              download(
                `diagnostic-production-${mode}.json`,
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
