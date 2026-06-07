"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import VisualSectionSource from "@/components/visuals/VisualSectionSource";

const GCS_BASE_URL = process.env.NEXT_PUBLIC_GCS_BASE_URL!;
const SOURCE_MEDIA_PATH = "sources";

export default function EditSource() {

  const params = useParams();
  const sourceId = params?.id as string;

  const [name, setName] = useState("");
  const [typeSource, setTypeSource] = useState("");
  const [description, setDescription] = useState("");
  const [domain, setDomain] = useState("");
  const [author, setAuthor] = useState("");
  const [authorProfile, setAuthorProfile] = useState("");

  const [acquisitionMode, setAcquisitionMode] = useState("MANUAL");

  const [universeId, setUniverseId] = useState("");
  const [universes, setUniverses] = useState<any[]>([]);

  const [logoFilename, setLogoFilename] = useState<string | null>(null);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // =========================================================
  // LOAD UNIVERS
  // =========================================================

  useEffect(() => {
    async function loadUniverses() {
      try {
        const res = await api.get("/universe/list");
        setUniverses(res.universes || []);
      } catch (e) {
        console.error("❌ load universes", e);
      }
    }

    loadUniverses();
  }, []);

  // =========================================================
  // LOAD SOURCE
  // =========================================================

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get(`/source/${sourceId}`);

        setName(res.name || "");
        setTypeSource(res.type_source || "");
        setDescription(res.description || "");
        setDomain(res.domain || "");
        setAuthor(res.author || "");
        setAuthorProfile(res.author_profile || "");
        setLogoFilename(res.logo || null);

        setUniverseId(res.universe_id || "");
        setAcquisitionMode(
          res.acquisition_mode || "MANUAL"
        );

      } catch (e) {
        console.error(e);
        alert("Erreur chargement source");
      } finally {
        setLoading(false);
      }
    }

    if (sourceId) {
      load();
    }
  }, [sourceId]);

  // =========================================================
  // SAVE
  // =========================================================

  async function save() {

    if (!name.trim()) {
      alert("Nom requis");
      return;
    }

    try {

      setSaving(true);

      await api.put(`/source/update/${sourceId}`, {
        name,
        type_source: typeSource || null,
        description: description || null,
        domain: domain || null,
        author: author || null,
        author_profile: authorProfile || null,
        universe_id: universeId || null,
        acquisition_mode: acquisitionMode,
      });

      alert("Source mise à jour");

    } catch (e) {

      console.error(e);
      alert("Erreur mise à jour");

    } finally {

      setSaving(false);

    }
  }

  // =========================================================
  // RELOAD
  // =========================================================

  async function reloadSource() {
    try {
      const s = await api.get(`/source/${sourceId}`);
      setLogoFilename(s.logo || null);
    } catch (e) {
      console.error(e);
      alert("❌ Erreur rechargement source");
    }
  }

  // =========================================================
  // DELETE
  // =========================================================

  async function remove() {

    if (!confirm("Supprimer cette source ?")) return;

    try {

      await api.delete(`/source/${sourceId}`);
      alert("Source supprimée");

      window.location.href = "/admin/source";

    } catch (e) {

      console.error(e);
      alert("Erreur suppression");

    }
  }

  if (loading) {
    return <div>Chargement...</div>;
  }

  const logoUrl = logoFilename
    ? `${GCS_BASE_URL}/${SOURCE_MEDIA_PATH}/${logoFilename}`
    : null;

  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="space-y-10">

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">
          Modifier la source
        </h1>

        <Link href="/admin/source" className="underline">
          ← Retour
        </Link>
      </div>

      {/* NAME */}
      <div className="space-y-2 max-w-xl">
        <label className="block text-sm font-medium">Nom</label>
        <input
          className="border p-2 w-full rounded"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      {/* TYPE */}
      <div className="space-y-2 max-w-md">
        <label className="block text-sm font-medium">Type</label>
        <input
          className="border p-2 w-full rounded"
          value={typeSource}
          onChange={(e) => setTypeSource(e.target.value)}
        />
      </div>

      {/* ACQUISITION MODE */}
      <div className="space-y-2 max-w-md">
        <label className="block text-sm font-medium">
          Mode d'acquisition
        </label>

        <select
          className="border p-2 w-full rounded"
          value={acquisitionMode}
          onChange={(e) => setAcquisitionMode(e.target.value)}
        >
          <option value="MANUAL">
            MANUAL - Copie / colle
          </option>

          <option value="AUTO">
            AUTO - Parse automatique
          </option>
        </select>
      </div>

      {/* UNIVERSE */}
      <div className="space-y-2 max-w-md">
        <label className="block text-sm font-medium">Univers</label>

        <select
          className="border p-2 w-full rounded"
          value={universeId}
          onChange={(e) => setUniverseId(e.target.value)}
        >
          <option value="">-- Aucun univers --</option>

          {universes.map((u) => (
            <option key={u.id_universe} value={u.id_universe}>
              {u.label}
            </option>
          ))}
        </select>
      </div>

      {/* DOMAIN */}
      <div className="space-y-2 max-w-md">
        <label className="block text-sm font-medium">Domaine</label>
        <input
          className="border p-2 w-full rounded"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
        />
      </div>

      {/* AUTHOR */}
      <div className="space-y-2 max-w-md">
        <label className="block text-sm font-medium">Auteur</label>
        <input
          className="border p-2 w-full rounded"
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
        />
      </div>

      {/* AUTHOR PROFILE */}
      <div className="space-y-2 max-w-xl">
        <label className="block text-sm font-medium">Profil auteur</label>
        <input
          className="border p-2 w-full rounded"
          value={authorProfile}
          onChange={(e) => setAuthorProfile(e.target.value)}
        />
      </div>

      {/* DESCRIPTION */}
      <div className="space-y-2 max-w-3xl">
        <label className="block text-sm font-medium">Description</label>
        <textarea
          className="border p-2 w-full rounded h-24"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      {/* ACTIONS */}
      <div className="flex gap-4">
        <button
          onClick={save}
          disabled={saving}
          className="bg-ratecard-blue px-6 py-2 text-white rounded"
        >
          {saving ? "Sauvegarde..." : "Enregistrer"}
        </button>

        <button
          onClick={remove}
          className="bg-red-600 px-6 py-2 text-white rounded"
        >
          Supprimer
        </button>
      </div>

      {/* LOGO */}
      <VisualSectionSource
        entityId={sourceId}
        rectUrl={logoUrl}
        onUpdated={reloadSource}
      />

    </div>
  );
}
