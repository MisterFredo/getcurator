"use client";

import { useEffect, useState } from "react";

import Link from "next/link";

import { Pencil, Trash2 } from "lucide-react";

import { api } from "@/lib/api";

import { Universe } from "@/types/topic";

/* ========================================================= */

type Topic = {
  id_topic: string;

  label: string;

  universes: Universe[];
};

/* ========================================================= */

export default function TopicList() {

  const [
    topics,
    setTopics,
  ] = useState<Topic[]>([]);

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
            "/topic/list"
          );

        setTopics(
          res.topics ?? []
        );

      } catch (e) {

        console.error(e);

        setTopics([]);

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

    const confirmed =
      window.confirm(
        "Delete this topic?"
      );

    if (!confirmed) {
      return;
    }

    try {

      setDeletingId(id);

      await api.delete(
        `/topic/${id}`
      );

      setTopics((prev) =>
        prev.filter(
          (t) =>
            t.id_topic !== id
        )
      );

    } catch (e) {

      console.error(e);

      alert(
        "Unable to delete topic."
      );

    } finally {

      setDeletingId(null);

    }

  }

  /* ======================================================= */

  const q =
    search.toLowerCase();

  const filteredTopics =
    topics.filter((t) => {

      if (
        t.label
          .toLowerCase()
          .includes(q)
      ) {
        return true;
      }

      return (
        t.universes ?? []
      ).some((u) =>
        u.label
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

  /* ======================================================= */

  return (

    <div className="space-y-8">

      <div className="flex items-center justify-between">

        <h1 className="text-3xl font-semibold">
          Topics
        </h1>

        <Link
          href="/admin/topic/create"
          className="bg-ratecard-green px-4 py-2 rounded text-white"
        >
          + Add topic
        </Link>

      </div>

      <div>

        <input
          type="text"
          value={search}
          placeholder="Search topic..."
          onChange={(e) =>
            setSearch(
              e.target.value
            )
          }
          className="border rounded px-3 py-2 w-full max-w-md"
        />

      </div>

      <div className="border rounded overflow-hidden">

        <table className="w-full text-sm">

          <thead className="bg-gray-100 text-left">

            <tr>

              <th className="p-3">
                Label
              </th>

              <th className="p-3">
                Universes
              </th>

              <th className="p-3 w-28 text-right">
                Actions
              </th>

            </tr>

          </thead>

          <tbody>

            {filteredTopics.map((t) => (

              <tr
                key={t.id_topic}
                className="border-t hover:bg-gray-50"
              >

                <td className="p-3 font-medium">
                  {t.label}
                </td>

                <td className="p-3">

                  <div className="flex flex-wrap gap-2">

                    {(t.universes ?? []).map(
                      (u) => (

                        <span
                          key={
                            u.id_universe
                          }
                          className="px-2 py-1 rounded bg-gray-100 text-xs"
                        >
                          {u.label}
                        </span>

                      )
                    )}

                  </div>

                </td>

                <td className="p-3 flex justify-end items-center gap-3">

                  <Link
                    href={`/admin/topic/edit/${t.id_topic}`}
                    className="text-blue-600 hover:text-blue-800"
                  >

                    <Pencil
                      size={16}
                    />

                  </Link>

                  <button
                    onClick={() =>
                      handleDelete(
                        t.id_topic
                      )
                    }
                    disabled={
                      deletingId ===
                      t.id_topic
                    }
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                  >

                    <Trash2
                      size={16}
                    />

                  </button>

                </td>

              </tr>

            ))}

            {filteredTopics.length ===
              0 && (

              <tr>

                <td
                  colSpan={3}
                  className="p-6 text-center text-gray-400"
                >
                  No topic found.
                </td>

              </tr>

            )}

          </tbody>

        </table>

      </div>

    </div>

  );

}
