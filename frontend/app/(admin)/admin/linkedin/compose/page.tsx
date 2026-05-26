"use client";

import { useEffect, useMemo, useState } from "react";
import NewsletterSelector from "@/components/newsletter/NewsletterSelectors";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL || "https://ratecard.fr";

/* =========================================================
   UTILS — LINKEDIN FORMAT
========================================================= */

function bold(text: string) {
  const map: Record<string, string> = {
    a: "𝗮", b: "𝗯", c: "𝗰", d: "𝗱", e: "𝗲",
    f: "𝗳", g: "𝗴", h: "𝗵", i: "𝗶", j: "𝗷",
    k: "𝗸", l: "𝗹", m: "𝗺", n: "𝗻", o: "𝗼",
    p: "𝗽", q: "𝗾", r: "𝗿", s: "𝘀", t: "𝘁",
    u: "𝘂", v: "𝘃", w: "𝘄", x: "𝘅", y: "𝘆", z: "𝘇",
    A: "𝗔", B: "𝗕", C: "𝗖", D: "𝗗", E: "𝗘",
    F: "𝗙", G: "𝗚", H: "𝗛", I: "𝗜", J: "𝗝",
    K: "𝗞", L: "𝗟", M: "𝗠", N: "𝗡", O: "𝗢",
    P: "𝗣", Q: "𝗤", R: "𝗥", S: "𝗦", T: "𝗧",
    U: "𝗨", V: "𝗩", W: "𝗪", X: "𝗫", Y: "𝗬", Z: "𝗭",
  };

  return text
    .split("")
    .map((c) => map[c] || c)
    .join("");
}

/* =========================================================
   TYPES
========================================================= */

export type NewsItem = {
  id: string;
  title: string;
  excerpt?: string | null;
};

export type AnalysisItem = {
  id: string;
  title: string;
  excerpt?: string | null;
};

/* =========================================================
   PAGE
========================================================= */

