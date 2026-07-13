"use client";

import { useEffect, useState } from "react";

import Link from "next/link";

import { Pencil, Trash2 } from "lucide-react";

import { api } from "@/lib/api";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

/* ========================================================= */

type SolutionRow = {

  id_solution: string;

  name: string;

  company_name?: string | null;

  media_logo_rectangle_id?: string | null;

  logo_type?: "solution" | "company";

};

/* ========================================================= */

export default function SolutionList() {

  const [
    solutions,
    setSolutions,
  ] = useState<
    SolutionRow[]
  >([]);

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

  /* =======================================================
     LOAD
  ======================================================= */

  useEffect(() => {

    async function load() {

      try {

        const res =
          await api.get(
            "/solution/list"
          );

        setSolutions(
          res.solutions ?? []
        );

      } catch (e) {

        console.error(e);

        alert(
          "Erreur chargement solutions."
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  /* =======================================================
     DELETE
  ======================================================= */

  async function handleDelete(
    id: string,
  ) {

    const ok = confirm(
      "Delete this solution?"
    );

    if (!ok) {
      return;
    }

    try {

      setDeletingId(id);

      await api.delete(
        `/solution/${id}`
      );

      setSolutions((prev) =>
        prev.filter(
          (s) =>
            s.id_solution !== id
        )
      );

    } catch (e) {

      console.error(e);

      alert(
        "Erreur suppression."
      );

    } finally {

      setDeletingId(null);

    }

  }

  /* =======================================================
     FILTER
  ======================================================= */

  const q =
    search.toLowerCase();

  const filteredSolutions =
    solutions.filter((s) =>

      s.name
        .toLowerCase()
        .includes(q)

      ||

      (
        s.company_name ?? ""
      )
        .toLowerCase()
        .includes(q)

    );

  /* =======================================================
     LOADING
  ======================================================= */

  if (loading) {

    return (
      <p className="text-gray-500">
        Chargement...
      </p>
    );

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-8">

      {/* =================================================== */}
      {/* HEADER */}
      {/* =================================================== */}

      <div className="flex justify-between items-center">

        <h1 className="text-3xl font-semibold text-ratecard-blue">
          Solutions
        </h1>

        <Link

          href="/admin/solution/create"

          className="
            bg-ratecard-green
            px-4
            py-2
            rounded
            text-white
          "

        >
          + Add solution
        </Link>

      </div>

      {/* =================================================== */}
      {/* SEARCH */}
      {/* =================================================== */}

      <input

        value={search}

        onChange={(e) =>
          setSearch(
            e.target.value
          )
        }

        placeholder="Search solution..."

        className="
          w-full
          max-w-md
          border
          rounded
          px-3
          py-2
        "

      />

      {/* =================================================== */}
      {/* TABLE */}
      {/* =================================================== */}

      <div className="border rounded overflow-hidden">

        <table className="w-full text-sm">

          <thead className="bg-gray-100">

            <tr>

              <th className="p-3 text-left">
                Name
              </th>

              <th className="p-3 text-left">
                Company
              </th>

              <th className="p-3 text-left">
                Logo
              </th>

              <th className="p-3 text-right w-28">
                Actions
              </th>

            </tr>

          </thead>

          <tbody>

            {filteredSolutions.map((s) => {

              const folder =
                s.logo_type === "solution"
                  ? "solutions"
                  : "companies";

              const rectUrl =
                s.media_logo_rectangle_id

                  ? `${GCS_BASE_URL}/${folder}/${s.media_logo_rectangle_id}`

                  : null;

              return (

                <tr

                  key={s.id_solution}

                  className="
                    border-t
                    hover:bg-gray-50
                  "

                >

                  <td className="p-3 font-medium">
                    {s.name}
                  </td>

                  <td className="p-3">

                    {s.company_name ?? (

                      <span className="text-gray-400">
                        —
                      </span>

                    )}

                  </td>

                  <td className="p-3">

                    {rectUrl ? (

                      <img

                        src={rectUrl}

                        alt={s.name}

                        className="
                          h-8
                          max-w-[100px]
                          object-contain
                        "

                      />

                    ) : (

                      <span className="text-gray-400">
                        —
                      </span>

                    )}

                  </td>

                  <td className="p-3">

                    <div className="flex justify-end gap-3">

                      <Link

                        href={`/admin/solution/edit/${s.id_solution}`}

                        className="
                          text-blue-600
                          hover:text-blue-800
                        "

                      >
                        <Pencil size={16} />
                      </Link>

                      <button

                        disabled={
                          deletingId ===
                          s.id_solution
                        }

                        onClick={() =>
                          handleDelete(
                            s.id_solution
                          )
                        }

                        className="
                          text-red-600
                          hover:text-red-800
                          disabled:opacity-40
                        "

                      >
                        <Trash2 size={16} />
                      </button>

                    </div>

                  </td>

                </tr>

              );

            })}

            {filteredSolutions.length === 0 && (

              <tr>

                <td

                  colSpan={4}

                  className="
                    p-6
                    text-center
                    text-gray-400
                  "

                >
                  No solution found.
                </td>

              </tr>

            )}

          </tbody>

        </table>

      </div>

    </div>

  );

}
