"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import SearchableMultiSelect, {
  SelectOption,
} from "@/components/ui/SearchableMultiSelect";

import DigestHeaderConfig from "@/components/delivery/core/DeliveryHeaderConfig";

import type { HeaderConfig } from "@/types/newsletter";

export default function AdminDigestTemplateCreatePage() {
  const [name, setName] = useState("");

  const [topics, setTopics] = useState<SelectOption[]>([]);
  const [companies, setCompanies] = useState<SelectOption[]>([]);
  const [types, setTypes] = useState<SelectOption[]>([]);

  const [topicOptions, setTopicOptions] = useState<SelectOption[]>([]);
  const [companyOptions, setCompanyOptions] = useState<SelectOption[]>([]);
  const [typeOptions, setTypeOptions] = useState<SelectOption[]>([]);

  /* =========================================================
     HEADER CONFIG (CLONE DIGEST PAGE)
  ========================================================= */

  const [headerConfig, setHeaderConfig] = useState<HeaderConfig>({
    title: "Newsletter Ratecard",
    subtitle: "",
    period: "",
    headerCompany: undefined,
    topBarEnabled: true,
    topBarColor: "#84CC16",
    periodColor: "#84CC16",
    introHtml: "",
  });

  const [introText, setIntroText] = useState("");

  /* =========================================================
     BLOCK CONFIG
  ========================================================= */

  const [limitNews, setLimitNews] = useState(10);
  const [limitBreves, setLimitBreves] = useState(5);
  const [limitAnalyses, setLimitAnalyses] = useState(0);

  const [period, setPeriod] = useState<"last_month" | "30d" | "7d">("last_month");

  const [loading, setLoading] = useState(false);

  /* =========================================================
     LOAD REFERENTIALS
  ========================================================= */

  useEffect(() => {
    async function load() {
      try {
        const t = await api.get("/topic/list");
        const c = await api.get("/company/list");
        const nt = await api.get("/news/types");

        const topicsRaw =
          Array.isArray(t)
            ? t
            : t?.result?.topics || t?.topics || t?.result || [];

        const companiesRaw =
          Array.isArray(c)
            ? c
            : c?.result?.companies || c?.companies || c?.result || [];

        const typesRaw =
          Array.isArray(nt)
            ? nt
            : nt?.result?.types || nt?.types || nt?.result || [];

        setTopicOptions(
          topicsRaw.map((x: any) => ({
            id: x.ID_TOPIC ?? x.id_topic ?? x.id,
            label: x.LABEL ?? x.label ?? x.name,
          }))
        );

        setCompanyOptions(
          companiesRaw.map((x: any) => ({
            id: x.ID_COMPANY ?? x.id_company ?? x.id,
            label: x.NAME ?? x.name,
          }))
        );

        setTypeOptions(
          typesRaw.map((x: any) => ({
            id: x.code || x.CODE || x.news_type || x.TYPE,
            label: x.label || x.LABEL,
          }))
        );

      } catch (e) {
        console.error("Erreur load référentiels", e);
      }
    }

    load();
  }, []);

  /* =========================================================
     SAVE TEMPLATE
  ========================================================= */

  async function handleCreate() {
    setLoading(true);

    try {
      await api.post("/admin/digest/template", {
        name,

        header_config: headerConfig, // 🔥 FULL CONFIG
        intro_text: introText,

        // 🔥 BLOCKS STRUCTURÉS
        blocks: {
          news: {
            topics: topics.map((t) => t.id),
            companies: companies.map((c) => c.id),
            news_types: types.map((t) => t.id),
            limit: limitNews,
            period,
          },
          breves: {
            topics: topics.map((t) => t.id),
            companies: companies.map((c) => c.id),
            news_types: types.map((t) => t.id),
            limit: limitBreves,
            period,
          },
          analyses: {
            topics: topics.map((t) => t.id),
            companies: companies.map((c) => c.id),
            news_types: types.map((t) => t.id),
            limit: limitAnalyses, // 🔥 0 = OFF
            period,
          },
        },

        editorial_order: [],
      });

      alert("Template créé");

    } catch (e) {
      console.error(e);
      alert("Erreur");
    } finally {
      setLoading(false);
    }
  }

  /* =========================================================
     UI
  ========================================================= */

  return (
    <div className="max-w-4xl space-y-6">

      <h1 className="text-lg font-semibold">
        Nouveau template
      </h1>

      <input
        className="w-full border p-2 rounded"
        placeholder="Nom du template"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />

      {/* 🔥 HEADER (CLONE DIGEST) */}
      <DigestHeaderConfig
        headerConfig={headerConfig}
        setHeaderConfig={setHeaderConfig}
        introText={introText}
        setIntroText={setIntroText}
      />

      {/* 🔥 FILTERS */}
      <SearchableMultiSelect
        label="Topics"
        options={topicOptions}
        values={topics}
        onChange={setTopics}
      />

      <SearchableMultiSelect
        label="Sociétés"
        options={companyOptions}
        values={companies}
        onChange={setCompanies}
      />

      <SearchableMultiSelect
        label="Types"
        options={typeOptions}
        values={types}
        onChange={setTypes}
      />

      {/* 🔥 LIMITS PAR BLOC */}
      <div className="grid grid-cols-3 gap-4">

        <div>
          <label className="text-xs">News</label>
          <input
            type="number"
            value={limitNews}
            onChange={(e) => setLimitNews(Number(e.target.value))}
            className="w-full border p-2 rounded"
          />
        </div>

        <div>
          <label className="text-xs">Brèves</label>
          <input
            type="number"
            value={limitBreves}
            onChange={(e) => setLimitBreves(Number(e.target.value))}
            className="w-full border p-2 rounded"
          />
        </div>

        <div>
          <label className="text-xs">Analyses</label>
          <input
            type="number"
            value={limitAnalyses}
            onChange={(e) => setLimitAnalyses(Number(e.target.value))}
            className="w-full border p-2 rounded"
          />
        </div>

      </div>

      {/* 🔥 PERIOD */}
      <div className="flex gap-2">
        {[
          { key: "last_month", label: "Mois précédent" },
          { key: "30d", label: "30 jours" },
          { key: "7d", label: "7 jours" },
        ].map((p) => (
          <button
            key={p.key}
            onClick={() => setPeriod(p.key as any)}
            className={`
              px-3 py-2 text-xs rounded
              ${
                period === p.key
                  ? "bg-black text-white"
                  : "bg-gray-100 text-gray-700"
              }
            `}
          >
            {p.label}
          </button>
        ))}
      </div>

      <button
        onClick={handleCreate}
        disabled={loading}
        className="bg-black text-white px-4 py-2 rounded"
      >
        Créer
      </button>

    </div>
  );
}
