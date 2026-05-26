"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type TopicStat = {
  id_topic: string;
  label: string;
  total: number;
  last_7_days: number;
  last_30_days: number;
};

type Props = {
  period?: 7 | 30;
  className?: string;
};

export default function DigestTopicStats({
  period = 30,
  className = "",
}: Props) {
  const [loading, setLoading] = useState(true);
  const [topics, setTopics] = useState<TopicStat[]>([]);

  useEffect(() => {
    async function loadStats() {
      try {
        const res = await api.get("/news/breves/stats");
        const data = res.result || res;

        const stats: TopicStat[] =
          data?.topics_stats || [];

        const sorted = [...stats].sort((a, b) => {
          if (period === 7) {
            return (
              (b.last_7_days || 0) -
              (a.last_7_days || 0)
            );
          }
          return (
            (b.last_30_days || 0) -
            (a.last_30_days || 0)
          );
        });

        // 🔥 LIMIT 12
        setTopics(sorted.slice(0, 12));

      } catch (e) {
        console.error("Erreur stats topics", e);
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, [period]);

  if (loading) {
    return (
      <div
        className={`border border-gray-200 rounded-lg p-4 bg-gray-50 text-xs text-gray-400 ${className}`}
      >
        Chargement du baromètre…
      </div>
    );
  }

  if (!topics.length) {
    return (
      <div
        className={`border border-gray-200 rounded-lg p-4 bg-gray-50 text-xs text-gray-400 ${className}`}
      >
        Aucune donnée disponible
      </div>
    );
  }

  return (
    <div
      className={`border border-gray-200 rounded-lg p-4 bg-gray-50 ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold">
          Baromètre marché
        </h2>
        <span className="text-xs text-gray-500">
          {period} jours
        </span>
      </div>

      <div className="grid grid-cols-2 gap-y-1 text-xs">
        {topics.map((t) => {
          const value =
            period === 7
              ? t.last_7_days
              : t.last_30_days;

          return (
            <div
              key={t.id_topic}
              className="flex justify-between"
            >
              <span className="text-gray-700 truncate pr-2">
                {t.label}
              </span>
              <span className="font-medium">
                {value || 0}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
