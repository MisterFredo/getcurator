"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function EditConcept({
  params,
}: {
  params: { id: string };
}) {
  const { id } = params;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [label, setLabel] = useState("");
  const [description, setDescription] = useState("");
  const [isActive, setIsActive] = useState(true);

  /* LOAD CONCEPT */
  useEffect(() => {
    async function load() {
      setLoading(true);

      try {
        const concept = await api.get(`/concept/${id}`);

        setLabel(concept.label || "");
        setDescription(concept.description || "");
        setIsActive(concept.is_active ?? true);

      } catch (e) {
        console.error(e);
        alert("❌ Erreur chargement concept");
      }

      setLoading(false);
    }

    load();
  }, [id]);

  /* SAVE */
  async function save() {
    if (!label.trim()) {
      alert("Label requis");
      return;
    }

    setSaving(true);

    try {
      await api.put(`/concept/update/${id}`, {
        label,
        description: description || null,
        is_active: isActive,
      });

      alert("Concept mis à jour");

    } catch (e) {
      console.error(e);
      alert("❌ Erreur mise à jour concept");
    }

    setSaving(false);
  }

  if (loading) return <p>Chargement…</p>;

  return (
    <div className="space-y-10">

      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-semibold">
          Modifier le concept
        </h1>

        <Link href="/admin/concept" className="underline">
          ← Retour
        </Link>
      </div>

      <div className="space-y-2 max-w-2xl">
        <label className="block text-sm font-medium">
          Label
        </label>

        <input
          className="border p-2 w-full rounded"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
      </div>

      <div className="space-y-2 max-w-2xl">
        <label className="block text-sm font-medium">
          Description (optionnelle)
        </label>

        <textarea
          className="border p-2 w-full rounded h-24"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div className="space-y-2 max-w-sm">
        <label className="block text-sm font-medium">
          Actif
        </label>

        <select
          className="border p-2 rounded w-full"
          value={isActive ? "true" : "false"}
          onChange={(e) =>
            setIsActive(e.target.value === "true")
          }
        >
          <option value="true">Actif</option>
          <option value="false">Inactif</option>
        </select>
      </div>

      <button
        onClick={save}
        disabled={saving}
        className="bg-ratecard-blue px-6 py-2 text-white rounded disabled:opacity-50"
      >
        {saving ? "Enregistrement…" : "Enregistrer"}
      </button>

    </div>
  );
}
