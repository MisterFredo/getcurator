"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

import {
  Pencil,
  Trash2,
} from "lucide-react";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const COMPANY_MEDIA_PATH =
  "companies";

/* ========================================================= */

type CompanyRow = {
  id_company: string;

  name: string;

  type?: string | null;

  media_logo_rectangle_id?: string | null;

  is_partner?: boolean | null;

  universes?: string[];
};

/* ========================================================= */

export default function CompanyList() {

  const [
    companies,
    setCompanies,
  ] = useState<CompanyRow[]>([]);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(true);

  /* ======================================================= */

  useEffect(() => {

    async function load() {

      setLoading(true);

      try {

        const res =
          await api.get("/company/list");

        setCompanies(
          res.companies || []
        );

      } catch (e) {

        console.error(e);

        alert(
          "Erreur chargement sociétés"
        );

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  /* ======================================================= */

  async function deleteCompany(
    id: string,
    name: string,
  ) {

    if (
      !confirm(
        `Supprimer "${name}" ?`
      )
    ) {
      return;
    }

    try {

      await api.delete(
        `/company/${id}`
      );

      setCompanies((prev) =>
        prev.filter(
          (c) =>
            c.id_company !== id
        )
      );

    } catch (e) {

      console.error(e);

      alert(
        "Erreur suppression"
      );

    }

  }

  /* ======================================================= */

  const filtered =
    companies.filter((c) => {

      const q =
        search.toLowerCase();

      return (
        c.name
          .toLowerCase()
          .includes(q)
        ||
        (
          c.type || ""
        )
          .toLowerCase()
          .includes(q)
      );

    });

  /* ======================================================= */

  return (

    <div className="space-y-8">

      {/* =================================================== */}

      <div className="flex items-center justify-between">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            Companies
          </h1>

          <div className="text-sm text-gray-500 mt-1">
            {companies.length} companies
          </div>

        </div>

        <Link
          href="/admin/company/create"
          className="bg-ratecard-green text-white px-4 py-2 rounded"
        >
          + New Company
        </Link>

      </div>

      {/* =================================================== */}

      <input
        value={search}
        onChange={(e) =>
          setSearch(
            e.target.value
          )
        }
        placeholder="Search..."
        className="border rounded px-3 py-2 w-full max-w-md"
      />

      {/* =================================================== */}

      {loading ? (

        <div>
          Loading...
        </div>

      ) : filtered.length === 0 ? (

        <div className="text-gray-500 italic">
          No company found.
        </div>

      ) : (

        <table className="w-full text-sm border-collapse">

          <thead>

            <tr className="bg-gray-100 border-b">

              <th className="p-2 w-[90px]">
                Logo
              </th>

              <th className="p-2 text-left">
                Name
              </th>

              <th className="p-2 text-left">
                Type
              </th>

              <th className="p-2 text-left">
                Universes
              </th>

              <th className="p-2 text-center">
                Partner
              </th>

              <th className="p-2 text-right">
                Actions
              </th>

            </tr>

          </thead>

          <tbody>

            {filtered.map((c) => {

              const logoUrl =
                c.media_logo_rectangle_id
                  ? `${GCS_BASE_URL}/${COMPANY_MEDIA_PATH}/${c.media_logo_rectangle_id}`
                  : null;

              return (

                <tr
                  key={c.id_company}
                  className="border-b hover:bg-gray-50"
                >

                  {/* LOGO */}

                  <td className="p-2">

                    {logoUrl ? (

                      <img
                        src={logoUrl}
                        alt={c.name}
                        className="h-10 max-w-[110px] object-contain"
                      />

                    ) : (

                      <span className="text-gray-400">
                        —
                      </span>

                    )}

                  </td>

                  {/* NAME */}

                  <td className="p-2 font-medium">
                    {c.name}
                  </td>

                  {/* TYPE */}

                  <td className="p-2">
                    {c.type || "—"}
                  </td>

                  {/* UNIVERSES */}

                  <td className="p-2">

                    <div className="flex flex-wrap gap-1">

                      {(c.universes || [])
                        .map((u) => (

                          <span
                            key={u}
                            className="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-700"
                          >
                            {u}
                          </span>

                        ))}

                    </div>

                  </td>

                  {/* PARTNER */}

                  <td className="text-center">

                    {c.is_partner
                      ? "✓"
                      : "—"}

                  </td>

                  {/* ACTIONS */}

                  <td className="text-right">

                    <div className="flex justify-end gap-3">

                      <Link
                        href={`/admin/company/edit/${c.id_company}`}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        <Pencil size={16} />
                      </Link>

                      <button
                        onClick={() =>
                          deleteCompany(
                            c.id_company,
                            c.name
                          )
                        }
                        className="text-red-600 hover:text-red-800"
                      >
                        <Trash2 size={16} />
                      </button>

                    </div>

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
