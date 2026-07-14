"use client";

import { useState } from "react";
import { Trash2, Play } from "lucide-react";

const PAGE_SIZE = 50;

export default function StockTable({
  raws,
  onDestock,
  onRetry,
  onDelete,
  onOpen,
}: any) {

  const [page, setPage] = useState(1);

  const totalPages = Math.ceil(raws.length / PAGE_SIZE);

  const paginated = raws.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );

  function getStatusClasses(status: string) {
    if (status === "STORED") return "bg-yellow-100 text-yellow-700";
    if (status === "PROCESSING") return "bg-blue-100 text-blue-700";
    if (status === "PROCESSED") return "bg-green-100 text-green-700";
    if (status === "ERROR") return "bg-red-100 text-red-700";
    return "bg-gray-100 text-gray-700";
  }

  function formatDate(value?: string | null) {
    if (!value) return "—";
    return new Date(value).toLocaleDateString("fr-FR");
  }

  return (
    <div className="space-y-4">

      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-100 border-b text-left text-gray-700 sticky top-0">
            <th className="p-2">Source</th>

            {/* 🔥 NEW */}
            <th className="p-2">Type</th>

            {/* 🔥 NEW */}
            <th className="p-2">
              Primary company
            </th>

            <th className="p-2">Titre</th>
            <th className="p-2">Date source</th>
            <th className="p-2">Créé</th>
            <th className="p-2">Import</th>
            <th className="p-2">Statut</th>
            <th className="p-2">Erreur</th>
            <th className="p-2 text-right">Actions</th>
          </tr>
        </thead>

        <tbody>
          {paginated.map((r: any) => (
            <tr
              key={r.id_raw}
              className="border-b hover:bg-gray-50 transition cursor-pointer"
              onClick={() => onOpen(r)}
            >
              <td className="p-2 text-gray-600">
                {r.source_name || r.source_id}
              </td>

              {/* 🔥 NEW */}
              <td className="p-2 text-gray-600">
                {r.primary_company_name || "—"}
              </td>

              <td className="p-2 font-medium">
                {r.source_title}
              </td>

              <td className="p-2 text-gray-600">
                {formatDate(r.date_source)}
              </td>

              <td className="p-2 text-gray-600">
                {formatDate(r.created_at)}
              </td>

              <td className="p-2">
                <span className="text-xs px-2 py-1 rounded bg-gray-200">
                  {r.import_type || "—"}
                </span>
              </td>

              <td className="p-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusClasses(r.status)}`}>
                  {r.status}
                </span>
              </td>

              <td className="p-2 text-xs text-red-600 max-w-xs truncate">
                {r.status === "ERROR" ? r.error_message : ""}
              </td>

              <td
                className="p-2 text-right space-x-3"
                onClick={(e) => e.stopPropagation()}
              >
                {r.status === "STORED" && (
                  <button
                    onClick={() => onDestock(r.id_raw)}
                    className="text-green-600"
                  >
                    <Play size={16} />
                  </button>
                )}

                {r.status === "ERROR" && (
                  <button
                    onClick={() => onRetry(r.id_raw)}
                    className="text-orange-600"
                  >
                    ↺
                  </button>
                )}

                <button
                  onClick={() => onDelete(r.id_raw)}
                  className="text-red-600"
                >
                  <Trash2 size={16} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="flex justify-center gap-4">
          <button
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="px-3 py-1 border rounded disabled:opacity-40"
          >
            Précédent
          </button>

          <span className="text-sm">
            Page {page} / {totalPages}
          </span>

          <button
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
            className="px-3 py-1 border rounded disabled:opacity-40"
          >
            Suivant
          </button>
        </div>
      )}

    </div>
  );
}
