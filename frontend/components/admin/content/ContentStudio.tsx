"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

import StepSource from "@/components/admin/content/steps/StepSource";
import StepSummary from "@/components/admin/content/steps/StepSummary";
import StepValidation from "@/components/admin/content/steps/StepValidation";
import StepPreview from "@/components/admin/content/steps/StepPreview";

type Mode = "create" | "edit" | "validate";

type Props = {
  mode: Mode;
  contentId?: string;
};

export default function ContentStudio({ mode, contentId }: Props) {

  const [internalContentId, setInternalContentId] =
    useState<string | null>(contentId || null);

  const [previewOpen, setPreviewOpen] = useState(false);

  // =========================
  // 🔥 CONTENT TYPE
  // =========================

  const [contentType, setContentType] =
    useState<"ANALYSIS" | "NEWS">("ANALYSIS");

  // 🔥 NEW
  const [primaryCompanyId, setPrimaryCompanyId] =
    useState<string | null>(null);

  // 🔥 NEW
  const [allCompanies, setAllCompanies] =
    useState<any[]>([]);

  // =========================
  // SOURCE
  // =========================

  const [sourceId, setSourceId] = useState<string | null>(null);
  const [sourceText, setSourceText] = useState("");
  const [sourcePublishedAt, setSourcePublishedAt] = useState<string | null>(null);

  // =========================
  // LLM RAW (STRING LISTS)
  // =========================

  const [topicsRaw, setTopicsRaw] = useState<string[]>([]);
  const [acteursRaw, setActeursRaw] = useState<string[]>([]);
  const [conceptsRaw, setConceptsRaw] = useState<string[]>([]);
  const [solutionsRaw, setSolutionsRaw] = useState<string[]>([]);

  // =========================
  // STRUCTURANT (IDS)
  // =========================

  const [topics, setTopics] = useState<string[]>([]);
  const [companies, setCompanies] = useState<string[]>([]);
  const [concepts, setConcepts] = useState<string[]>([]);
  const [solutions, setSolutions] = useState<string[]>([]);

  // =========================
  // EDITORIAL
  // =========================

  const [title, setTitle] = useState("");
  const [title_en, setTitle_en] = useState("");

  const [excerpt, setExcerpt] = useState("");
  const [excerpt_en, setExcerpt_en] = useState("");

  const [contentBody, setContentBody] = useState("");

  const [chiffres, setChiffres] = useState<string[]>([]);

  const [mecanique, setMecanique] = useState("");
  const [enjeu, setEnjeu] = useState("");
  const [friction, setFriction] = useState("");
  const [signal, setSignal] = useState("");

  // =========================
  // STATUS / PUBLISH
  // =========================

  const [status, setStatus] = useState("DRAFT");

  const [publishing, setPublishing] =
    useState(false);

  const [publishMode, setPublishMode] =
    useState<"NOW" | "SCHEDULE">("NOW");

  const [publishAt, setPublishAt] = useState("");

  // ============================================================
  // LOAD COMPANIES
  // ============================================================

  useEffect(() => {

    async function loadCompanies() {

      try {

        const res = await api.get("/company/list");

        setAllCompanies(
          res.items || res.companies || []
        );

      } catch (e) {

        console.error(
          "Erreur chargement companies",
          e
        );

      }
    }

    loadCompanies();

  }, []);

  // ============================================================
  // LOAD EXISTING CONTENT
  // ============================================================

  useEffect(() => {

    if (!contentId) return;

    async function load() {

      const res = await api.get(
        `/content/${contentId}`
      );

      const c = res.content;

      setContentType(
        c.content_type || "ANALYSIS"
      );

      // 🔥 NEW
      setPrimaryCompanyId(
        c.id_primary_company || null
      );

      setTitle(c.title || "");
      setTitle_en(c.title_en || "");

      setExcerpt(c.excerpt || "");
      setExcerpt_en(c.excerpt_en || "");

      setContentBody(c.content_body || "");

      setChiffres(c.chiffres || []);

      setActeursRaw(c.acteurs_cites || []);

      setTopicsRaw(c.topics_llm || []);

      setConceptsRaw(c.concepts_llm || []);

      setSolutionsRaw(c.solutions_llm || []);

      setMecanique(
        c.mecanique_expliquee || ""
      );

      setEnjeu(
        c.enjeu_strategique || ""
      );

      setFriction(
        c.point_de_friction || ""
      );

      setSignal(
        c.signal_analytique || ""
      );

      setSourcePublishedAt(
        c.source_published_at || null
      );

      // STRUCTURED IDS

      setTopics(
        (c.topics || []).map(
          (x: any) => x.id_topic
        )
      );

      setCompanies(
        (c.companies || []).map(
          (x: any) => x.id_company
        )
      );

      setSolutions(
        (c.solutions || []).map(
          (x: any) => x.id_solution
        )
      );

      setConcepts(
        (c.concepts || []).map(
          (x: any) => x.id_concept
        )
      );

      setStatus(
        c.status || "DRAFT"
      );
    }

    load();

  }, [contentId]);

  // ============================================================
  // SAVE EDITORIAL
  // ============================================================

  async function saveEditorial() {

    const payload = {

      content_type: contentType,

      // 🔥 NEW
      id_primary_company: primaryCompanyId,

      source_id: sourceId,

      source_text: sourceText,

      source_published_at:
        sourcePublishedAt,

      title,
      title_en,

      excerpt,
      excerpt_en,

      content_body: contentBody,

      chiffres,

      acteurs_cites: acteursRaw,

      topics_llm: topicsRaw,

      concepts_llm: conceptsRaw,

      solutions_llm: solutionsRaw,

      mecanique_expliquee: mecanique,

      enjeu_strategique: enjeu,

      point_de_friction: friction,

      signal_analytique: signal,
    };

    if (!internalContentId) {

      const res = await api.post(
        "/content/create",
        payload
      );

      setInternalContentId(
        res.id_content
      );

    } else {

      await api.put(
        `/content/update/${internalContentId}`,
        payload
      );

    }

    alert("Éditorial sauvegardé");
  }

  // ============================================================
  // SAVE STRUCTURANT
  // ============================================================

  async function saveValidation() {

    if (!internalContentId) return;

    await api.put(
      `/content/update/${internalContentId}`,
      {

        content_type: contentType,

        // 🔥 NEW
        id_primary_company:
          primaryCompanyId,

        topics,
        companies,
        concepts,
        solutions,
      }
    );

    alert("Validation sauvegardée");
  }

  // ============================================================
  // PUBLISH
  // ============================================================

  async function publishContent() {

    if (!internalContentId) return;

    setPublishing(true);

    try {

      const res = await api.post(
        `/content/publish/${internalContentId}`,
        {
          publish_at:
            publishMode === "NOW"
              ? null
              : new Date(
                  publishAt
                ).toISOString(),
        }
      );

      setStatus(
        res.published_status
      );

    } catch (e) {

      console.error(e);

      alert("Erreur publication");

    }

    setPublishing(false);
  }

  // ============================================================
  // RENDER
  // ============================================================

  return (

    <div className="grid grid-cols-3 gap-8">

      {/* LEFT */}

      <div className="col-span-2 space-y-8">

        <div className="bg-white border rounded p-4">

          <div className="text-sm font-medium mb-3">
            Type de contenu
          </div>

          <div className="flex gap-6">

            <label className="flex items-center gap-2 text-sm">

              <input
                type="radio"
                checked={
                  contentType === "ANALYSIS"
                }
                onChange={() =>
                  setContentType("ANALYSIS")
                }
              />

              Analysis

            </label>

            <label className="flex items-center gap-2 text-sm">

              <input
                type="radio"
                checked={
                  contentType === "NEWS"
                }
                onChange={() =>
                  setContentType("NEWS")
                }
              />

              News

            </label>

          </div>

          {/* 🔥 NEW */}

          <div className="mt-4">

            <label className="block text-sm font-medium mb-2">
              Primary company
            </label>

            <select
              value={primaryCompanyId || ""}
              onChange={(e) =>
                setPrimaryCompanyId(
                  e.target.value || null
                )
              }
              className="border rounded px-3 py-2 w-full text-sm"
            >

              <option value="">
                Aucune
              </option>

              {allCompanies.map((c) => (

                <option
                  key={c.id_company}
                  value={c.id_company}
                >
                  {c.name}
                </option>

              ))}

            </select>

          </div>

        </div>

        {!internalContentId && (

          <StepSource
            contentType={contentType}
            primaryCompanyId={primaryCompanyId}

            onCreate={({
              source_id,
              text,
              date_source
            }) => {

              setSourceId(source_id);

              setSourceText(text);

              setSourcePublishedAt(
                date_source || null
              );
            }}
          />

        )}

        <div className="bg-white border rounded p-4 space-y-4">

          <div>

            <label className="block text-sm font-medium mb-2">
              Title
            </label>

            <input
              type="text"
              value={title}
              onChange={(e) =>
                setTitle(e.target.value)
              }
              className="border rounded px-3 py-2 w-full text-sm"
            />

          </div>

          <div>

            <label className="block text-sm font-medium mb-2">
              Title EN
            </label>

            <input
              type="text"
              value={title_en}
              onChange={(e) =>
                setTitle_en(e.target.value)
              }
              className="border rounded px-3 py-2 w-full text-sm"
            />

          </div>

          <div>

            <label className="block text-sm font-medium mb-2">
              Source publication date
            </label>

            <input
              type="date"
              value={
                sourcePublishedAt
                  ? sourcePublishedAt.slice(0, 10)
                  : ""
              }
              onChange={(e) =>
                setSourcePublishedAt(
                  e.target.value || null
                )
              }
              className="border rounded px-3 py-2 w-full text-sm"
            />

          </div>

        </div>

        <StepSummary

          sourceId={sourceId}

          sourceText={sourceText}

          contentType={contentType}

          title={title}
          title_en={title_en}

          excerpt={excerpt}
          excerpt_en={excerpt_en}

          contentBody={contentBody}

          chiffres={chiffres}

          acteurs={acteursRaw}

          concepts={conceptsRaw}

          solutions={solutionsRaw}

          topics={topicsRaw}

          mecanique={mecanique}

          enjeu={enjeu}

          friction={friction}

          signal={signal}

          onChange={(d) => {

            if (d.title !== undefined) {
              setTitle(d.title);
            }

            if (d.title_en !== undefined) {
              setTitle_en(d.title_en);
            }

            if (d.excerpt !== undefined) {
              setExcerpt(d.excerpt);
            }

            if (d.excerpt_en !== undefined) {
              setExcerpt_en(d.excerpt_en);
            }

            if (d.contentBody !== undefined) {
              setContentBody(d.contentBody);
            }

            if (d.chiffres !== undefined) {
              setChiffres(d.chiffres);
            }

            if (d.acteurs !== undefined) {
              setActeursRaw(d.acteurs);
            }

            if (d.concepts !== undefined) {
              setConceptsRaw(d.concepts);
            }

            if (d.solutions !== undefined) {
              setSolutionsRaw(d.solutions);
            }

            if (d.topics !== undefined) {

              setTopicsRaw(d.topics);

              setTopics(d.topics);

            }

            if (d.mecanique !== undefined) {
              setMecanique(d.mecanique);
            }

            if (d.enjeu !== undefined) {
              setEnjeu(d.enjeu);
            }

            if (d.friction !== undefined) {
              setFriction(d.friction);
            }

            if (d.signal !== undefined) {
              setSignal(d.signal);
            }
          }}

          onNext={saveEditorial}
        />

        {internalContentId && (

          <button
            onClick={() =>
              setPreviewOpen(true)
            }
            className="px-4 py-2 bg-gray-800 text-white rounded text-sm"
          >
            Aperçu
          </button>

        )}

      </div>

      {/* RIGHT */}

      <div className="col-span-1">

        <div className="sticky top-6 space-y-6">

          <div className="bg-white border rounded p-5 shadow-sm space-y-6">

            <StepValidation

              topicsRaw={topicsRaw}

              acteursRaw={acteursRaw}

              conceptsRaw={conceptsRaw}

              solutionsRaw={solutionsRaw}

              topics={topics}

              companies={companies}

              concepts={concepts}

              solutions={solutions}

              primaryCompanyId={primaryCompanyId}

              onPrimaryCompanyChange={
                setPrimaryCompanyId
              }

              onChange={(d) => {

                if (d.topics !== undefined) {
                  setTopics(d.topics);
                }

                if (d.companies !== undefined) {
                  setCompanies(d.companies);
                }

                if (d.concepts !== undefined) {
                  setConcepts(d.concepts);
                }

                if (d.solutions !== undefined) {
                  setSolutions(d.solutions);
                }
              }}

              onSave={saveValidation}
            />

            <div className="border-t pt-4 space-y-4">

              <div className="text-sm">
                Statut :
                {" "}
                <strong>{status}</strong>
              </div>

              <div className="space-y-2 text-sm">

                <label className="flex gap-2">

                  <input
                    type="radio"
                    checked={
                      publishMode === "NOW"
                    }
                    onChange={() =>
                      setPublishMode("NOW")
                    }
                  />

                  Publier maintenant

                </label>

                <label className="flex gap-2">

                  <input
                    type="radio"
                    checked={
                      publishMode === "SCHEDULE"
                    }
                    onChange={() =>
                      setPublishMode("SCHEDULE")
                    }
                  />

                  Planifier

                </label>

              </div>

              {publishMode === "SCHEDULE" && (

                <input
                  type="datetime-local"
                  value={publishAt}
                  onChange={(e) =>
                    setPublishAt(
                      e.target.value
                    )
                  }
                  className="border rounded p-2 w-full text-sm"
                />

              )}

              <button
                onClick={publishContent}
                disabled={publishing}
                className="w-full px-4 py-2 bg-green-600 text-white rounded text-sm"
              >
                {publishing
                  ? "Publication..."
                  : "Publier"}
              </button>

            </div>

          </div>

        </div>

      </div>

      {/* PREVIEW */}

      {previewOpen && internalContentId && (

        <StepPreview
          contentId={internalContentId}
          onClose={() =>
            setPreviewOpen(false)
          }
        />

      )}

    </div>
  );
}
