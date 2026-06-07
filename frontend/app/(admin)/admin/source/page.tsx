"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

const GCS_BASE_URL = process.env.NEXT_PUBLIC_GCS_BASE_URL!;
const SOURCE_MEDIA_PATH = "sources";

type SourceRow = {
  source_id: string;
  name: string;
  type_source?: string | null;
  domain?: string | null;
  author?: string | null;
  logo?: string | null;

  universe_id?: string | null;

  acquisition_mode?: "AUTO" | "MANUAL" | null;
};

type Universe = {
  id_universe: string;
  label: string;
};

export default function SourceList() {

  const [sources, setSources] = useState<SourceRow[]>([]);
  const [universes, setUniverses] = useState<Universe[]>([]);

  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  // =========================================================
  // LOAD DATA
  // =========================================================

  useEffect(() => {
    async function load() {
      setLoading(true);

      try {

        const [sourcesRes, universesRes] = await Promise.all([
          api.get("/source/list"),
          api.get("/universe/list"),
        ]);

        setSources(sourcesRes.sources || []);
        setUniverses(universesRes.universes || []);

      } catch (e) {

        console.error(e);
        alert("❌ Erreur chargement sources");

      } finally {

        setLoading(false);

      }
    }

    load();
  }, []);

  // =========================================================
  // DELETE
  // =========================================================

  async function deleteSource(id: string, name: string) {

    const ok = confirm(`Supprimer la source "${name}" ?`);
    if (!ok) return;

    try {

      await api.delete(`/source/${id}`);

      setSources((prev) =>
        prev.filter((s) => s.source_id !== id)
      );

    } catch (e) {

      console.error(e);
      alert("❌ Erreur suppression");

    }
  }

  // =========================================================
  // HELPERS
  // =========================================================

  function getUniverseLabel(universeId?: string | null) {
    if (!universeId) return null;

    const u = universes.find((x) => x.id_universe === universeId);
    return u?.label || null;
  }

  const q = search.toLowerCase();

  const filteredSources = sources.filter((s) =>
    s.name.toLowerCase().includes(q) ||
    (s.type_source || "").toLowerCase().includes(q) ||
    (s.domain || "").toLowerCase().includes(q)
  );

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="space-y-8">

      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-semibold text-ratecard-blue">
          Sources
        </h1>

        <Link
          href="/admin/source/create"
          className="bg-ratecard-green px-4 py-2 text-white rounded"
        >
          + Ajouter une source
        </Link>
      </div>

      {/* SEARCH */}
      <div>
        <input
          type="text"
          placeholder="Rechercher une source..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border px-3 py-2 rounded w-full max-w-md"
        />
      </div>

      {loading ? (
        <p className="text-gray-500">Chargement…</p>
      ) : filteredSources.length === 0 ? (
        <p className="italic text-gray-500">
          Aucune source.
        </p>
      ) : (
        <table className="w-full text-sm border-collapse">

          <thead>
            <tr className="bg-gray-100 border-b text-left">
              <th className="p-2">Nom</th>
              <th className="p-2">Type</th>
              <th className="p-2">Domaine</th>
              <th className="p-2">Auteur</th>
              <th className="p-2">Univers</th>
              <th className="p-2">Acquisition</th>
              <th className="p-2">Logo</th>
              <th className="p-2 text-right">Actions</th>
            </tr>
          </thead>

          <tbody>

            {filteredSources.map((s) => {

              const logoUrl = s.logo
                ? `${GCS_BASE_URL}/${SOURCE_MEDIA_PATH}/${s.logo}`
                : null;

              return (

                <tr
                  key={s.source_id}
                  className="border-b hover:bg-gray-50"
                >

                  {/* NAME */}
                  <td className="p-2 font-medium">
                    {s.name}
                  </td>

                  {/* TYPE */}
                  <td className="p-2">
                    {s.type_source || (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>

                  {/* DOMAIN */}
                  <td className="p-2">
                    {s.domain || (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>

                  {/* AUTHOR */}
                  <td className="p-2">
                    {s.author || (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>

                  {/* UNIVERSE */}
                  <td className="p-2">
                    {getUniverseLabel(s.universe_id) || (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>

                  {/* ACQUISITION */}
                  <td className="p-2">
                    {s.acquisition_mode === "AUTO" ? (
                      <span className="text-green-600 font-medium">
                        AUTO
                      </span>
                    ) : (
                      <span className="text-orange-600 font-medium">
                        MANUAL
                      </span>
                    )}
                  </td>

                  {/* LOGO */}
                  <td className="p-2">
                    {logoUrl ? (
                      <div className="w-14 h-14 flex items-center justify-center bg-white rounded">
                        <img
                          src={logoUrl}
                          alt={`Logo ${s.name}`}
                          className="max-w-[70%] max-h-[70%] object-contain"
                        />
                      </div>
                    ) : (
                      <span className="text-gray-400 text-sm">—</span>
                    )}
                  </td>

                  {/* ACTIONS */}
                  <td className="p-2 text-right space-x-3">

                    <Link
                      href={`/admin/source/edit/${s.source_id}`}
                      className="text-blue-600 hover:underline"
                    >
                      Modifier
                    </Link>

                    <button
                      onClick={() => deleteSource(s.source_id, s.name)}
                      className="text-red-600 hover:underline"
                    >
                      Supprimer
                    </button>

                  </td>

                </tr>

              );

            })}

          </tbody>

        </table>
      )}

    </div>
  );
}
