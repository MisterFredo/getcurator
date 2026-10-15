"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import {
  createProduction,
  generateProductionPlan,
  getProduction,
  getProductionPlan,
  listProductionPlans,
  listProductions,
} from "@/lib/production";

import type {
  Production,
  ProductionOutputFormat,
  ProductionPageLayout,
  ProductionPlanVersionSummary,
  ProductionSavedPlan,
  ProductionSummary,
} from "@/types/production";


/* =========================================================
   TYPES
========================================================= */

type SourceReport = {
  report_id: string;
  subject: string;
  output_language: string;
  report_type?: string;
  period_start?: string | null;
  period_end?: string | null;
};

type ReportsResponse = {
  status: string;
  reports: SourceReport[];
};


/* =========================================================
   HELPERS
========================================================= */

const REPORT_LIMIT = 100;

const INPUT =
  "w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm";

const BUTTON =
  "rounded-lg border border-slate-200 px-4 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50";

const PRIMARY =
  "rounded-lg bg-emerald-700 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50";

const LAYOUT_LABELS: Record<
  ProductionPageLayout,
  string
> = {
  COVER: "Couverture",
  EXECUTIVE_SUMMARY: "Synthèse exécutive",
  CHART_WITH_ANALYSIS: "Graphique commenté",
  KEY_NUMBERS: "Chiffres clés",
  CASE_STUDY: "Étude de cas",
  COMPARISON: "Comparaison",
  EXPLANATORY: "Explication",
  IMPLICATIONS: "Implications",
  SOURCES: "Sources",
};

function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "Une erreur est survenue.";
}

function displayDate(
  value?: string | null,
): string {
  if (!value) return "";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString("fr-FR");
}

function reportPeriod(
  report: SourceReport,
): string {
  return [
    displayDate(report.period_start),
    displayDate(report.period_end),
  ]
    .filter(Boolean)
    .join(" – ");
}

async function loadReportBatch(
  offset: number,
): Promise<SourceReport[]> {
  const response: ReportsResponse =
    await api.get(
      `/touch/reports?archive=active&limit=${REPORT_LIMIT}&offset=${offset}`,
    );

  return response.reports;
}


/* =========================================================
   PAGE
========================================================= */

