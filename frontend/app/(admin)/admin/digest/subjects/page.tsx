"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  digestV2Endpoint as endpoint, previousDigestMonday, generateUserDigestsV2,
  digestBatchMessage, type DigestRecipient,
} from "@/lib/digest-v2";
import SubjectDigestDocument, { type SubjectDigest } from "@/components/digest/SubjectDigestDocument";

type Saved = { id: string; name: string; user_id: string };

export default function DigestPage() {
  const [week, setWeek] = useState(previousDigestMonday);
  const [users, setUsers] = useState<DigestRecipient[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [userSearch, setUserSearch] = useState("");
  const [userError, setUserError] = useState("");
  const [experts, setExperts] = useState<DigestRecipient[]>([]);
  const [expertLoading, setExpertLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [saved, setSaved] = useState<Saved[]>([]);
  const [document, setDocument] = useState<(SubjectDigest & { user_id: string }) | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const start = params.get("period_start");
    if (start && /^\d{4}-\d{2}-\d{2}$/.test(start)) setWeek(start);
    const id = params.get("digest_id");
    if (id) {
      api.get(endpoint + "/" + encodeURIComponent(id))
        .then(result => setDocument(result.document))
        .catch(failure => setError(failure instanceof Error ? failure.message : "Digest indisponible."));
    }
    let active = true;
    api.get(endpoint + "/recipients?audience=user")
      .then(result => { if (active) setUsers(result.recipients); })
      .catch(failure => { if (active) setUserError(failure instanceof Error ? failure.message : "Utilisateurs indisponibles."); })
      .finally(() => { if (active) setUsersLoading(false); });
    api.get(endpoint + "/recipients?audience=expert")
      .then(result => { if (active) setExperts(result.recipients); })
      .catch(failure => { if (active) setError(failure instanceof Error ? failure.message : "Experts indisponibles."); })
      .finally(() => { if (active) setExpertLoading(false); });
    return () => { active = false; };
  }, []);

  async function readWeek(start: string) {
    const result: Saved[] = [];
    for (let offset = 0; ; offset += 200) {
      const response = await api.get(endpoint + "?" + new URLSearchParams({
        period_start: start, limit: "200", offset: String(offset),
      }).toString());
      result.push(...response.digests);
      if (response.digests.length < 200) return result;
    }
  }

  useEffect(() => {
    let active = true;
    setSaved([]);
    if (week) readWeek(week)
      .then(items => { if (active) setSaved(items); })
      .catch(failure => { if (active) setError(failure instanceof Error ? failure.message : "Historique indisponible."); });
    return () => { active = false; };
  }, [week]);

  async function perform(action: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await action();
      setSaved(await readWeek(week));
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Opération indisponible.");
    } finally {
      setBusy(false);
    }
  }

  async function generateUsers() {
    await perform(async () => {
      const result = await generateUserDigestsV2(week, setStatus);
      setStatus(digestBatchMessage(result));
      if (result.errors.length) setError(result.errors.join(" · "));
    });
  }

  async function generateIndividual(person: DigestRecipient) {
    await perform(async () => {
      setStatus("Génération · " + person.name);
      const result = await api.post(endpoint, { user_id: person.id, period_start: week });
      setDocument(result.document);
      setStatus("Digest disponible · " + person.name);
    });
  }

  async function open(id: string) {
    await perform(async () => {
      const result = await api.get(endpoint + "/" + encodeURIComponent(id));
      setDocument(result.document);
      setStatus("");
    });
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-semibold">Digests</h1>
        <Link href="/admin/digest/subjects/history" className="rounded border bg-white px-4 py-2 text-sm">Historique des Digests</Link>
      </header>
      <fieldset disabled={busy} className="space-y-4 rounded-xl border bg-white p-5">
        <label className="grid max-w-xs gap-1 text-sm">
          Semaine commençant le lundi
          <input type="date" value={week} className="rounded border px-3 py-2" onChange={event => {
            setWeek(event.target.value);
            setDocument(null);
            setStatus("");
          }} />
        </label>
        <section className="space-y-2">
          <h2 className="font-semibold">Utilisateurs</h2>
          <p className="text-sm text-gray-500">Génération pour tous les utilisateurs éligibles de cette semaine. Garder la page ouverte pendant le traitement.</p>
          <button type="button" disabled={!week} onClick={() => void generateUsers()}
            className="rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50">Générer les Digests Users</button>
          <input aria-label="Rechercher un utilisateur" placeholder="Rechercher un utilisateur ou une société"
            value={userSearch} onChange={event => setUserSearch(event.target.value)}
            className="w-full rounded border px-3 py-2 text-sm" />
          {usersLoading && <p role="status" className="text-sm">Chargement des utilisateurs…</p>}
          {userError && <p role="alert" className="text-sm text-red-700">{userError}</p>}
          <ul className="max-h-80 divide-y overflow-auto">
            {users.filter(person => (person.name + " " + (person.company ?? "")).toLowerCase().includes(userSearch.toLowerCase())).map(person => {
              const existing = saved.find(item => item.user_id === person.id);
              return <li key={person.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                <span>{person.name}<span className="ml-2 text-gray-500">{person.company}</span></span>
                <button type="button" disabled={!week} className="rounded border px-3 py-2"
                  onClick={() => existing ? void open(existing.id) : void generateIndividual(person)}>
                  {existing ? "Ouvrir · généré" : "Générer"}
                </button>
              </li>;
            })}
          </ul>
          {!usersLoading && !userError && !users.some(person =>
            (person.name + " " + (person.company ?? "")).toLowerCase().includes(userSearch.toLowerCase())
          ) && <p className="text-sm text-gray-500">Aucun utilisateur trouvé.</p>}
        </section>
        <section className="space-y-3 border-t pt-4">
          <h2 className="font-semibold">Experts</h2>
          <input aria-label="Rechercher un expert" placeholder="Rechercher un expert" value={search}
            onChange={event => setSearch(event.target.value)} className="w-full rounded border px-3 py-2 text-sm" />
          {expertLoading && <p role="status">Chargement des experts…</p>}
          <ul className="max-h-80 divide-y overflow-auto">
            {experts.filter(person => (person.name + " " + (person.company ?? "")).toLowerCase().includes(search.toLowerCase())).map(person => {
              const existing = saved.find(item => item.user_id === person.id);
              return <li key={person.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                <span>{person.name}</span>
                <button type="button" disabled={!week} className="rounded border px-3 py-2"
                  onClick={() => existing ? void open(existing.id) : void generateIndividual(person)}>
                  {existing ? "Ouvrir · généré" : "Générer"}
                </button>
              </li>;
            })}
          </ul>
        </section>
      </fieldset>
      {status && <p role="status" className="text-sm text-green-700">{status}</p>}
      {error && <p role="alert" className="whitespace-pre-line text-sm text-red-700">{error}</p>}
      {!!saved.length && <section className="space-y-2">
        <h2 className="font-semibold">Digests générés cette semaine ({saved.length})</h2>
        <div className="flex flex-wrap gap-2">
          {saved.map(item => <button key={item.id} type="button" disabled={busy} onClick={() => void open(item.id)}
            className="rounded border bg-white px-3 py-2 text-sm">{item.name}</button>)}
        </div>
      </section>}
      {document && <>
        <button type="button" disabled={busy} className="rounded border bg-white px-3 py-2 text-sm" onClick={() => {
          if (!window.confirm("Régénérer et remplacer ce Digest enregistré ?")) return;
          void perform(async () => {
            const result = await api.post(endpoint, {
              user_id: document.user_id, period_start: document.period_start, regenerate: true,
            });
            setDocument(result.document);
            setStatus("Digest régénéré.");
          });
        }}>Régénérer ce Digest</button>
        <SubjectDigestDocument key={document.id} digest={document} />
      </>}
      <footer className="border-t pt-3 text-xs">
        <Link href="/admin/digest/v1" className="text-gray-500 underline">Accéder aux Digests V1</Link>
      </footer>
    </div>
  );
}
