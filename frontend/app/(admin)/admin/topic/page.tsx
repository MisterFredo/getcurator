"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type Universe = {
  id_universe: string;
  label: string;
};

type TopicRow = {
  id_topic: string;
  label: string;
  universes?: Universe[];
  nb_analyses?: number;
  delta_30d?: number;
};

export default function TopicList() {

  const [topics, setTopics] = useState<TopicRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {

    async function load() {

      try {

        const res = await api.get("/topic/list");
        setTopics(res.topics || []);

      } catch (e) {

        console.error(e);
        alert("❌ Erreur chargement topics");

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  // ============================================================
  // RENDER UNIVERS
  // ============================================================

  function renderUniverses(universes?: Universe[]) {

    if (!universes || universes.length === 0) {
      return <span className="text-gray-400 text-xs">Aucun</span>;
    }

    return (
      <div className="flex flex-wrap gap-1">
        {universes.map((u) => (
          <span
            key={u.id_universe}
            className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-800"
          >
            {u.label}
          </span>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-8">

      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-semibold">
          Topics
        </h1>

        <Link
          href="/admin/topic/create"
          className="bg-ratecard-green px-4 py-2 text-white rounded"
        >
          + Ajouter un topic
        </Link>
      </div>

      {loading ? (

        <p className="text-gray-500">Chargement…</p>

      ) : topics.length === 0 ? (

        <p className="italic text-gray-500">
          Aucun topic.
        </p>

      ) : (

        <div className="border rounded overflow-hidden">

          <table className="w-full text-sm">
            <thead className="bg-gray-100 text-left">
              <tr>
                <th className="p-3">Label</th>
                <th className="p-3">Univers</th>
                <th className="p-3">Analyses</th>
                <th className="p-3">Δ 30j</th>
                <th className="p-3 w-24 text-right">Actions</th>
              </tr>
            </thead>

            <tbody>
              {topics.map((t) => (
                <tr
                  key={t.id_topic}
                  className="border-t hover:bg-gray-50"
                >
                  <td className="p-3 font-medium">
                    {t.label}
                  </td>

                  <td className="p-3">
                    {renderUniverses(t.universes)}
                  </td>

                  <td className="p-3 text-gray-700">
                    {t.nb_analyses ?? 0}
                  </td>

                  <td className="p-3 text-gray-700">
                    {t.delta_30d ?? 0}
                  </td>

                  <td className="p-3 text-right">
                    <Link
                      href={`/admin/topic/edit/${t.id_topic}`}
                      className="text-blue-600 hover:underline"
                    >
                      Modifier
                    </Link>
                  </td>

                </tr>
              ))}
            </tbody>
          </table>

        </div>

      )}

    </div>
  );
}
