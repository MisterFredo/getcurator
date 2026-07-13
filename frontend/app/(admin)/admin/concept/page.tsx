"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  Pencil,
  Trash2,
} from "lucide-react";

import { api } from "@/lib/api";

/* ========================================================= */

type Concept = {
  id_concept: string;
  label: string;
  description: string;
};

/* ========================================================= */

export default function ConceptList() {

  const [
    concepts,
    setConcepts,
  ] = useState<Concept[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    deletingId,
    setDeletingId,
  ] = useState<string | null>(
    null
  );

  const [
    search,
    setSearch,
  ] = useState("");

  /* ======================================================= */

  useEffect(() => {

    async function load() {

      try {

        const res =
          await api.get(
            "/concept/list"
          );

        setConcepts(
          res.concepts ?? []
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  /* ======================================================= */

  async function handleDelete(
    id: string,
  ) {

    if (
      !window.confirm(
        "Delete this concept?"
      )
    ) {
      return;
    }

    try {

      setDeletingId(id);

      await api.delete(
        `/concept/${id}`
      );

      setConcepts((prev) =>
        prev.filter(
          (c) =>
            c.id_concept !== id
        )
      );

    } finally {

      setDeletingId(null);

    }

  }

  /* ======================================================= */

  const filtered =
    concepts.filter((c) => {

      const q =
        search.toLowerCase();

      return (
        c.label
          .toLowerCase()
          .includes(q) ||
        (c.description ?? "")
          .toLowerCase()
          .includes(q)
      );

    });

  /* ======================================================= */

  if (loading) {

    return (
      <p>
        Loading...
      </p>
    );

  }

  return (

    <div className="space-y-8">

      <div className="flex justify-between items-center">

        <h1 className="text-3xl font-semibold">
          Concepts
        </h1>

        <Link
          href="/admin/concept/create"
          className="bg-ratecard-green text-white px-4 py-2 rounded"
        >
          + Add concept
        </Link>

      </div>

      <input
        value={search}
        onChange={(e) =>
          setSearch(
            e.target.value
          )
        }
        className="border rounded px-3 py-2 w-full max-w-md"
        placeholder="Search concept..."
      />

      <div className="border rounded overflow-hidden">

        <table className="w-full text-sm">

          <thead className="bg-gray-100">

            <tr>

              <th className="p-3 text-left">
                Label
              </th>

              <th className="p-3 text-left">
                Description
              </th>

              <th className="p-3 w-28 text-right">
                Actions
              </th>

            </tr>

          </thead>

          <tbody>

            {filtered.map((c) => (

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

                <td className="p-3 flex justify-end gap-3">

                  <Link
                    href={`/admin/concept/edit/${c.id_concept}`}
                    className="text-blue-600"
                  >
                    <Pencil size={16}/>
                  </Link>

                  <button
                    disabled={
                      deletingId ===
                      c.id_concept
                    }
                    onClick={() =>
                      handleDelete(
                        c.id_concept
                      )
                    }
                    className="text-red-600"
                  >
                    <Trash2 size={16}/>
                  </button>

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </div>

    </div>

  );

}
