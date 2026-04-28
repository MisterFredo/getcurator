"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

/* ========================================================= */

export default function NumbersBacklogExplorer() {

  const [items, setItems] = useState<any[]>([]);
  const [types, setTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [typeId, setTypeId] = useState("");

  /* ========================================================= */

  async function load() {

    try {

      setLoading(true);

      const [res, typesRes] = await Promise.all([
        api.get("/numbers/backlog/processed"),
        api.get("/numbers/types"),
      ]);

      setItems(res.items || []);
      setTypes(typesRes || []);

    } catch (e) {
      console.error(e);
    }

    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  /* ========================================================= */

  async function handleCreate(item: any) {

    if (!typeId) {
      alert("Select a type");
      return;
    }

    try {

      await api.post("/numbers/", {
        label: item.LABEL,
        value: item.VALUE,
        unit: item.UNIT,
        scale: null,
        id_number_type: typeId,
        zone: item.MARKET,
        period: item.PERIOD,
        source_id: null,

        company_ids: [],
        topic_ids: [],
        solution_ids: [],
      });

      setItems(prev => prev.filter(i => i.ID_BACKLOG !== item.ID_BACKLOG));
      setSelectedId(null);
      setTypeId("");

    } catch (e) {
      console.error(e);
    }
  }

  /* ========================================================= */

  return (

    <div className="space-y-4">

      <h2 className="text-xl font-semibold">
        Backlog Review
      </h2>

      {loading && <div>Loading...</div>}

      {!loading && (

        <div className="border rounded">

          <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_2fr_1fr_auto] text-xs bg-gray-100 p-2 font-semibold">
            <div>Label</div>
            <div>Value</div>
            <div>Unit</div>
            <div>Market</div>
            <div>Period</div>
            <div>Actor</div>
            <div>Decision</div>
            <div></div>
          </div>

          {items.map((item) => (

            <div key={item.ID_BACKLOG} className="border-t p-2 text-sm">

              <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_2fr_1fr_auto] items-center">

                <div>{item.LABEL}</div>
                <div>{item.VALUE}</div>
                <div>{item.UNIT}</div>
                <div>{item.MARKET}</div>
                <div>{item.PERIOD}</div>
                <div>{item.ACTOR}</div>

                <div
                  className={`text-xs font-medium ${
                    item.DECISION === "KEEP"
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {item.DECISION}
                </div>

                <div className="flex gap-2">

                  {item.DECISION === "KEEP" && (
                    <button
                      onClick={() => setSelectedId(item.ID_BACKLOG)}
                      className="text-blue-600"
                    >
                      Create
                    </button>
                  )}

                </div>

              </div>

              {/* CREATE PANEL */}

              {selectedId === item.ID_BACKLOG && (

                <div className="mt-2 flex gap-2">

                  <select
                    value={typeId}
                    onChange={(e) => setTypeId(e.target.value)}
                    className="border p-1"
                  >
                    <option value="">Type</option>
                    {types.map((t: any) => (
                      <option key={t.id} value={t.id}>
                        {t.label}
                      </option>
                    ))}
                  </select>

                  <button
                    onClick={() => handleCreate(item)}
                    className="bg-blue-600 text-white px-2 rounded"
                  >
                    Confirm
                  </button>

                </div>

              )}

            </div>

          ))}

          {items.length === 0 && (
            <div className="p-4 text-sm text-gray-500">
              No backlog items
            </div>
          )}

        </div>

      )}

    </div>
  );
}
