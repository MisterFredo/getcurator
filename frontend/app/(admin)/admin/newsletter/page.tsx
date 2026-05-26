"use client";

import { useMemo, useState, useEffect } from "react";

import NewsletterEngine from "@/components/newsletter/NewsletterEngine";
import NewsletterSelectors from "@/components/newsletter/NewsletterSelectors";

import DeliveryHeaderConfig from "@/components/delivery/DeliveryHeaderConfig";
import DeliveryEditorialFlow from "@/components/delivery/DeliveryEditorialFlow";
import DeliveryPreviewPanel from "@/components/delivery/DeliveryPreviewPanel";

import NewsletterTopicStats from "@/components/newsletter/NewsletterTopicStats";

import { api } from "@/lib/api";

import type {
  NewsletterNewsItem,
  HeaderConfig,
  TopicStat,
} from "@/types/newsletter";

import type {
  SelectOption,
} from "@/components/ui/SearchableMultiSelect";

/* ========================================================= */

type EditorialItem = {
  id: string;
  type: "news" | "breve";
};

/* ========================================================= */

export default function NewsletterPage() {

  const [loading, setLoading] = useState(false);

  /* =========================================================
     DATA
  ========================================================= */

  const [news, setNews] = useState<
    NewsletterNewsItem[]
  >([]);

  const [breves, setBreves] = useState<
    NewsletterNewsItem[]
  >([]);

  /* =========================================================
     FILTERS
  ========================================================= */

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
            last_30_days: t.last_30_days ?? 0,
            total: t.total ?? 0,
          }))
          .sort(
            (a, b) =>
              b.last_30_days - a.last_30_days
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
     SEARCH
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
        "/admin/newsletter/search",
        {
          ...filters,
          limit: 20,
        }
      );

      const data = json.result || json || {};

      setNews(data.news || []);
      setBreves(data.breves || []);

      storeItems([
        ...(data.news || []),
        ...(data.breves || []),
      ]);

    } catch (e) {

      console.error(
        "Erreur search newsletter",
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
        .filter((i) => i.type === "news")
        .map((i) => selectedItemsMap[i.id])
        .filter(Boolean) as NewsletterNewsItem[],
    [editorialOrder, selectedItemsMap]
  );

  const editorialBreves = useMemo(
    () =>
      editorialOrder
        .filter((i) => i.type === "breve")
        .map((i) => selectedItemsMap[i.id])
        .filter(Boolean) as NewsletterNewsItem[],
    [editorialOrder, selectedItemsMap]
  );

  /* =========================================================
     UI
  ========================================================= */

  return (

    <div className="space-y-4">

      <div className="flex items-center justify-between">

        <h1 className="text-lg font-semibold tracking-tight">
          Newsletter
        </h1>

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

          <NewsletterEngine
            selectedTopics={selectedTopics}
            setSelectedTopics={setSelectedTopics}
            selectedCompanies={selectedCompanies}
            setSelectedCompanies={setSelectedCompanies}
            selectedTypes={selectedTypes}
            setSelectedTypes={setSelectedTypes}
            onSearch={handleSearch}
          />

          <NewsletterSelectors
            news={news}
            breves={breves}
            editorialOrder={editorialOrder}
            setEditorialOrder={setEditorialOrder}
          />

          <DeliveryEditorialFlow
            editorialOrder={editorialOrder}
            news={editorialNews}
            breves={editorialBreves}
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
            topicStats={topicStats}
          />

        </div>

      </div>

    </div>
  );
}
