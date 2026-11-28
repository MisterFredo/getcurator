"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

type Source = { id: string; label: string; quote: string; json_pointer: string };
type Field = { location: string; page_id: string; page_number: number; page_title: string;
  value: string; max_length: number; issues: { code: string; message: string }[]; sources: Source[] };
type Context = { production_id: string; document_artifact_id: string; review_artifact_id: string;
  corpus_sha256: string; context_sha256: string; document_title: string; language: string;
  editable: boolean; unhandled_locations: string[]; fields: Field[] };
type Proposal = { proposal_id: string; status: string; mode: string;
  replacements?: Record<string, string>; evidence_bindings?: Record<string, string[]>;
  resolution_notes?: Record<string, string>; checks?: { location: string; reason: string;
    issue_resolved: boolean; evidence_supported: boolean; scope_preserved: boolean; no_new_material_issue: boolean }[];
  error?: { message?: string } | null; queue?: { running: boolean; queued: boolean } };
const PROPOSAL_ACTIVE = ["STARTING", "queued", "in_progress", "checking"];
type Props = { productionId: string; disabled?: boolean;
  onSavingChange: (value: boolean) => void; onProgress: (productionId: string) => Promise<void>; onSaved: (productionId: string) => Promise<void> };
const BUTTON = "rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm disabled:opacity-50";
const PRIMARY = "rounded-lg bg-emerald-700 px-4 py-2 text-sm text-white disabled:opacity-50";
const errorMessage = (error: unknown) => error instanceof Error ? error.message : "Impossible de confirmer la correction.";

