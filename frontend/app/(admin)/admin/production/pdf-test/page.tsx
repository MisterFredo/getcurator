"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import Link from "next/link";
import ProductionDocumentPreview from "@/components/admin/production/ProductionDocumentPreview";
import type { ProductionDocument } from "@/types/production-document";

import {
  api,
} from "@/lib/api";


type Job = {
  id: string;
  status: string;
  model: string;
  text: string;
  input_mode?: "pdf" | "json";
  stage?: "plan" | "report_draft" | "document";
  document?: ProductionDocument | null;
  validation_notes?: string[];
  production_id?: string | null;
  corpus_sha256?: string | null;
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
const REVIEW_KEY = "getcurator-production-reviewed-plan";

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

  const [reviewedPlan, setReviewedPlan] = useState("");
  const [reviewProductionId, setReviewProductionId] = useState("");
  const [writing, setWriting] = useState(false);
  const [storageWarning, setStorageWarning] = useState("");

  const submitting =
    useRef(false);

  const running = isRunning(job);

  const jobId = job?.id;
  const jobStatus = job?.status;
  const jobStage = job?.stage;

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

    try {
      const savedReview = localStorage.getItem(REVIEW_KEY);
      if (savedReview) {
        const review = JSON.parse(savedReview);
        if (typeof review?.text === "string"
          && typeof review?.productionId === "string") {
          setReviewedPlan(review.text);
          setReviewProductionId(review.productionId);
        }
      }
    } catch {
      setStorageWarning("La restauration du plan relu a échoué. Conserve une copie téléchargée.");
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(REVIEW_KEY, JSON.stringify({
        text: reviewedPlan,
        productionId: reviewProductionId,
      }));
    } catch {
      setStorageWarning("Le plan relu ne peut pas être sauvegardé dans ce navigateur. Télécharge une copie avant de quitter.");
    }
  }, [ready, reviewedPlan, reviewProductionId]);

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
          (jobStage === "document" ? "/production/documents/jobs/" : "/production/pdf-test/jobs/")
          + encodeURIComponent(
            responseId,
          ),
        );

        if (stopped) {
          return;
        }

        // Preserve client-side provenance for older backend responses.
        setJob(previous => {
          const next = {
            ...response.job,
            production_id: response.job.production_id || previous?.production_id,
            stage: response.job.stage || previous?.stage,
          };
          remember(next);
          return next;
        });

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
    jobStage,
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

      const nextJob: Job = {
        ...data.job,
        production_id: id,
        stage: "plan",
      };
      setJob(nextJob);
      remember(nextJob);
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

  async function writeReport() {
    if (submitting.current || running) return;
    const id = reviewProductionId.trim();
    if (!id || !reviewedPlan.trim()) {
      setError("Renseigne la production et le plan relu.");
      return;
    }
    if (reviewedPlan.length > 150_000) {
      setError("Le plan dépasse la limite de 150 000 caractères.");
      return;
    }
    submitting.current = true;
    setBusy(true);
    setWriting(true);
    setError("");
    try {
      const response: { status: string; job: Job } = await api.post(
        "/production/" + encodeURIComponent(id) + "/documents/jobs",
        { reviewed_plan: reviewedPlan },
      );
      if (!response.job?.id || !response.job?.status) {
        throw new Error("Réponse sans identifiant de rédaction. Consulte les logs avant de relancer.");
      }
      const nextJob: Job = {
        ...response.job,
        production_id: id,
        stage: "document",
      };
      setJob(nextJob);
      remember(nextJob);
      setPaused(false);
    } catch (err) {
      setError(errorMessage(err) + " Aucune relance automatique n'a été effectuée. Vérifie les logs avant de relancer.");
    } finally {
      submitting.current = false;
      setBusy(false);
      setWriting(false);
    }
  }

  async function revalidateDocument() {
    if (busy || !job || job.stage !== "document") return;
    setBusy(true);
    setError("");
    try {
      const response: { status: string; job: Job } = await api.get(
        "/production/documents/jobs/" + encodeURIComponent(job.id),
      );
      setJob(response.job);
      remember(response.job);
      setPaused(false);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
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
          Production depuis les rapports sauvegardés
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
            ? (writing ? "Démarrage de la rédaction…" : "Préparation du plan…")
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

      <section className="rounded-xl border bg-white p-6 space-y-4">
        <h2 className="text-lg font-semibold">Plan relu et rédaction</h2>
        <p className="text-sm text-gray-600">
          Charge le dernier plan terminé ou colle une version déjà téléchargée.
          Relis et corrige son contenu avant de lancer la rédaction et la composition.
          Le prototype PDF n’est pas nécessaire pour cette étape.
        </p>
        <button
          type="button"
          disabled={busy || running || !job?.text || job.status !== "completed" || (job.stage === "report_draft" || job.stage === "document")}
          className="rounded border px-4 py-2 disabled:opacity-50"
          onClick={() => {
            if (!job?.text) return;
            if (reviewedPlan.trim() && reviewedPlan !== job.text
              && !window.confirm("Remplacer le plan actuellement présent dans l’éditeur ?")) return;
            setReviewedPlan(job.text);
            setReviewProductionId(job.production_id || productionId.trim());
          }}
        >Charger le dernier plan dans l’éditeur</button>
        <label className="block space-y-2">
          <span className="block text-sm font-medium">Production dont les rapports seront utilisés</span>
          <input
            type="text"
            value={reviewProductionId}
            disabled={busy || running}
            onChange={event => setReviewProductionId(event.target.value)}
            className="w-full rounded border px-3 py-2"
          />
        </label>
        <p className="text-xs text-gray-500">
          Vérifie que cet identifiant correspond aux rapports ayant servi au plan.
          Pour un ancien résultat sans provenance enregistrée, l’identifiant du formulaire est repris : vérifie-le.
        </p>
        <label className="block space-y-2">
          <span className="block text-sm font-medium">Plan à valider</span>
          <textarea
            value={reviewedPlan}
            disabled={busy || running}
            onChange={event => setReviewedPlan(event.target.value)}
            placeholder="Colle ici le plan relu et corrigé…"
            rows={20}
            className="w-full rounded-lg border p-4 font-mono text-sm"
          />
        </label>
        {storageWarning && <p role="alert" className="text-sm text-amber-700">{storageWarning}</p>}
        <p className="text-xs text-gray-500">Le plan édité est conservé dans ce navigateur, pas encore dans BigQuery.</p>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled={!reviewedPlan.trim()}
            className="rounded border px-4 py-2 disabled:opacity-50"
            onClick={() => download("plan-audio-relu.md", reviewedPlan, "text/markdown;charset=utf-8")}
          >Télécharger le plan relu</button>
          <button
            type="button"
            disabled={!ready || busy || running || !reviewedPlan.trim() || !reviewProductionId.trim()}
            onClick={() => void writeReport()}
            className="rounded-lg bg-ratecard-blue px-5 py-3 text-white disabled:opacity-50"
          >{writing ? "Démarrage de la rédaction…" : "Valider le plan et produire le document"}</button>
        </div>
      </section>

      {job && (
        <section className="rounded-xl border bg-white p-6 space-y-4">
          <div>
            <h2 className="text-lg font-semibold">
              {job.stage === "document" ? "Document structuré" : job.stage === "report_draft" ? "Rapport rédigé" : "Dernier plan généré"}
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
              {job.production_id && <> · Production : {job.production_id}</>}
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
                {job.status === "validation_failed"
                  ? "La réponse a été reçue, mais les contrôles du document l’ont rejetée. Le détail est indiqué ci-dessous."
                  : "La génération ne s’est pas terminée correctement. Le texte éventuel peut être partiel."}
              </p>

              {job.stage === "document" && job.status === "validation_failed" && (
                <button type="button" disabled={busy} onClick={() => void revalidateDocument()} className="mt-3 rounded border px-4 py-2 disabled:opacity-50">
                  Revérifier le document existant sans régénérer
                </button>
              )}
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
              Aucun contenu exploitable retourné.
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
                    job.stage === "document"
                      ? `document-getcurator${suffix}.json`
                      : job.stage === "report_draft"
                      ? `rapport-audio-redige${suffix}.md`
                      : `plan-audio-${mode}${suffix}.md`,
                    job.text,
                    job.stage === "document" ? "application/json" : "text/markdown;charset=utf-8",
                  );
                }}
              >
                {job.status === "completed"
                  ? (job.stage === "document" ? "Télécharger le document JSON" : job.stage === "report_draft" ? "Télécharger le rapport rédigé" : "Télécharger le plan")
                  : "Télécharger le texte partiel"}
              </button>

              {job.stage !== "document" && <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-7">{job.text}</pre>}
              {job.stage === "document" && <details><summary className="cursor-pointer text-sm">JSON de génération et diagnostic</summary><pre className="mt-3 whitespace-pre-wrap break-words text-xs">{job.text}</pre></details>}
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
      {job?.stage === "document" && job.status === "completed" && job.document && (
        <ProductionDocumentPreview document={job.document} />
      )}
      {job?.stage === "document" && job.validation_notes && (
        <ul className="list-disc pl-5 text-xs text-gray-600">{job.validation_notes.map((note, index) => <li key={index}>{note}</li>)}</ul>
      )}
    </div>
  );
}
