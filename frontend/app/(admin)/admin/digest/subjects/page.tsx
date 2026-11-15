"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import SubjectDigestDocument, { type SubjectDigest } from "@/components/digest/SubjectDigestDocument";

const endpoint = "/digest/admin/subject-digests";

type Recipient = { id: string; name: string; company?: string };
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
  const [audience, setAudience] = useState<"user" | "expert">("user");
  const [recipients, setRecipients] = useState<Recipient[]>([]);
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
    setRecipients([]);
    setSelection([]);
    api.get(endpoint + "/recipients?audience=" + audience)
      .then(result => { if (active) setRecipients(result.recipients); })
      .catch(error => { if (active) setErrors(current => [...current, message(error)]); });
    return () => { active = false; };
  }, [audience]);

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
      const name = recipients.find(item => item.id === userId)?.name ?? document?.profile.name ?? userId;
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

  const filtered = recipients.filter(person =>
    (person.name + " " + (person.company ?? "")).toLowerCase().includes(search.toLowerCase()));
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
          <label className="grid gap-1 text-sm">Audience
            <select className="rounded border px-3 py-2" value={audience}
              onChange={event => setAudience(event.target.value === "expert" ? "expert" : "user")}>
              <option value="user">Utilisateurs</option>
              <option value="expert">Experts</option>
            </select>
          </label>
        </div>
        <label className="grid gap-1 text-sm">Rechercher un profil
          <input className="rounded border px-3 py-2" value={search} onChange={event => setSearch(event.target.value)} />
        </label>
        <div className="max-h-52 space-y-1 overflow-auto rounded border p-3">
          {filtered.map(person => (
            <label key={person.id} className="flex gap-2 text-sm">
              <input type="checkbox" checked={selection.includes(person.id)} onChange={event => {
                const checked = event.target.checked;
                setSelection(current => checked ? [...current, person.id] : current.filter(id => id !== person.id));
              }} />
              {[person.name, person.company].filter(Boolean).join(" · ")}
            </label>
          ))}
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
