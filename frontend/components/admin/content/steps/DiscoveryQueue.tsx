"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

type DiscoveryItem = {
  id_discovery: string;

  source_id: string;
  source_name?: string | null;

  url: string;
  title?: string | null;

  date_found?: string | null;
};

type Props = {
  onSelect: (
    item: DiscoveryItem
  ) => void;
};

export default function DiscoveryQueue({
  onSelect,
}: Props) {

  const [items, setItems] = useState<
    DiscoveryItem[]
  >([]);

  const [loading, setLoading] =
    useState(true);

  // ==========================================================
  // LOAD
  // ==========================================================

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const res = await api.get(
          "/discovery/manual-list"
        );

        setItems(
          res.items || []
        );

      } catch (e) {

        console.error(
          "Erreur chargement discovery",
          e
        );

      } finally {

        setLoading(false);

      }
    }

    load();

  }, []);

  // ==========================================================
  // EMPTY
  // ==========================================================

  if (
    !loading &&
    items.length === 0
  ) {
    return null;
  }

  // ==========================================================
  // UI
  // ==========================================================

  return (

    <div className="bg-blue-50 border border-blue-200 rounded p-4">

      <div className="flex items-center justify-between mb-3">

        <div>

          <h3 className="font-semibold text-blue-900">
            Discovery en attente
          </h3>

          <p className="text-xs text-blue-700 mt-1">
            URLs envoyées au Studio
          </p>

        </div>

        <div className="text-xs text-blue-700 font-medium">
          {items.length} URL(s)
        </div>

      </div>

      {loading ? (

        <div className="text-sm text-gray-500">
          Chargement...
        </div>

      ) : (

        <div className="space-y-3 max-h-72 overflow-auto">

          {items.map((item) => (

            <div
              key={item.id_discovery}
              className="bg-white border rounded p-3"
            >

              <div className="font-medium text-sm">
                {item.title || "Sans titre"}
              </div>

              <div className="text-xs text-gray-500 mt-1">
                {item.source_name}
              </div>

              <div className="text-xs text-gray-500 mt-1 break-all">
                {item.url}
              </div>

              <div className="flex justify-between items-center mt-3">

                <div className="text-xs text-gray-400">

                  {item.date_found
                    ? new Date(
                        item.date_found
                      ).toLocaleDateString()
                    : "—"}

                </div>

                <button
                  onClick={() =>
                    onSelect(item)
                  }
                  className="px-3 py-1 bg-ratecard-blue text-white rounded text-xs"
                >
                  UTILISER
                </button>

              </div>

            </div>

          ))}

        </div>

      )}

    </div>

  );
}
