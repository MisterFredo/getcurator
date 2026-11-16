"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import SubjectDigestDocument, { type SubjectDigest } from "@/components/digest/SubjectDigestDocument";

const endpoint = "/digest/admin/subject-digests";

type Recipient = { id: string; name: string; company?: string };
const audiences = [
  { id: "user", label: "Utilisateurs" },
  { id: "expert", label: "Experts" },
] as const;
type Audience = (typeof audiences)[number]["id"];
type RecipientList = { items: Recipient[]; loading: boolean; error?: string };
type SavedDigest = { id: string; name: string; user_id: string; generated_at: string };

function previousMonday() {
  const now = new Date();
  now.setHours(12, 0, 0, 0);
  now.setDate(now.getDate() - ((now.getDay() + 6) % 7) - 7);
  return now.toISOString().slice(0, 10);
}

function message(error: unknown) {
  return error instanceof Error ? error.message : "Action indisponible.";
}


export default function SubjectDigestsPage() {
  const [periodStart, setPeriodStart] = useState(previousMonday);
  const [lists, setLists] = useState<Record<Audience, RecipientList>>({
    user: { items: [], loading: true },
    expert: { items: [], loading: true },
  });
  const [selection, setSelection] = useState<string[]>([]);
  const [search, setSearch] = useState("");
  const [saved, setSaved] = useState<SavedDigest[]>([]);
  const [document, setDocument] = useState<SubjectDigest | null>(null);
  const [progress, setProgress] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [requestedDigest, setRequestedDigest] = useState<{ id: string; week: string } | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const week = params.get("period_start");
    if (!week || !/^\d{4}-\d{2}-\d{2}$/.test(week)) return;
    setPeriodStart(week);
    const id = params.get("digest_id");
    if (id) setRequestedDigest({ id, week });
  }, []);

  useEffect(() => {
    let active = true;
    for (const { id } of audiences) {
      api.get(endpoint + "/recipients?audience=" + id)
        .then(result => {
          if (active) setLists(current => ({
            ...current, [id]: { items: result.recipients, loading: false },
          }));
        })
        .catch(error => {
          if (active) setLists(current => ({
            ...current, [id]: { items: [], loading: false, error: message(error) },
          }));
        });
    }
    return () => { active = false; };
  }, []);

  async function readWeek(start: string): Promise<SavedDigest[]> {
    const result = await api.get(endpoint + "?period_start=" + encodeURIComponent(start));
    return result.digests;
  }

  useEffect(() => {
    let active = true;
    setSaved([]);
    setDocument(null);
    if (periodStart) {
      readWeek(periodStart)
        .then(items => { if (active) setSaved(items); })
        .catch(error => { if (active) setErrors(current => [...current, message(error)]); });
    }
    return () => { active = false; };
  }, [periodStart]);

  useEffect(() => {
    if (!requestedDigest || requestedDigest.week !== periodStart) return;
    let active = true;
    setProgress("Chargement du Digest…");
    api.get(endpoint + "/" + encodeURIComponent(requestedDigest.id))
      .then(result => { if (active) setDocument(result.document); })
      .catch(error => { if (active) setErrors(current => [...current, message(error)]); })
      .finally(() => {
        if (active) {
          setRequestedDigest(null);
          setProgress("");
        }
      });
    return () => { active = false; };
  }, [requestedDigest, periodStart]);

  async function generate(ids: string[], regenerate = false) {
    setErrors([]);
    const failures: string[] = [];
    for (let index = 0; index < ids.length; index += 1) {
      const userId = ids[index];
      const name = (lists.user.items.find(item => item.id === userId)
        ?? lists.expert.items.find(item => item.id === userId))?.name ?? document?.profile.name ?? userId;
      setProgress(`${index + 1}/${ids.length} · ${name}`);
      try {
        const result = await api.post(endpoint, { user_id: userId, period_start: periodStart, regenerate });
        setDocument(result.document);
      } catch (error) {
        failures.push(`${name} · ${message(error)}`);
      }
    }
    try {
      setSaved(await readWeek(periodStart));
    } catch (error) {
      failures.push(message(error));
    } finally {
      setErrors(failures);
      setProgress("");
    }
  }

  const searchTerm = search.trim().toLowerCase();
  const selectedSaved = saved.find(item => item.id === document?.id);

  return (
    <div className="space-y-6">
      <Link href="/admin/digest" className="text-sm text-ratecard-blue underline">Retour aux Digests</Link>
      <Link href="/admin/digest/subjects/history" className="ml-4 text-sm text-ratecard-blue underline">Historique des Digests par sujets</Link>
      <h1 className="text-3xl font-semibold">Digests par sujets</h1>
      <fieldset disabled={!!progress} className="space-y-4 rounded-xl border bg-white p-5">
        <div className="flex flex-wrap gap-4">
          <label className="grid gap-1 text-sm">Début de semaine
            <input className="rounded border px-3 py-2" type="date" value={periodStart}
              onChange={event => setPeriodStart(event.target.value)} />
          </label>
        </div>
        <label className="grid gap-1 text-sm">Rechercher un profil
          <input className="rounded border px-3 py-2" value={search} onChange={event => setSearch(event.target.value)} />
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          {audiences.map(({ id, label }) => {
            const list = lists[id];
            const filtered = list.items.filter(person =>
              (person.name + " " + (person.company ?? "")).toLowerCase().includes(searchTerm));
            const count = list.items.filter(person => selection.includes(person.id)).length;
            return (
              <section key={id} aria-labelledby={id + "-recipients"} className="rounded border">
                <h2 id={id + "-recipients"} className="border-b bg-gray-50 px-3 py-2 text-sm font-semibold">
                  {label}{count > 0 && " · " + count + " sélectionné(s)"}
                </h2>
                <div className="max-h-56 space-y-1 overflow-auto p-3">
                  {list.loading && <p role="status" className="text-sm text-gray-500">Chargement…</p>}
                  {list.error && <p role="alert" className="text-sm text-red-700">{list.error}</p>}
                  {!list.loading && !list.error && !filtered.length && (
                    <p className="text-sm text-gray-500">{searchTerm ? "Aucun profil trouvé." : "Aucun profil éligible."}</p>
                  )}
                  {filtered.map(person => (
                    <label key={person.id} className="flex gap-2 text-sm">
                      <input type="checkbox" checked={selection.includes(person.id)} onChange={event => {
                        const checked = event.target.checked;
                        setSelection(current => checked
                          ? Array.from(new Set([...current, person.id]))
                          : current.filter(selectedId => selectedId !== person.id));
                      }} />
                      {[person.name, person.company].filter(Boolean).join(" · ")}
                    </label>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
        <button type="button" disabled={!periodStart || !selection.length}
          className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50"
          onClick={() => void generate(selection)}>
          Générer ({selection.length})
        </button>
      </fieldset>
      {progress && <p role="status">{progress}</p>}
      {!!errors.length && <ul role="alert" className="space-y-1 text-sm text-red-700">
        {errors.map((error, index) => <li key={index}>{error}</li>)}
      </ul>}
      {document && (
        <>
          {selectedSaved && (
            <button type="button" disabled={!!progress} className="rounded border bg-white px-3 py-2 text-sm"
              onClick={() => void generate([selectedSaved.user_id], true)}>Régénérer ce Digest</button>
          )}
          <SubjectDigestDocument digest={document} />
        </>
      )}
    </div>
  );
}
