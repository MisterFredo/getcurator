"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function CreateConcept() {

  const [label, setLabel] = useState("");
  const [description, setDescription] = useState("");

  const [loading, setLoading] = useState(false);

  async function save() {

    if (!label.trim()) {
      alert("Label requis");
      return;
    }

    try {

      setLoading(true);

      await api.post("/concept/create", {
        label,
        description: description || null,
      });

      alert("Concept créé avec succès");

      setLabel("");
      setDescription("");

    } catch (e) {

      console.error(e);
      alert("❌ Erreur création concept");

    } finally {

      setLoading(false);

    }

  }

  return (
    <div className="space-y-10">

      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">
          Ajouter un concept
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
          placeholder="Ex: Consumer Behavior"
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
          placeholder="Définition du concept"
        />
      </div>

      <button
        onClick={save}
        disabled={loading}
        className="bg-ratecard-blue px-6 py-2 text-white rounded disabled:opacity-50"
      >
        {loading ? "Création..." : "Créer le concept"}
      </button>

    </div>
  );
}