export default function LinkedInComposePage() {
  const [mode, setMode] = useState<"list" | "ai">("list");

  const [news, setNews] = useState<NewsItem[]>([]);
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);

  const [selectedNewsIds, setSelectedNewsIds] = useState<string[]>([]);
  const [selectedAnalysisIds, setSelectedAnalysisIds] = useState<string[]>([]);

  const [postText, setPostText] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  /* -----------------------------------------------------
     Fetch sources
  ----------------------------------------------------- */
  useEffect(() => {
    fetch(`${API_BASE}/news/list`, { cache: "no-store" })
      .then((r) => r.json())
      .then((json) => {
        const mapped = (json.news || []).map((n: any) => ({
          id: n.ID_NEWS,
          title: n.TITLE,
          excerpt: n.EXCERPT ?? null,
        }));
        setNews(mapped);
      });

    fetch(`${API_BASE}/public/analysis/list`, { cache: "no-store" })
      .then((r) => r.json())
      .then((json) => {
        const mapped = (json.items || []).map((a: any) => ({
          id: a.id,
          title: a.title,
          excerpt: a.excerpt ?? null,
        }));
        setAnalyses(mapped);
      });
  }, []);

  /* -----------------------------------------------------
     Selected objects
  ----------------------------------------------------- */
  const selectedNews = useMemo(
    () => news.filter((n) => selectedNewsIds.includes(n.id)),
    [news, selectedNewsIds]
  );

  const selectedAnalyses = useMemo(
    () => analyses.filter((a) => selectedAnalysisIds.includes(a.id)),
    [analyses, selectedAnalysisIds]
  );

  /* -----------------------------------------------------
     GENERATION — LIST MODE (ENRICHI + FORMAT LINKEDIN)
  ----------------------------------------------------- */
  function generateListPost() {
    const lines: string[] = [];

    if (selectedNews.length > 0) {
      selectedNews.forEach((n) => {
        lines.push(
          `• ${bold(n.title)}\n` +
          (n.excerpt ? `  ${n.excerpt}\n` : "") +
          `  ${SITE_URL}/news?news_id=${n.id}\n`
        );
      });
    }

    if (selectedAnalyses.length > 0) {
      selectedAnalyses.forEach((a) => {
        lines.push(
          `• ${bold(a.title)}\n` +
          (a.excerpt ? `  ${a.excerpt}\n` : "") +
          `  ${SITE_URL}/analysis?analysis_id=${a.id}\n`
        );
      });
    }

    const intro =
      `${bold("Plusieurs annonces et analyses à retenir ces derniers jours")} 👇\n\n`;

    setPostText(intro + lines.join("\n"));
  }

  /* -----------------------------------------------------
     GENERATION — AI MODE
  ----------------------------------------------------- */
  async function generateAIPost() {
    setIsGenerating(true);

    const sources = [
      ...selectedNews.map((n) => ({
        type: "news",
        title: n.title,
        excerpt: n.excerpt,
      })),
      ...selectedAnalyses.map((a) => ({
        type: "analysis",
        title: a.title,
        excerpt: a.excerpt,
      })),
    ];

    try {
      const res = await fetch(
        `${API_BASE}/public/linkedin/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sources }),
        }
      );

      const json = await res.json();

      if (json?.text) {
        setPostText(json.text);
      }
    } catch (e) {
      console.error("Erreur génération IA LinkedIn", e);
    } finally {
      setIsGenerating(false);
    }
  }

  /* -----------------------------------------------------
     COPY
  ----------------------------------------------------- */
  function copyPost() {
    navigator.clipboard.writeText(postText);
    alert("Post LinkedIn copié. Prêt à être publié.");
  }

  return (
    <div className="space-y-10">

      {/* HEADER */}
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">
          Créer un post LinkedIn
        </h1>

        <div className="flex gap-2">
          <button
            onClick={() => setMode("list")}
            className={`px-3 py-1.5 text-xs rounded-md border ${
              mode === "list"
                ? "bg-gray-900 text-white"
                : "bg-white text-gray-700"
            }`}
          >
            Liste
          </button>
          <button
            onClick={() => setMode("ai")}
            className={`px-3 py-1.5 text-xs rounded-md border ${
              mode === "ai"
                ? "bg-gray-900 text-white"
                : "bg-white text-gray-700"
            }`}
          >
            Synthèse IA
          </button>
        </div>
      </div>

      {/* MAIN */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">

        {/* LEFT — SELECTION */}
        <div className="space-y-6">
          <NewsletterSelector
            title="News"
            items={news}
            selectedIds={selectedNewsIds}
            onChange={setSelectedNewsIds}
            labelKey="title"
          />

          <NewsletterSelector
            title="Analyses"
            items={analyses}
            selectedIds={selectedAnalysisIds}
            onChange={setSelectedAnalysisIds}
            labelKey="title"
          />
        </div>

        {/* RIGHT — TEXT */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">
              Texte du post
            </h2>

            {mode === "list" && (
              <button
                onClick={generateListPost}
                className="px-3 py-1.5 rounded-md bg-gray-900 text-white text-xs"
              >
                Générer automatiquement
              </button>
            )}

            {mode === "ai" && (
              <button
                onClick={generateAIPost}
                disabled={isGenerating}
                className="px-3 py-1.5 rounded-md bg-ratecard-blue text-white text-xs disabled:opacity-60"
              >
                {isGenerating
                  ? "Génération en cours…"
                  : "Générer avec l’IA"}
              </button>
            )}
          </div>

          <textarea
            value={postText}
            onChange={(e) => setPostText(e.target.value)}
            placeholder={
              mode === "list"
                ? "Le texte du post sera généré automatiquement…"
                : "Le texte sera généré par l’IA…"
            }
            className="w-full min-h-[380px] rounded-lg border border-gray-300 p-3 text-sm"
          />

          <div className="flex justify-between items-center text-xs text-gray-500">
            <span>{postText.length} caractères</span>

            <button
              onClick={copyPost}
              className="px-3 py-1.5 rounded-md bg-ratecard-blue text-white"
            >
              Copier le post
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
