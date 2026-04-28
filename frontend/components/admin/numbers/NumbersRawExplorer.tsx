"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

/* ========================================================= */

export default function NumbersRawExplorer() {

  const [items, setItems] = useState<any[]>([]);
  const [types, setTypes] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [typeId, setTypeId] = useState("");

  /* ========================================================= */

  async function load() {

    const [raw, typesRes] = await Promise.all([
      api.get("/numbers/raw"),
      api.get("/numbers/types"),
    ]);

    setItems(raw.items || []);
    setTypes(typesRes || []);
  }

  useEffect(() => {
    load();
  }, []);

  /* ========================================================= */

  async function handleDismiss(id: string) {

    await api.post(`/numbers/raw/${id}/dismiss`);

    setItems(prev => prev.filter(i => i.id !== id));
  }

  async function handleKeep(item: any) {

    if (!typeId) {
      alert("Select a type");
      return;
    }

    await api.post("/numbers/", {
      label: item.label,
      value: item.value,
      unit: item.unit,
      scale: item.scale || null,
      zone: item.market,
      period: item.period,
      id_number_type: typeId,
    });

    setItems(prev => prev.filter(i => i !== item));
    setSelectedId(null);
    setTypeId("");
  }

  /* ========================================================= */

  return (

    <div className="space-y-4">

      <h2 className="text-xl font-semibold">
        Raw Numbers Review
      </h2>

      <div className="border rounded">

        <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_2fr_auto] text-xs bg-gray-100 p-2 font-semibold">
          <div>Label</div>
          <div>Value</div>
          <div>Unit</div>
          <div>Market</div>
          <div>Period</div>
          <div>Actor</div>
          <div></div>
        </div>

        {items.map((item) => (

          <div key={item.id} className="border-t p-2 text-sm">

            <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_2fr_auto] items-center">

              <div>{item.label}</div>
              <div>{item.value}</div>
              <div>{item.unit}</div>
              <div>{item.market}</div>
              <div>{item.period}</div>
              <div>{item.actor}</div>

              <div className="flex gap-2">

                <button
                  onClick={() => handleDismiss(item.id)}
                  className="text-red-600"
                >
                  Dismiss
                </button>

                <button
                  onClick={() => setSelectedId(item.id)}
                  className="text-blue-600"
                >
                  Keep
                </button>

              </div>

            </div>

            {/* KEEP PANEL */}

            {selectedId === item.id && (

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
                  onClick={() => handleKeep(item)}
                  className="bg-blue-600 text-white px-2 rounded"
                >
                  Confirm
                </button>

              </div>

            )}

          </div>

        ))}

      </div>

    </div>
  );
}
