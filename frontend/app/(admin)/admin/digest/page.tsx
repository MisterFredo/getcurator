"use client";

import { useMemo, useState, useEffect } from "react";

import DeliveryHeaderConfig from "@/components/delivery/DeliveryHeaderConfig";
import DeliveryPreviewPanel from "@/components/delivery/DeliveryPreviewPanel";

import DigestEngine from "@/components/digest/DigestEngine";
import DigestSelectors from "@/components/digest/DigestSelectors";
import DigestEditorialFlow from "@/components/digest/DigestEditorialFlow";

import NewsletterTopicStats from "@/components/newsletter/NewsletterTopicStats";

import { api } from "@/lib/api";

import type {
  NewsletterNewsItem,
  NewsletterAnalysisItem,
  NewsletterNumberItem,
  HeaderConfig,
  TopicStat,
} from "@/types/newsletter";

import type {
  SelectOption,
} from "@/components/ui/SearchableMultiSelect";

/* ========================================================= */

type EditorialItem = {
  id: string;
  type: "news" | "breve" | "analysis" | "number";
};

/* ========================================================= */

export default function DigestPage() {

  const [loading, setLoading] = useState(false);

  const [isRunMode, setIsRunMode] = useState(false);

  const [news, setNews] = useState<
    NewsletterNewsItem[]
  >([]);

  const [breves, setBreves] = useState<
    NewsletterNewsItem[]
  >([]);

  const [analyses, setAnalyses] = useState<
    NewsletterAnalysisItem[]
  >([]);

  const [numbers, setNumbers] = useState<
    NewsletterNumberItem[]
  >([]);

  const [selectedTopics, setSelectedTopics] = useState<
    SelectOption[]
  >([]);

  const [selectedCompanies, setSelectedCompanies] = useState<
    SelectOption[]
  >([]);

  const [selectedTypes, setSelectedTypes] = useState<
    SelectOption[]
  >([]);

  /* =========================================================
     STORE GLOBAL DES ITEMS
  ========================================================= */

  const [selectedItemsMap, setSelectedItemsMap] = useState<{
    [id: string]: any;
  }>({});

  function storeItems(items: any[]) {

    setSelectedItemsMap((prev) => {

      const next = {
        ...prev,
      };

      items.forEach((i) => {

        if (i?.id) {
          next[i.id] = i;
        }

      });

      return next;
    });
  }

  /* =========================================================
     HEADER CONFIG
  ========================================================= */

  const [headerConfig, setHeaderConfig] = useState<HeaderConfig>({
    title: "Newsletter Ratecard",
    subtitle: "",
    period: "",
    headerCompany: undefined,
    showTopicStats: false,
    topBarEnabled: true,
    topBarColor: "#84CC16",
    periodColor: "#84CC16",
    introHtml: "",
  });

  const [introText, setIntroText] = useState("");

  /* =========================================================
     EDITORIAL FLOW
  ========================================================= */

  const [editorialOrder, setEditorialOrder] = useState<
    EditorialItem[]
  >([]);

  /* =========================================================
     TOPIC STATS
  ========================================================= */

  const [topicStats, setTopicStats] = useState<
    TopicStat[]
  >([]);

  /* =========================================================
     LOAD RUN (MODE PRODUCTION)
  ========================================================= */

  async function loadRun(id: string) {

    setLoading(true);

    try {

      const res = await api.get(
        `/admin/digest/run/${id}`
      );

      const run = res.run;

      const data = run.data || {};

      setNews(data.news || []);
      setBreves(data.breves || []);
      setAnalyses(data.analyses || []);
      setNumbers(data.numbers || []);

      storeItems([
        ...(data.news || []),
        ...(data.breves || []),
        ...(data.analyses || []),
        ...(data.numbers || []),
      ]);

      setEditorialOrder(
        run.editorial_order || []
      );

      setHeaderConfig(
        run.header_config || {}
      );

      setIntroText(
        run.intro_text || ""
      );

    } catch (e) {

      console.error(
        "Erreur load run",
        e
      );

    } finally {

      setLoading(false);

    }
  }

  /* =========================================================
     DETECT MODE (URL)
  ========================================================= */

  useEffect(() => {

    const params = new URLSearchParams(
      window.location.search
    );

    const runId = params.get("run");

    if (!runId) return;

    setIsRunMode(true);

    loadRun(runId);

  }, []);

  /* =========================================================
     LOAD STATS
  ========================================================= */

  useEffect(() => {

    async function loadStats() {

      try {

        const res = await api.get(
          "/news/breves/stats"
        );

        const data = res.result || res;

        const topics: TopicStat[] = (
          data.topics_stats || []
        )
          .map((t: any) => ({
            label: t.label,
            last_30_days:
              t.last_30_days ?? 0,
            total:
              t.total ?? 0,
          }))
          .sort(
            (a, b) =>
              b.last_30_days -
              a.last_30_days
          );

        setTopicStats(topics);

      } catch (e) {

        console.error(
          "Erreur chargement baromètre",
          e
        );

      }
    }

    loadStats();

  }, []);

  /* =========================================================
     SEARCH (AD HOC)
  ========================================================= */

  async function handleSearch(filters: {
    topics: string[];
    companies: string[];
    news_types: string[];
    period: "total" | "30d" | "7d";
  }) {

    setLoading(true);

    try {

      const json = await api.post(
        "/admin/digest/search",
        {
          ...filters,
          limit: 20,
        }
      );

      const data = json.result || json || {};

      setNews(data.news || []);
      setBreves(data.breves || []);
      setAnalyses(data.analyses || []);
      setNumbers(data.numbers || []);

      storeItems([
        ...(data.news || []),
        ...(data.breves || []),
        ...(data.analyses || []),
        ...(data.numbers || []),
      ]);

    } catch (e) {

      console.error(
        "Erreur search digest",
        e
      );

    } finally {

      setLoading(false);

    }
  }

  /* =========================================================
     MAP ORDER → DATA
  ========================================================= */

  const editorialNews = useMemo(
    () =>
      editorialOrder
        .filter(
          (i) => i.type === "news"
        )
        .map(
          (i) => selectedItemsMap[i.id]
        )
        .filter(Boolean) as NewsletterNewsItem[],
    [
      editorialOrder,
      selectedItemsMap,
    ]
  );

  const editorialBreves = useMemo(
    () =>
      editorialOrder
        .filter(
          (i) => i.type === "breve"
        )
        .map(
          (i) => selectedItemsMap[i.id]
        )
        .filter(Boolean) as NewsletterNewsItem[],
    [
      editorialOrder,
      selectedItemsMap,
    ]
  );

  const editorialAnalyses = useMemo(
    () =>
      editorialOrder
        .filter(
          (i) => i.type === "analysis"
        )
        .map(
          (i) => selectedItemsMap[i.id]
        )
        .filter(Boolean) as NewsletterAnalysisItem[],
    [
      editorialOrder,
      selectedItemsMap,
    ]
  );

  const editorialNumbers = useMemo(
    () =>
      editorialOrder
        .filter(
          (i) => i.type === "number"
        )
        .map(
          (i) => selectedItemsMap[i.id]
        )
        .filter(Boolean) as NewsletterNumberItem[],
    [
      editorialOrder,
      selectedItemsMap,
    ]
  );

  /* =========================================================
     UI
  ========================================================= */

  return (

    <div className="space-y-4">

      <div className="flex items-center justify-between">

        <h1 className="text-lg font-semibold tracking-tight">
          Digest
        </h1>

        {isRunMode && (
          <div className="text-xs bg-yellow-100 px-2 py-1 rounded">
            Mode édition mensuelle
          </div>
        )}

      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1.1fr_1.3fr] gap-6 items-start">

        {/* LEFT */}

        <div className="space-y-5">

          <DeliveryHeaderConfig
            headerConfig={headerConfig}
            setHeaderConfig={setHeaderConfig}
            introText={introText}
            setIntroText={setIntroText}
          />

          <NewsletterTopicStats period={30} />

          {!isRunMode && (
            <DigestEngine
              selectedTopics={selectedTopics}
              setSelectedTopics={setSelectedTopics}
              selectedCompanies={selectedCompanies}
              setSelectedCompanies={setSelectedCompanies}
              selectedTypes={selectedTypes}
              setSelectedTypes={setSelectedTypes}
              onSearch={handleSearch}
            />
          )}

          <DigestSelectors
            news={news}
            breves={breves}
            analyses={analyses}
            numbers={numbers}
            editorialOrder={editorialOrder}
            setEditorialOrder={setEditorialOrder}
          />

          <DigestEditorialFlow
            editorialOrder={editorialOrder}
            news={editorialNews}
            breves={editorialBreves}
            analyses={editorialAnalyses}
            numbers={editorialNumbers}
            setEditorialOrder={setEditorialOrder}
          />

        </div>

        {/* RIGHT */}

        <div className="sticky top-6 h-[calc(100vh-4rem)] overflow-y-auto pr-2">

          <DeliveryPreviewPanel
            headerConfig={headerConfig}
            editorialHtml={introText}
            news={editorialNews}
            breves={editorialBreves}
            analyses={editorialAnalyses}
            numbers={editorialNumbers}
            topicStats={topicStats}
          />

        </div>

      </div>

    </div>
  );
}
