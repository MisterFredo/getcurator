"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";

import FeedExplorer from "@/components/feed/FeedExplorer";
import SelectionPanel from "@/components/insight/SelectionPanel";

import AnalysisDrawer from "@/components/drawers/AnalysisDrawer";
import NewsDrawer from "@/components/drawers/NewsDrawer";

import { searchCurator, getLatestCurator } from "@/lib/search";

import type { FeedItem, FeedBadge } from "@/types/feed";
import { api } from "@/lib/api";

/* ========================================================= */

type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export default function FeedPage() {
  const LIMIT = 20;

  const searchParams = useSearchParams();
  const analysisId = searchParams.get("analysis_id");
  const newsId = searchParams.get("news_id");

  /* =========================================================
     UNIVERSE
  ========================================================= */

  const [universes, setUniverses] = useState<Universe[]>([]);
  const [activeUniverse, setActiveUniverse] = useState<string | null>(null);

  /* =========================================================
     DATA
  ========================================================= */

  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);

  const [hasMore, setHasMore] = useState(true);

  /* =========================================================
     SELECTION
  ========================================================= */

  const [selectedItems, setSelectedItems] = useState<FeedItem[]>([]);

  // 🔥 IMPORTANT → dérivé (remplace ton ancien selectedIds)
  const selectedIds = selectedItems.map((i) => i.id);

  /* =========================================================
     ANALYSIS
  ========================================================= */

  const [analysis, setAnalysis] = useState("");
  const [loadingInsight, setLoadingInsight] = useState(false);

  /* =========================================================
     PANEL
  ========================================================= */

  const [isPanelOpen, setIsPanelOpen] = useState(false);

  /* =========================================================
     DRAWER
  ========================================================= */

  const [selectedItem, setSelectedItem] =
    useState<FeedItem | null>(null);

  const [loadingItemId, setLoadingItemId] =
    useState<string | null>(null);

  /* =========================================================
     LOAD UNIVERS
  ========================================================= */

  useEffect(() => {
    async function loadUniverses() {
      try {
        const res = await api.get("/universe/list-for-user");
        setUniverses(res?.universes || []);
      } catch (e) {
        console.error("❌ universe load error", e);
      }
    }

    loadUniverses();
  }, []);

  /* =========================================================
     LOAD FEED
  ========================================================= */

  async function load(reset = false, q?: string) {
    if (loading && !reset) return;

    const finalQuery =
      q !== undefined ? q.trim() : query.trim();

    const currentOffset = reset ? 0 : offset;

    if (reset) {
      setItems([]);
      setOffset(0);
      setHasMore(true);
    }

    setLoading(true);

    try {
      const res = finalQuery
        ? await searchCurator({
            query: finalQuery,
            limit: LIMIT,
            offset: currentOffset,
            universe_id: activeUniverse || undefined,
          })
        : await getLatestCurator({
            limit: LIMIT,
            offset: currentOffset,
            universe_id: activeUniverse || undefined,
          });

      if (reset) {
        setItems(res.items);
        setOffset(res.items.length);
      } else {
        setItems((prev) => [...prev, ...res.items]);
        setOffset((prev) => prev + res.items.length);
      }

      setTotal(res.count ?? 0);
      setHasMore(res.items.length === LIMIT);

    } catch (e) {
      console.error("❌ load error", e);
    } finally {
      setLoading(false);
    }
  }

  /* =========================================================
     INIT + UNIVERSE CHANGE
  ========================================================= */

  useEffect(() => {
    load(true);
  }, [activeUniverse]);

  /* =========================================================
     DRAWER FROM URL
  ========================================================= */

  useEffect(() => {
    if (!analysisId && !newsId) return;
    if (selectedItem) return;

    if (analysisId) {
      setSelectedItem({
        id: analysisId,
        type: "analysis",
      } as FeedItem);
    }

    if (newsId) {
      setSelectedItem({
        id: newsId,
        type: "news",
      } as FeedItem);
    }

  }, [analysisId, newsId]);

  /* =========================================================
     BADGES
  ========================================================= */

  function handleBadgeClick(badge: FeedBadge) {

    if (badge.type === "universe") {
      setActiveUniverse(badge.id || null);
      setQuery("");
      window.scrollTo({ top: 0 });
      return;
    }

    const value = badge.label;
    if (!value) return;

    setQuery(value);
    setActiveUniverse(null);

    window.scrollTo({ top: 0 });

    load(true, value);
  }

  /* =========================================================
     DRAWER
  ========================================================= */

  function handleSelectItem(item: FeedItem) {
    setLoadingItemId(item.id);
    setSelectedItem(item);

    setTimeout(() => {
      setLoadingItemId(null);
    }, 300);
  }

  /* =========================================================
     SELECTION
  ========================================================= */

  function toggleSelect(item: FeedItem) {
    setSelectedItems((prev) => {
      const exists = prev.some((i) => i.id === item.id);

      if (exists) {
        return prev.filter((i) => i.id !== item.id);
      }

      return [...prev, item];
    });

    // 🔥 IMPORTANT → garde comportement panel
    setIsPanelOpen(true);
  }

  /* =========================================================
     INSIGHT
  ========================================================= */

  async function generateInsight() {
    if (!selectedIds.length) return;

    setLoadingInsight(true);

    try {
      const res: any = await api.post("/insight/", {
        ids: selectedIds,
      });

      setAnalysis(res.insight || "");

    } catch (e) {
      console.error("❌ generateInsight error", e);
    } finally {
      setLoadingInsight(false);
    }
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 items-start">

      <div className="xl:col-span-2">

        <FeedExplorer
          query={query}
          setQuery={setQuery}
          onSearch={() => load(true, query)}

          universes={universes.map(u => ({
            id: u.id_universe,
            label: u.label
          }))}

          selectedUniverse={activeUniverse}
          onSelectUniverse={(id) => setActiveUniverse(id)}

          items={items}
          total={total}
          loading={loading}
          hasMore={hasMore}

          onLoadMore={() => load(false)}
          onSelectItem={handleSelectItem}
          onClickBadge={handleBadgeClick}

          loadingItemId={loadingItemId}

          selectedIds={selectedIds}
          onToggleSelect={toggleSelect}
        />
      </div>

      {isPanelOpen && (
        <div className="xl:col-span-1 sticky top-6 h-[calc(100vh-120px)]">
          <SelectionPanel
            selectedItems={selectedItems}
            analysis={analysis}
            loading={loadingInsight}
            onGenerateInsight={generateInsight}
            onClose={() => setIsPanelOpen(false)}
          />
        </div>
      )}

      {selectedItem && (
        <>
          {selectedItem.type === "analysis" && (
            <AnalysisDrawer
              id={selectedItem.id}
              onClose={() => setSelectedItem(null)}
            />
          )}

          {selectedItem.type === "news" && (
            <NewsDrawer
              id={selectedItem.id}
              onClose={() => setSelectedItem(null)}
            />
          )}
        </>
      )}
    </div>
  );
}
