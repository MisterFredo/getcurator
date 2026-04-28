"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

/* ========================================================= */

type RawNumber = {
  id_content: string;
  label: string;
  value: number;
  unit: string;
  scale?: string | null;
  actor: string;
  market: string;
  period: string;
};

/* ========================================================= */

export default function NumbersRawExplorer() {

  const [items, setItems] = useState<RawNumber[]>([]);
  const [grouped, setGrouped] = useState<any[]>([]);

  const [loading, setLoading] = useState(false);

  /* ========================================================= */

  function normalizeLabel(label: string) {
    return label
      .toLowerCase()
      .replace(/[^a-z0-9 ]/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  /* ========================================================= */

  function groupData(data: RawNumber[]) {

    const map: any = {};

    data.forEach((item) => {

      const key = normalizeLabel(item.label);

      if (!map[key]) {
        map[key] = {
          label: key,
          count: 0,
          examples: [],
        };
      }

      map[key].count += 1;

      if (map[key].examples.length < 3) {
        map[key].examples.push(item.label);
      }

    });

    return Object.values(map)
      .sort((a: any, b: any) => b.count - a.count);
  }

  /* ========================================================= */

  async function load() {

    try {

      setLoading(true);

      const res = await api.get("/numbers/raw");

      const data = res.items || [];

      setItems(data);
      setGrouped(groupData(data));

    } catch (e) {
      console.error(e);
    }

    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  /* ========================================================= */

  return (

    <div className="space-y-6">

      <h2 className="text-xl font-semibold">
        Raw Numbers Explorer
      </h2>

      {loading && <div>Loading...</div>}

      {!loading && (

        <div className="border rounded">

          <div className="grid grid-cols-[2fr_1fr_3fr_auto] text-xs bg-gray-100 p-2 font-semibold">
            <div>Label (normalized)</div>
            <div>Count</div>
            <div>Examples</div>
            <div></div>
          </div>

          {grouped.map((g: any, i: number) => (

            <div
              key={i}
              className="grid grid-cols-[2fr_1fr_3fr_auto] text-sm p-2 border-t"
            >

              <div>{g.label}</div>
              <div>{g.count}</div>
              <div>{g.examples.join(" / ")}</div>

              <button
                className="text-blue-600"
                onClick={() => alert("TODO: send to assistant")}
              >
                Select
              </button>

            </div>

          ))}

        </div>

      )}

    </div>
  );
}