export default function ProductionPage() {
  const [reports, setReports] =
    useState<SourceReport[]>([]);

  const [reportOffset, setReportOffset] =
    useState(0);

  const [hasMoreReports, setHasMoreReports] =
    useState(false);

  const [reportSearch, setReportSearch] =
    useState("");

  const [selectedReportIds, setSelectedReportIds] =
    useState<string[]>([]);

  const [productions, setProductions] =
    useState<ProductionSummary[]>([]);

  const [production, setProduction] =
    useState<Production | null>(null);

  const [plan, setPlan] =
    useState<ProductionSavedPlan | null>(null);

  const [versions, setVersions] =
    useState<ProductionPlanVersionSummary[]>([]);

  const [title, setTitle] =
    useState("");

  const [objective, setObjective] =
    useState("");

  const [audience, setAudience] =
    useState("Décideurs médias et marketing");

  const [language, setLanguage] =
    useState<"fr" | "en">("fr");

  const [format, setFormat] =
    useState<ProductionOutputFormat>(
      "AUTONOMOUS_REPORT",
    );

  const [pageCount, setPageCount] =
    useState(12);

  const [loading, setLoading] =
    useState(true);

  const [loadingReports, setLoadingReports] =
    useState(false);

  const [opening, setOpening] =
    useState(false);

  const [creating, setCreating] =
    useState(false);

  const [generating, setGenerating] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const selectionRequestRef = useRef(0);

  const busy =
    loading ||
    opening ||
    creating ||
    generating;


  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [
          firstReports,
          savedProductions,
        ] = await Promise.all([
          loadReportBatch(0),
          listProductions(100),
        ]);

        if (!active) return;

        setReports(firstReports);
        setReportOffset(firstReports.length);

        setHasMoreReports(
          firstReports.length === REPORT_LIMIT,
        );

        setProductions(savedProductions);
      } catch (err) {
        if (active) {
          setError(errorMessage(err));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      active = false;
      selectionRequestRef.current += 1;
    };
  }, []);


  /* =======================================================
     REPORT SELECTION
  ======================================================= */

  function toggleReport(
    reportId: string,
  ) {
    setSelectedReportIds((current) => {
      if (current.includes(reportId)) {
        return current.filter(
          (id) => id !== reportId,
        );
      }

      if (current.length >= 20) {
        return current;
      }

      return [...current, reportId];
    });
  }

  async function loadMoreReports() {
    if (loadingReports) return;

    setLoadingReports(true);
    setError(null);

    try {
      const batch = await loadReportBatch(
        reportOffset,
      );

      setReports((current) => {
        const knownIds = new Set(
          current.map(
            (report) => report.report_id,
          ),
        );

        return [
          ...current,
          ...batch.filter(
            (report) =>
              !knownIds.has(report.report_id),
          ),
        ];
      });

      setReportOffset(
        (current) => current + batch.length,
      );

      setHasMoreReports(
        batch.length === REPORT_LIMIT,
      );
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoadingReports(false);
    }
  }


  /* =======================================================
     OPEN PRODUCTION OR PLAN VERSION
  ======================================================= */

  async function openProduction(
    productionId: string,
  ) {
    const requestId =
      ++selectionRequestRef.current;

    setOpening(true);
    setError(null);
    setProduction(null);
    setPlan(null);
    setVersions([]);

    try {
      const [
        savedProduction,
        history,
      ] = await Promise.all([
        getProduction(productionId),
        listProductionPlans(
          productionId,
          100,
        ),
      ]);

      if (
        requestId !==
        selectionRequestRef.current
      ) {
        return;
      }

      setProduction(savedProduction);
      setVersions(history);

      if (history.length > 0) {
        const savedPlan =
          await getProductionPlan(
            productionId,
            history[0].plan_version,
          );

        if (
          requestId ===
          selectionRequestRef.current
        ) {
          setPlan(savedPlan);
        }
      }
    } catch (err) {
      if (
        requestId ===
        selectionRequestRef.current
      ) {
        setError(errorMessage(err));
      }
    } finally {
      if (
        requestId ===
        selectionRequestRef.current
      ) {
        setOpening(false);
      }
    }
  }

  async function openPlanVersion(
    version: number,
  ) {
    if (!production) return;

    const requestId =
      ++selectionRequestRef.current;

    setOpening(true);
    setError(null);
    setPlan(null);

    try {
      const savedPlan =
        await getProductionPlan(
          production.production_id,
          version,
        );

      if (
        requestId ===
        selectionRequestRef.current
      ) {
        setPlan(savedPlan);
      }
    } catch (err) {
      if (
        requestId ===
        selectionRequestRef.current
      ) {
        setError(errorMessage(err));
      }
    } finally {
      if (
        requestId ===
        selectionRequestRef.current
      ) {
        setOpening(false);
      }
    }
  }


  /* =======================================================
     CREATE
  ======================================================= */

  async function handleCreate() {
    if (
      busy ||
      !title.trim() ||
      selectedReportIds.length === 0
    ) {
      return;
    }

    setCreating(true);
    setError(null);

    try {
      const created =
        await createProduction({
          title: title.trim(),
          report_ids: selectedReportIds,
          objective: objective.trim(),
          target_audience: audience.trim(),
          output_language: language,
          output_format: format,
          target_page_count: pageCount,
        });

      selectionRequestRef.current += 1;

      setProduction(created);
      setPlan(null);
      setVersions([]);

      setProductions((current) => [
        created,
        ...current.filter(
          (item) =>
            item.production_id !==
            created.production_id,
        ),
      ]);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setCreating(false);
    }
  }


  /* =======================================================
     GENERATE
  ======================================================= */

  async function handleGenerate() {
    if (!production || busy) return;

    setGenerating(true);
    setError(null);

    try {
      const savedPlan =
        await generateProductionPlan(
          production.production_id,
        );

      setPlan(savedPlan);

      setVersions((current) => [
        savedPlan,
        ...current.filter(
          (item) =>
            item.plan_id !== savedPlan.plan_id,
        ),
      ]);

      setProduction((current) =>
        current
          ? {
              ...current,
              status: "PLAN_TO_REVIEW",
            }
          : current,
      );

      setProductions((current) =>
        current.map((item) =>
          item.production_id ===
          production.production_id
            ? {
                ...item,
                status: "PLAN_TO_REVIEW",
              }
            : item,
        ),
      );
    } catch (err) {
      setError(
        `${errorMessage(err)} Consultez l’historique en rouvrant la production avant de relancer.`,
      );
    } finally {
      setGenerating(false);
    }
  }


  /* =======================================================
     DERIVED DATA
  ======================================================= */

  const search = reportSearch
    .trim()
    .toLocaleLowerCase();

  const filteredReports = reports.filter(
    (report) =>
      report.subject
        .toLocaleLowerCase()
        .includes(search),
  );

  const counts =
    production?.corpus.counts;

  const evidenceById = new Map(
    production?.corpus.evidence_index.map(
      (reference) => [
        reference.reference_id,
        reference,
      ],
    ) || [],
  );

  const reportsById = new Map(
    production?.corpus.reports.map(
      (report) => [
        report.report_id,
        report,
      ],
    ) || [],
  );

  const canGenerate =
    production?.status ===
      "CORPUS_PREPARED" ||
    production?.status ===
      "PLAN_TO_REVIEW";


  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">
          Productions
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          Créez un document à partir des rapports
          Touch sélectionnés.
        </p>
      </header>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800"
        >
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-slate-500">
          Chargement…
        </p>
      ) : (
        <div className="grid gap-8 xl:grid-cols-[400px_minmax(0,1fr)]">
          <aside className="min-w-0 space-y-8">
            <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-5">
              <h2 className="font-semibold">
                Nouvelle production
              </h2>

              <label className="block space-y-1 text-sm">
                <span>Titre</span>
                <input
                  className={INPUT}
                  value={title}
                  maxLength={250}
                  onChange={(event) =>
                    setTitle(event.target.value)
                  }
                  placeholder="Audio & Podcast — T3 2026"
                />
              </label>

              <label className="block space-y-1 text-sm">
                <span>Objectif</span>
                <textarea
                  className={INPUT}
                  rows={4}
                  value={objective}
                  maxLength={5000}
                  onChange={(event) =>
                    setObjective(
                      event.target.value,
                    )
                  }
                  placeholder="Quelle question doit traiter le document ?"
                />
              </label>

              <label className="block space-y-1 text-sm">
                <span>Public</span>
                <input
                  className={INPUT}
                  value={audience}
                  maxLength={2000}
                  onChange={(event) =>
                    setAudience(
                      event.target.value,
                    )
                  }
                />
              </label>

              <div className="grid grid-cols-2 gap-3">
                <label className="space-y-1 text-sm">
                  <span>Langue</span>
                  <select
                    className={INPUT}
                    value={language}
                    onChange={(event) =>
                      setLanguage(
                        event.target.value as
                          | "fr"
                          | "en",
                      )
                    }
                  >
                    <option value="fr">
                      Français
                    </option>
                    <option value="en">
                      Anglais
                    </option>
                  </select>
                </label>

                <label className="space-y-1 text-sm">
                  <span>Pages</span>
                  <select
                    className={INPUT}
                    value={pageCount}
                    onChange={(event) =>
                      setPageCount(
                        Number(
                          event.target.value,
                        ),
                      )
                    }
                  >
                    {Array.from(
                      { length: 37 },
                      (_, index) => index + 4,
                    ).map((count) => (
                      <option
                        key={count}
                        value={count}
                      >
                        {count}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <label className="block space-y-1 text-sm">
                <span>Format</span>
                <select
                  className={INPUT}
                  value={format}
                  onChange={(event) =>
                    setFormat(
                      event.target.value as
                        ProductionOutputFormat,
                    )
                  }
                >
                  <option value="AUTONOMOUS_REPORT">
                    Rapport autonome
                  </option>
                  <option value="SPEAKER_PRESENTATION">
                    Présentation avec speaker
                  </option>
                </select>
              </label>

              <div className="space-y-3 border-t pt-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium">
                    Rapports Touch
                  </h3>
                  <span className="text-xs text-slate-500">
                    {selectedReportIds.length}/20
                  </span>
                </div>

                <input
                  className={INPUT}
                  value={reportSearch}
                  onChange={(event) =>
                    setReportSearch(
                      event.target.value,
                    )
                  }
                  placeholder="Filtrer les rapports chargés"
                />

                <div className="max-h-80 space-y-2 overflow-y-auto">
                  {filteredReports.map(
                    (report) => {
                      const checked =
                        selectedReportIds.includes(
                          report.report_id,
                        );

                      return (
                        <label
                          key={report.report_id}
                          className="flex gap-3 rounded-lg border border-slate-100 p-3 text-sm"
                        >
                          <input
                            type="checkbox"
                            className="mt-1"
                            checked={checked}
                            disabled={
                              busy ||
                              (
                                !checked &&
                                selectedReportIds.length >=
                                  20
                              )
                            }
                            onChange={() =>
                              toggleReport(
                                report.report_id,
                              )
                            }
                          />

                          <span className="min-w-0">
                            <span className="block font-medium">
                              {report.subject}
                            </span>
                            <span className="mt-1 block text-xs text-slate-500">
                              {[
                                report.output_language.toUpperCase(),
                                reportPeriod(
                                  report,
                                ),
                              ]
                                .filter(Boolean)
                                .join(" · ")}
                            </span>
                          </span>
                        </label>
                      );
                    },
                  )}

                  {filteredReports.length === 0 && (
                    <p className="py-4 text-sm text-slate-500">
                      Aucun rapport dans cette sélection.
                    </p>
                  )}
                </div>

                {hasMoreReports && (
                  <button
                    type="button"
                    className={BUTTON}
                    disabled={
                      loadingReports || busy
                    }
                    onClick={() =>
                      void loadMoreReports()
                    }
                  >
                    {loadingReports
                      ? "Chargement…"
                      : "Charger plus de rapports"}
                  </button>
                )}
              </div>

              <button
                type="button"
                className={`${PRIMARY} w-full`}
                disabled={
                  busy ||
                  !title.trim() ||
                  selectedReportIds.length === 0
                }
                onClick={() =>
                  void handleCreate()
                }
              >
                {creating
                  ? "Préparation du socle…"
                  : "Créer la production"}
              </button>
            </section>

            <section className="space-y-3">
              <h2 className="font-semibold">
                Productions récentes
              </h2>

              {productions.length === 0 && (
                <p className="text-sm text-slate-500">
                  Aucune production enregistrée.
                </p>
              )}

              {productions.map((item) => (
                <button
                  key={item.production_id}
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void openProduction(
                      item.production_id,
                    )
                  }
                  className={`w-full rounded-lg border p-4 text-left disabled:opacity-50 ${
                    production?.production_id ===
                    item.production_id
                      ? "border-emerald-400 bg-emerald-50"
                      : "border-slate-200 bg-white"
                  }`}
                >
                  <span className="block text-sm font-medium">
                    {item.title}
                  </span>

                  <span className="mt-1 block text-xs text-slate-500">
                    {displayDate(
                      item.created_at,
                    )}
                    {" · "}
                    {item.status ===
                    "PLAN_TO_REVIEW"
                      ? "Plan à relire"
                      : "Socle préparé"}
                  </span>
                </button>
              ))}
            </section>
          </aside>

          <main className="min-w-0 space-y-6">
            {opening && (
              <p className="text-sm text-slate-500">
                Chargement de la sélection…
              </p>
            )}

            {!production && !opening && (
              <div className="rounded-xl border border-dashed border-slate-300 p-10 text-sm text-slate-500">
                Créez une production ou ouvrez
                une production enregistrée.
              </div>
            )}

            {production && counts && (
              <>
                <section className="space-y-5 rounded-xl border border-slate-200 bg-white p-6">
                  <div>
                    <h2 className="text-xl font-semibold">
                      {production.title}
                    </h2>
                    <p className="mt-2 text-sm text-slate-500">
                      {production.corpus.request.objective ||
                        "Aucun objectif complémentaire."}
                    </p>
                  </div>

                  <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                    {[
                      [
                        "Rapports",
                        counts.reports,
                      ],
                      [
                        "Contenus uniques",
                        counts.unique_contents,
                      ],
                      [
                        "Notes",
                        counts.notes,
                      ],
                      [
                        "Numbers uniques",
                        counts.unique_number_ids,
                      ],
                    ].map(([label, value]) => (
                      <div key={String(label)}>
                        <dt className="text-xs text-slate-500">
                          {label}
                        </dt>
                        <dd className="mt-1 text-2xl font-semibold text-emerald-700">
                          {value}
                        </dd>
                      </div>
                    ))}
                  </dl>

                  <p className="text-xs text-slate-500">
                    {counts.number_occurrences} occurrences
                    de Numbers dans les rapports.
                    Les données sont conservées
                    dans le socle enregistré.
                  </p>

                  <div className="flex flex-wrap items-center gap-3 border-t pt-4">
                    <button
                      type="button"
                      className={PRIMARY}
                      disabled={
                        busy || !canGenerate
                      }
                      onClick={() =>
                        void handleGenerate()
                      }
                    >
                      {generating
                        ? "Génération du plan…"
                        : versions.length > 0
                          ? "Générer une nouvelle version"
                          : "Générer le plan"}
                    </button>

                    {versions.length > 0 && (
                      <select
                        aria-label="Version du plan"
                        className={`${INPUT} max-w-52`}
                        disabled={busy}
                        value={
                          plan?.plan_version || ""
                        }
                        onChange={(event) =>
                          void openPlanVersion(
                            Number(
                              event.target.value,
                            ),
                          )
                        }
                      >
                        <option
                          value=""
                          disabled
                        >
                          Choisir une version
                        </option>

                        {versions.map(
                          (version) => (
                            <option
                              key={
                                version.plan_id
                              }
                              value={
                                version.plan_version
                              }
                            >
                              Version{" "}
                              {
                                version.plan_version
                              }
                            </option>
                          ),
                        )}
                      </select>
                    )}
                  </div>

                  {generating && (
                    <p
                      role="status"
                      className="text-sm text-slate-500"
                    >
                      La génération peut prendre
                      quelques minutes. Gardez
                      cette page ouverte.
                    </p>
                  )}
                </section>

                {plan && (
                  <section className="space-y-5">
                    <div>
                      <h2 className="text-xl font-semibold">
                        {plan.snapshot.plan.title}
                      </h2>
                      <p className="mt-2 text-sm leading-relaxed text-slate-600">
                        {
                          plan.snapshot.plan
                            .editorial_angle
                        }
                      </p>
                      <p className="mt-2 text-xs text-emerald-700">
                        Version {plan.plan_version}
                        {" · "}
                        Plan à relire
                      </p>
                    </div>

                    {plan.snapshot.plan.pages.map(
                      (page, index) => (
                        <article
                          key={page.page_id}
                          className="space-y-4 rounded-xl border border-slate-200 bg-white p-6"
                        >
                          <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
                            Page {index + 1}
                            {" · "}
                            {
                              LAYOUT_LABELS[
                                page.layout
                              ]
                            }
                          </p>

                          <h3 className="text-lg font-semibold">
                            {page.title}
                          </h3>

                          <p className="text-sm leading-relaxed">
                            {page.key_message}
                          </p>

                          {page.explanation_outline.length >
                            0 && (
                            <ul className="list-disc space-y-2 pl-5 text-sm text-slate-600">
                              {page.explanation_outline.map(
                                (item, itemIndex) => (
                                  <li
                                    key={
                                      itemIndex
                                    }
                                  >
                                    {item}
                                  </li>
                                ),
                              )}
                            </ul>
                          )}

                          {page.visual_intent && (
                            <div className="border-t pt-3 text-sm">
                              <p className="font-medium">
                                Représentation prévue
                              </p>
                              <p className="mt-1 text-slate-600">
                                {page.visual_intent}
                              </p>
                            </div>
                          )}

                          {page.cautions.length >
                            0 && (
                            <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
                              <p className="font-medium">
                                Points d’attention
                              </p>
                              <ul className="mt-2 list-disc space-y-1 pl-5">
                                {page.cautions.map(
                                  (caution, cautionIndex) => (
                                    <li
                                      key={
                                        cautionIndex
                                      }
                                    >
                                      {caution}
                                    </li>
                                  ),
                                )}
                              </ul>
                            </div>
                          )}

                          <details className="border-t pt-3 text-sm">
                            <summary className="cursor-pointer text-slate-500">
                              {
                                page
                                  .evidence_reference_ids
                                  .length
                              } preuves
                              {" · "}
                              {
                                page
                                  .number_reference_ids
                                  .length
                              } Numbers
                            </summary>

                            <ul className="mt-3 space-y-3">
                              {page.evidence_reference_ids.map(
                                (referenceId) => {
                                  const reference =
                                    evidenceById.get(
                                      referenceId,
                                    );

                                  if (!reference) {
                                    return (
                                      <li
                                        key={
                                          referenceId
                                        }
                                        className="text-red-700"
                                      >
                                        Référence
                                        introuvable.
                                      </li>
                                    );
                                  }

                                  const sourceReport =
                                    reportsById.get(
                                      reference.report_id,
                                    );

                                  const subject =
                                    sourceReport
                                      ?.payload
                                      .subject;

                                  return (
                                    <li
                                      key={
                                        referenceId
                                      }
                                      className="text-slate-600"
                                    >
                                      <span className="font-medium">
                                        {
                                          reference.kind
                                        }
                                      </span>
                                      {" · "}
                                      {
                                        reference.local_id
                                      }
                                      <span className="block text-xs text-slate-400">
                                        {typeof subject ===
                                        "string"
                                          ? subject
                                          : reference.report_id}
                                        {" · "}
                                        Rapport v
                                        {
                                          reference.report_version
                                        }
                                      </span>
                                    </li>
                                  );
                                },
                              )}
                            </ul>
                          </details>
                        </article>
                      ),
                    )}
                  </section>
                )}
              </>
            )}
          </main>
        </div>
      )}
    </div>
  );
}