export default function MonthlyReviewCorrections({ productionId, disabled = false, onSavingChange, onProgress, onSaved }: Props) {
  const [context, setContext] = useState<Context | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [bindings, setBindings] = useState<Record<string, string[]>>({});
  const [reason, setReason] = useState("Correction des remarques du contrôle qualité.");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [proposing, setProposing] = useState(false);
  const [proposalLoadingError, setProposalLoadingError] = useState("");
  const [usedProposalId, setUsedProposalId] = useState<string | null>(null);
  const draftRevision = useRef(0);
  const proposalDraftRevision = useRef(0);
  const appliedProposal = useRef<string | null>(null);
  const proposalCanPrefill = useRef(false);
  const [proposalPollVersion, setProposalPollVersion] = useState(0);
  const proposeLock = useRef(false);
  const proposalShouldPoll = Boolean(proposal && PROPOSAL_ACTIVE.includes(proposal.status));
  const proposalBusy = proposing || proposalShouldPoll || proposal?.status === "SUBMISSION_UNKNOWN";
  const sequence = useRef(0);
  const requestId = useRef<string | null>(null);
  const savingLock = useRef(false);
  useEffect(() => () => { sequence.current += 1; }, []);

  async function load() {
    if (savingLock.current || disabled) return;
    const token = ++sequence.current;
    setLoading(true); setError("");
    try {
      const response: { context: Context } = await api.get(
        `/production/monthly-users/${encodeURIComponent(productionId)}/editorial-context`);
      if (token !== sequence.current) return;
      const next = response.context;
      if (next.production_id !== productionId) throw new Error("Le contexte appartient à un autre rapport.");
      const nextValues: Record<string, string> = {};
      const nextBindings: Record<string, string[]> = {};
      next.fields.forEach(field => { nextValues[field.location] = field.value; nextBindings[field.location] = []; });
      setContext(next); setValues(nextValues); setBindings(nextBindings); requestId.current = null; setProposal(null); setUsedProposalId(null); appliedProposal.current = null; draftRevision.current = 0;
    } catch (exception) { if (token === sequence.current) setError(errorMessage(exception)); }
    finally { if (token === sequence.current) setLoading(false); }
  }
  function changeText(location: string, value: string) {
    setValues(current => ({ ...current, [location]: value })); requestId.current = null; draftRevision.current += 1; appliedProposal.current = null;
  }
  function toggleSource(location: string, id: string) {
    setBindings(current => {
      const ids = current[location] || [];
      return { ...current, [location]: ids.includes(id) ? ids.filter(value => value !== id) : ids.concat(id) };
    }); requestId.current = null; draftRevision.current += 1; appliedProposal.current = null;
  }
  const ready = Boolean(context?.editable && context.fields.length && reason.trim()
    && context.fields.every(field => Boolean(values[field.location]?.trim())
      && values[field.location].trim() !== field.value.trim() && bindings[field.location]?.length));

  async function save() {
    if (!context || !ready || disabled || savingLock.current || proposalBusy) return;
    savingLock.current = true; setSaving(true); onSavingChange(true); setError("");
    const token = sequence.current;
    try {
      // Keep the same request ID/body for an unchanged draft after a network error.
      if (!requestId.current) requestId.current = crypto.randomUUID();
      await api.post(`/production/monthly-users/${encodeURIComponent(productionId)}/editorial-edits`, {
        request_id: requestId.current, document_artifact_id: context.document_artifact_id,
        review_artifact_id: context.review_artifact_id, corpus_sha256: context.corpus_sha256,
        context_sha256: context.context_sha256, replacements: values,
        evidence_bindings: bindings, reason: reason.trim(),
        ...(usedProposalId ? { proposal_artifact_id: usedProposalId } : {}),
      });
      if (token !== sequence.current) return;
      await onSaved(productionId);
    } catch (exception) {
      if (token === sequence.current) setError(`${errorMessage(exception)} Le brouillon est conservé ici. En cas de doute, rouvrez le rapport pour vérifier son historique avant de modifier la demande.`);
    } finally {
      savingLock.current = false;
      if (token === sequence.current) setSaving(false);
      onSavingChange(false);
    }
  }
  function useVerifiedProposal(value: Proposal) {
    if (!context || value.status !== "ready" || !value.replacements || !value.evidence_bindings) return;
    setValues(value.replacements); setBindings(value.evidence_bindings);
    setUsedProposalId(value.proposal_id); requestId.current = null;
    appliedProposal.current = value.proposal_id;
    draftRevision.current += 1;
  }

  async function propose() {
    if (!context?.editable || disabled || savingLock.current || proposeLock.current || proposalBusy) return;
    proposeLock.current = true; setProposing(true); setProposalLoadingError("");
    proposalDraftRevision.current = draftRevision.current;
    proposalCanPrefill.current = context.fields.every(field => values[field.location] === field.value && !(bindings[field.location] || []).length);
    const token = sequence.current;
    try {
      const response: { proposal: Proposal } = await api.post(
        `/production/monthly-users/${encodeURIComponent(productionId)}/correction-proposals`, {
          request_id: crypto.randomUUID(), document_artifact_id: context.document_artifact_id,
          review_artifact_id: context.review_artifact_id, corpus_sha256: context.corpus_sha256,
          context_sha256: context.context_sha256,
        });
      if (token !== sequence.current) return;
      setProposal(response.proposal);
      if (response.proposal.status === "ready" && proposalCanPrefill.current && draftRevision.current === proposalDraftRevision.current) useVerifiedProposal(response.proposal);
      await onProgress(productionId);
    } catch (exception) { if (token === sequence.current) setProposalLoadingError(errorMessage(exception)); }
    finally { proposeLock.current = false; if (token === sequence.current) setProposing(false); }
  }

  useEffect(() => {
    if (!proposal || !proposalShouldPoll) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const id = proposal.proposal_id;
    const token = sequence.current;
    async function pollProposal() {
      try {
        const response: { proposal: Proposal } = await api.get(
          `/production/monthly-users/${encodeURIComponent(productionId)}/correction-proposals/${encodeURIComponent(id)}`);
        if (!active || token !== sequence.current) return;
        const next = response.proposal; setProposal(next); setProposalLoadingError("");
        if (next.status === "ready" && proposalCanPrefill.current && appliedProposal.current !== next.proposal_id
            && draftRevision.current === proposalDraftRevision.current) useVerifiedProposal(next);
        if (PROPOSAL_ACTIVE.includes(next.status)) {
          if (next.queue && !next.queue.running && !next.queue.queued) {
            await api.post(`/production/monthly-users/${encodeURIComponent(productionId)}/refresh`, {});
          }
          if (active) timer = setTimeout(() => void pollProposal(), 4000);
        } else await onProgress(productionId);
      } catch (exception) {
        if (active && token === sequence.current) setProposalLoadingError(`${errorMessage(exception)} La proposition est enregistrée. Utilisez Actualiser / reprendre, puis rouvrez-la.`);
      }
    }
    timer = setTimeout(() => void pollProposal(), 1500);
    return () => { active = false; clearTimeout(timer); };
    // Keep one polling loop for this durable proposal, independently of drafts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [proposal?.proposal_id, proposalShouldPoll, proposalPollVersion]);

  async function reloadProposal() {
    if (!proposal || savingLock.current || disabled) return;
    const token = sequence.current;
    try {
      const response: { proposal: Proposal } = await api.get(
        `/production/monthly-users/${encodeURIComponent(productionId)}/correction-proposals/${encodeURIComponent(proposal.proposal_id)}`);
      if (token !== sequence.current) return;
      setProposal(response.proposal); setProposalLoadingError("");
      if (response.proposal.status === "ready" && proposalCanPrefill.current
          && appliedProposal.current !== response.proposal.proposal_id
          && draftRevision.current === proposalDraftRevision.current) useVerifiedProposal(response.proposal);
      setProposalPollVersion(value => value + 1);
      await onProgress(productionId);
    } catch (exception) { if (token === sequence.current) setProposalLoadingError(errorMessage(exception)); }
  }

  function close() {
    if (savingLock.current) return;
    sequence.current += 1; setContext(null); setError(""); requestId.current = null;
  }

  return <section className="space-y-4 rounded-lg border border-slate-200 p-4">
    <div>
      <h3 className="font-semibold text-slate-900">Relecture éditoriale</h3>
      <p className="mt-1 text-sm text-slate-600">Demandez une proposition vérifiée pour les passages signalés, puis examinez-la ou ajustez-la si nécessaire. Les autres champs restent conservés. L’enregistrement relance le contrôle qualité, sans valider le rapport directement.</p>
    </div>
    {!context && <button type="button" className={BUTTON} disabled={disabled || loading} onClick={() => void load()}>
      {loading ? "Chargement des passages…" : "Corriger les passages signalés"}
    </button>}
    {error && <p role="alert" className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">{error}</p>}
    {context && <>
      <p className="text-sm text-slate-500">{context.document_title} · {context.language.toUpperCase()}</p>
      <div className="space-y-2 rounded-lg border border-emerald-100 bg-emerald-50 p-3 text-sm">
        <button type="button" className={BUTTON} disabled={disabled || saving || proposalBusy || !context.editable} onClick={() => void propose()}>
          {proposalBusy ? "Proposition et vérification en cours…" : proposal ? "Rouvrir la proposition enregistrée" : "Proposer les corrections"}
        </button>
        {proposal && <button type="button" className={BUTTON} disabled={disabled || saving} onClick={() => void reloadProposal()}>Actualiser la proposition</button>}
        <p>Une proposition est rédigée puis contrôlée séparément avant de préremplir les textes et leurs preuves. Une seule proposition est générée pour cette version du document et de son diagnostic.</p>
        {proposal?.status === "ready" && <p className="text-emerald-900">Proposition vérifiée. Examinez les remplacements, puis enregistrez pour relancer le contrôle du rapport.</p>}
        {proposal?.status === "ready" && appliedProposal.current !== proposal.proposal_id && <button type="button" className={BUTTON} disabled={saving || disabled} onClick={() => useVerifiedProposal(proposal)}>Utiliser la proposition vérifiée dans le brouillon</button>}
        {proposal?.status === "rejected" && <div role="alert" className="text-amber-900"><p>La proposition n’a pas passé sa vérification. Aucun texte n’a été appliqué.</p>{proposal.checks?.filter(check => !check.issue_resolved || !check.evidence_supported || !check.scope_preserved || !check.no_new_material_issue).map(check => <p key={check.location}>{check.reason}</p>)}</div>}
        {(proposal?.status === "failed" || proposal?.status === "SUBMISSION_UNKNOWN") && <p role="alert" className="text-amber-900">{proposal.error?.message || "Le suivi de la proposition nécessite une vérification. Le document reste conservé."}</p>}
        {proposalLoadingError && <p role="alert" className="text-amber-900">{proposalLoadingError}</p>}
      </div>
      {!context.editable && <p role="alert" className="text-sm text-amber-800">Ce diagnostic contient des remarques hors édition de texte : {context.unhandled_locations.join(" · ")}. Aucun enregistrement partiel n’est possible.</p>}
      {context.fields.map((field, index) => <div key={field.location} className="space-y-3 rounded-lg bg-slate-50 p-4">
        <h4 className="text-sm font-semibold">Page {field.page_number} · {field.page_title}</h4>
        {field.issues.map((issue, issueIndex) => <p key={issueIndex} className="text-sm text-amber-900">{issue.message}</p>)}
        {proposal?.status === "ready" && proposal.resolution_notes?.[field.location] && <p className="text-sm text-emerald-900">Correction proposée : {proposal.resolution_notes[field.location]}</p>}
        <details><summary className="cursor-pointer text-xs text-slate-500">Texte enregistré</summary><p className="mt-2 whitespace-pre-wrap text-sm">{field.value}</p></details>
        <label htmlFor={`monthly-correction-${index}`} className="block text-sm font-medium">{proposal?.status === "ready" && appliedProposal.current === proposal.proposal_id ? "Proposition vérifiée" : "Brouillon de correction"} ({context.language.toUpperCase()})</label>
        <textarea id={`monthly-correction-${index}`} rows={5} value={values[field.location] || ""}
          maxLength={field.max_length} disabled={saving || disabled || !context.editable}
          onChange={event => changeText(field.location, event.target.value)}
          className="w-full rounded-lg border border-slate-200 bg-white p-3 text-sm" />
        <fieldset disabled={saving || disabled || !context.editable} className="space-y-2">
          <legend className="mb-2 text-sm font-medium">Preuves qui soutiennent ce texte</legend>
          {field.sources.map(source => <div key={source.id} className="rounded-lg border border-slate-200 bg-white p-3">
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1" checked={(bindings[field.location] || []).includes(source.id)} onChange={() => toggleSource(field.location, source.id)} />
              <span>{source.id} · {source.label}</span>
            </label>
            <details className="ml-6 mt-1"><summary className="cursor-pointer text-xs text-slate-500">Passage cité</summary><blockquote className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{source.quote}</blockquote></details>
          </div>)}
        </fieldset>
      </div>)}
      <label className="block text-sm font-medium">Motif conservé dans l’historique
        <input value={reason} maxLength={2000} disabled={saving || disabled} onChange={event => { setReason(event.target.value); requestId.current = null; draftRevision.current += 1; }} className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
      </label>
      {!usedProposalId && <p className="text-xs text-slate-500">Le brouillon contient le texte enregistré tant que vous ne l’avez pas modifié ou remplacé par une proposition vérifiée.</p>}
      <p className="text-xs text-slate-500">Modifiez chaque passage signalé et sélectionnez au moins une preuve par passage. Les corrections ne sont pas sauvegardées tant que vous n’avez pas enregistré.</p>
      <div className="flex flex-wrap gap-3">
        <button type="button" className={PRIMARY} disabled={!ready || saving || disabled || proposalBusy} onClick={() => void save()}>{saving ? "Enregistrement…" : "Enregistrer et relancer les contrôles"}</button>
        <button type="button" className={BUTTON} disabled={saving} onClick={close}>Fermer sans enregistrer</button>
      </div>
    </>}
  </section>;
}
