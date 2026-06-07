"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type DiscoveryItem = {
  id_discovery: string;

  source_id: string;
  source_name?: string | null;

  url: string;
  title?: string | null;

  status: string;

  date_found?: string | null;
  created_at?: string | null;
};

export default function DiscoveryPage() {

  const [items, setItems] = useState<DiscoveryItem[]>([]);

  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  // =========================================================
  // LOAD
  // =========================================================

  async function loadDiscovery() {

    try {

      setLoading(true);

      const res = await api.get(
        "/discovery/list"
      );

      setItems(
        res.items || []
      );

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur chargement Discovery"
      );

    } finally {

      setLoading(false);

    }
  }

  // =========================================================
  // INIT
  // =========================================================

  useEffect(() => {

    loadDiscovery();

  }, []);

  // =========================================================
  // SCAN ALL
  // =========================================================

  async function scanAll() {

    try {

      setScanning(true);

      const res = await api.post(
        "/discovery/scan-all"
      );

      alert(
        `${res.discovered_urls || 0} URL(s) découverte(s)`
      );

      await loadDiscovery();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur scan"
      );

    } finally {

      setScanning(false);

    }
  }

  // =========================================================
  // BADGE
  // =========================================================

  function getStatusBadge(
    status: string
  ) {

    switch (status) {

      case "STORED":
        return (
          <span className="px-2 py-1 rounded bg-green-100 text-green-700 text-xs font-medium">
            STORED
          </span>
        );

      case "IGNORED":
        return (
          <span className="px-2 py-1 rounded bg-gray-100 text-gray-700 text-xs font-medium">
            IGNORED
          </span>
        );

      default:
        return (
          <span className="px-2 py-1 rounded bg-orange-100 text-orange-700 text-xs font-medium">
            NEW
          </span>
        );
    }
  }

  // =========================================================
  // UI
  // =========================================================

  return (

    <div className="space-y-8">

      {/* HEADER */}

      <div className="flex justify-between items-center">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            Discovery
          </h1>

          <p className="text-gray-500 mt-1">
            Détection automatique des nouvelles URLs
          </p>

        </div>

        <button
          onClick={scanAll}
          disabled={scanning}
          className="bg-ratecard-green px-5 py-2 text-white rounded disabled:opacity-50"
        >
          {scanning
            ? "Scan en cours..."
            : "SCAN ALL SOURCES"}
        </button>

      </div>

      {/* COUNTER */}

      <div className="bg-white border rounded p-4">

        <div className="text-sm text-gray-500">
          URLs découvertes
        </div>

        <div className="text-3xl font-semibold mt-1">
          {items.length}
        </div>

      </div>

      {/* TABLE */}

      {loading ? (

        <div className="text-gray-500">
          Chargement...
        </div>

      ) : items.length === 0 ? (

        <div className="bg-white border rounded p-8 text-center text-gray-500">
          Aucune URL découverte.
        </div>

      ) : (

        <div className="bg-white border rounded overflow-hidden">

          <table className="w-full text-sm">

            <thead>

              <tr className="bg-gray-50 border-b text-left">

                <th className="p-3">
                  Source
                </th>

                <th className="p-3">
                  Titre
                </th>

                <th className="p-3">
                  URL
                </th>

                <th className="p-3">
                  Status
                </th>

              </tr>

            </thead>

            <tbody>

              {items.map((item) => (

                <tr
                  key={item.id_discovery}
                  className="border-b hover:bg-gray-50"
                >

                  {/* SOURCE */}

                  <td className="p-3 font-medium whitespace-nowrap">
                    {item.source_name || "—"}
                  </td>

                  {/* TITLE */}

                  <td className="p-3">
                    {item.title || "—"}
                  </td>

                  {/* URL */}

                  <td className="p-3">

                    <a
                      href={item.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 hover:underline break-all"
                    >
                      {item.url}
                    </a>

                  </td>

                  {/* STATUS */}

                  <td className="p-3 whitespace-nowrap">
                    {getStatusBadge(
                      item.status
                    )}
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
