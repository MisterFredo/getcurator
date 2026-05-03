"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Option = { id: string; label: string };

export default function NumbersAdminList() {

  const LIMIT = 100;

  const [items, setItems] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const [types, setTypes] = useState<Option[]>([]);
  const [topics, setTopics] = useState<Option[]>([]);
  const [companies, setCompanies] = useState<Option[]>([]);
  const [solutions, setSolutions] = useState<Option[]>([]);

  const [typeId, setTypeId] = useState("");
  const [topicId, setTopicId] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [solutionId, setSolutionId] = useState("");

  const [loading, setLoading] = useState(false);

  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  /* ========================================================= */

  async function loadFilters() {
    const [typesRes, t, c, s] = await Promise.all([
      api.get("/numbers/types"),
      api.get("/topic/list"),
      api.get("/company/list"),
      api.get("/solution/list"),
    ]);

    setTypes(typesRes || []);
    setTopics(t.topics || []);
    setCompanies(c.companies || []);
    setSolutions(s.solutions || []);
  }

  /* ========================================================= */

  async function search(reset = true) {

    setLoading(true);

    const params = new URLSearchParams();

    if (typeId) params.append("id_number_type", typeId);
    if (topicId) params.append("topic_id", topicId);
    if (companyId) params.append("company_id", companyId);
    if (solutionId) params.append("solution_id", solutionId);

    params.append("limit", String(LIMIT));
    params.append("offset", String(reset ? 0 : offset));

    const res = await api.get(`/numbers/search?${params}`);
    const newItems = res.items || [];

    if (reset) {
      setItems(newItems);
      setOffset(newItems.length);
    } else {
      setItems(prev => [...prev, ...newItems]);
      setOffset(prev => prev + newItems.length);
    }

    setHasMore(newItems.length === LIMIT);
    setLoading(false);
  }

  /* =========================================================
     SELECTION
  ========================================================= */

  function toggleSelect(id: string) {
    setSelectedIds(prev =>
      prev.includes(id)
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  }

  function selectAllVisible() {
    setSelectedIds(items.map(i => i.id));
  }

  function clearSelection() {
    setSelectedIds([]);
  }

  /* =========================================================
     BULK ACTIONS
  ========================================================= */

  async function validateSelected() {
    if (!selectedIds.length) return;

    await api.post("/numbers/bulk/validate", {
      ids: selectedIds,
    });

    setItems(prev => prev.filter(i => !selectedIds.includes(i.id)));
    setSelectedIds([]);
  }

  async function validateAllLoaded() {
    const ids = items.map(i => i.id);

    await api.post("/numbers/bulk/validate", {
      ids,
    });

    setItems([]);
    setSelectedIds([]);
  }

  /* ========================================================= */

  useEffect(() => {
    loadFilters();
  }, []);

  /* ========================================================= */

  return (

    <div className="space-y-6">

      <h2 className="text-xl font-semibold">Numbers Admin</h2>

      {/* FILTERS */}
      <div className="grid grid-cols-5 gap-2">

        <select onChange={(e) => setTypeId(e.target.value)} className="border p-2">
          <option value="">Type</option>
          {types.map((t) => (
            <option key={t.id} value={t.id}>{t.label}</option>
          ))}
        </select>

        <select onChange={(e) => setTopicId(e.target.value)} className="border p-2">
          <option value="">Topic</option>
          {topics.map((t: any) => (
            <option key={t.id_topic} value={t.id_topic}>{t.label}</option>
          ))}
        </select>

        <select onChange={(e) => setCompanyId(e.target.value)} className="border p-2">
          <option value="">Company</option>
          {companies.map((c: any) => (
            <option key={c.id_company} value={c.id_company}>{c.name}</option>
          ))}
        </select>

        <select onChange={(e) => setSolutionId(e.target.value)} className="border p-2">
          <option value="">Solution</option>
          {solutions.map((s: any) => (
            <option key={s.id_solution} value={s.id_solution}>{s.name}</option>
          ))}
        </select>

        <button onClick={() => search(true)} className="bg-blue-600 text-white rounded px-3">
          Search
        </button>

      </div>

      {/* BULK ACTION BAR */}
      {items.length > 0 && (
        <div className="flex gap-2 items-center text-sm">

          <button onClick={selectAllVisible} className="px-3 py-1 bg-gray-100 rounded">
            Select all
          </button>

          <button onClick={clearSelection} className="px-3 py-1 bg-gray-100 rounded">
            Clear
          </button>

          <button onClick={validateSelected} className="px-3 py-1 bg-green-600 text-white rounded">
            Validate selected ({selectedIds.length})
          </button>

          <button onClick={validateAllLoaded} className="px-3 py-1 bg-black text-white rounded">
            Validate ALL loaded ({items.length})
          </button>

        </div>
      )}

      {/* TABLE */}
      <div className="border rounded">

        <div className="grid grid-cols-[auto_2fr_1fr_1fr_1fr_1fr_1fr_1fr] text-xs bg-gray-100 p-2 font-semibold">
          <div></div>
          <div>Label</div>
          <div>Value</div>
          <div>Scale</div>
          <div>Unit</div>
          <div>Type</div>
          <div>Zone</div>
          <div>Period</div>
        </div>

        {items.map((n) => (

          <div
            key={n.id}
            className="grid grid-cols-[auto_2fr_1fr_1fr_1fr_1fr_1fr_1fr] text-sm p-2 border-t"
          >

            <input
              type="checkbox"
              checked={selectedIds.includes(n.id)}
              onChange={() => toggleSelect(n.id)}
            />

            <div>{n.label || "-"}</div>
            <div>{n.value}</div>
            <div>{n.scale}</div>
            <div>{n.unit}</div>
            <div>{n.type}</div>
            <div>{n.zone}</div>
            <div>{n.period}</div>

          </div>

        ))}

        {/* LOAD MORE */}
        {!loading && hasMore && (
          <div className="p-4 text-center">
            <button onClick={() => search(false)} className="px-4 py-2 bg-gray-200 rounded">
              Load more
            </button>
          </div>
        )}

      </div>

    </div>
  );
}
