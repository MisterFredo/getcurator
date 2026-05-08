"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Option = { id: string; label: string };

export default function NumbersAdminList() {

  const [items, setItems] = useState<any[]>([]);

  const [types, setTypes] = useState<Option[]>([]);
  const [topics, setTopics] = useState<Option[]>([]);
  const [companies, setCompanies] = useState<Option[]>([]);
  const [solutions, setSolutions] = useState<Option[]>([]);

  const [typeId, setTypeId] = useState("");
  const [topicId, setTopicId] = useState("");
  const [companyId, setCompanyId] = useState("");
  const [solutionId, setSolutionId] = useState("");

  const [loading, setLoading] = useState(false);

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

  async function search() {

    try {

      setLoading(true);

      const params = new URLSearchParams();

      if (typeId) params.append("id_number_type", typeId);
      if (topicId) params.append("topic_id", topicId);
      if (companyId) params.append("company_id", companyId);
      if (solutionId) params.append("solution_id", solutionId);

      const res = await api.get(`/numbers/search?${params}`);

      setItems(res.items || []);

    } catch (e) {
      console.error(e);
    }

    setLoading(false);
  }

  async function handleDelete(id: string) {

    if (!confirm("Delete this number ?")) return;

    try {

      await api.delete(`/numbers/${id}`);

      setItems(prev => prev.filter(i => i.id !== id));

    } catch (e) {
      console.error(e);
    }
  }

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

        <button onClick={search} className="bg-blue-600 text-white rounded px-3">
          Search
        </button>

      </div>

      {/* TABLE */}
      <div className="border rounded">

        <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr_1fr_auto] text-xs bg-gray-100 p-2 font-semibold">
          <div>Label</div>
          <div>Value</div>
          <div>Scale</div>
          <div>Unit</div>
          <div>Type</div>
          <div>Zone</div>
          <div>Period</div>
          <div></div>
        </div>

        {items.map((n) => (

          <div
            key={n.id}
            className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_1fr_1fr_auto] text-sm p-2 border-t"
          >

            <div>{n.label || "-"}</div>
            <div>{n.value}</div>
            <div>{n.scale}</div>
            <div>{n.unit}</div>
            <div>{n.type}</div>
            <div>{n.zone}</div>
            <div>{n.period}</div>

            <button
              onClick={() => handleDelete(n.id)}
              className="text-red-600"
            >
              Delete
            </button>

            {/* ENTITIES */}
            <div className="col-span-8 text-xs text-gray-500 mt-1">
              {(n.topics || []).join(", ")} | {(n.companies || []).join(", ")} | {(n.solutions || []).join(", ")}
            </div>

          </div>

        ))}

        {!loading && items.length === 0 && (
          <div className="p-4 text-sm text-gray-500">
            No results
          </div>
        )}

        {loading && (
          <div className="p-4 text-sm text-gray-500">
            Loading...
          </div>
        )}

      </div>

    </div>
  );
}
