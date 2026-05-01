"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Pencil, Trash2 } from "lucide-react";

type ConceptRow = {
  id_concept: string;
  label: string;
  description?: string;
  is_active?: boolean;
  updated_at?: string;
};

export default function ConceptList() {

  const [loading, setLoading] = useState(true);
  const [concepts, setConcepts] = useState<ConceptRow[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {

    async function load() {

      try {

        const res = await api.get("/concept/list");
        setConcepts(res.concepts || []);

      } catch (e) {

        console.error(e);
        alert("❌ Erreur chargement concepts");

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  async function handleDelete(id: string) {

    const confirmDelete = window.confirm(
      "Confirmer la suppression de ce concept ?"
    );

    if (!confirmDelete) return;

    setDeletingId(id);

    try {

      await api.delete(`/concept/${id}`);

      setConcepts((prev) =>
        prev.filter((c) => c.id_concept !== id)
      );

    } catch (e) {

      console.error(e);
      alert("❌ Erreur suppression concept");

    } finally {

      setDeletingId(null);

    }

  }

  if (loading) return <p>Chargement…</p>;

  return (
    <div className="space-y-8">

      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-semibold">
          Concepts
        </h1>

        <Link
          href="/admin/concept/create"
          className="bg-ratecard-blue text-white px-4 py-2 rounded"
        >
          + Nouveau concept
        </Link>
      </div>

      <div className="border rounded overflow-hidden">

        <table className="w-full text-sm">

          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-3">Label</th>
              <th className="p-3">Description</th>
              <th className="p-3">Statut</th>
              <th className="p-3">Mis à jour</th>
              <th className="p-3 w-24"></th>
            </tr>
          </thead>

          <tbody>

            {concepts.map((c) => (

              <tr
                key={c.id_concept}
                className="border-t hover:bg-gray-50"
              >

                <td className="p-3 font-medium">
                  {c.label}
                </td>

                <td className="p-3 text-gray-600">
                  {c.description || "—"}
                </td>

                <td className="p-3">
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      c.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-200 text-gray-600"
                    }`}
                  >
                    {c.is_active ? "Actif" : "Inactif"}
                  </span>
                </td>

                <td className="p-3 text-gray-500">
                  {c.updated_at
                    ? new Date(c.updated_at).toLocaleDateString()
                    : "-"}
                </td>

                <td className="p-3 flex items-center gap-3">

                  <Link
                    href={`/admin/concept/edit/${c.id_concept}`}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Pencil size={16} />
                  </Link>

                  <button
                    onClick={() =>
                      handleDelete(c.id_concept)
                    }
                    disabled={deletingId === c.id_concept}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                  >
                    <Trash2 size={16} />
                  </button>

                </td>

              </tr>

            ))}

            {concepts.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="p-6 text-center text-gray-400"
                >
                  Aucun concept trouvé
                </td>
              </tr>
            )}

          </tbody>

        </table>

      </div>

    </div>
  );
}
