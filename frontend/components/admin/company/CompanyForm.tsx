"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { EMPTY_COMPANY } from "@/types/company";
import type { CompanyFormData, CompanyType, Universe } from "@/types/company";
import type { WatchCompany } from "@/lib/companyWatch";
import CompanyIdentity from "./CompanyIdentity";
import CompanyKnowledge from "./CompanyKnowledge";
import CompanyAliases from "./CompanyAliases";
import CompanyVisuals from "./CompanyVisuals";
import CompanyWatchManager from "./CompanyWatchManager";

type Props = {
  mode: "create" | "edit";
  companyId?: string;
};

export default function CompanyForm({ mode, companyId: initialCompanyId }: Props) {
  const [company, setCompany] = useState<CompanyFormData>(EMPTY_COMPANY);
  const [companyId, setCompanyId] = useState<string | null>(initialCompanyId ?? null);
  const [companyTypes, setCompanyTypes] = useState<CompanyType[]>([]);
  const [availableUniverses, setAvailableUniverses] = useState<Universe[]>([]);
  const [logoFilename, setLogoFilename] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedWatchCompany, setSavedWatchCompany] = useState<WatchCompany | null>(null);
  const [loadError, setLoadError] = useState("");
  const [notice, setNotice] = useState("");
  const [saveError, setSaveError] = useState("");
  const [mentionWatchEnabled, setMentionWatchEnabled] = useState(false);
  const [mentionWatchLoaded, setMentionWatchLoaded] = useState(mode === "create" && !initialCompanyId);
  const [mentionWatchLoading, setMentionWatchLoading] = useState(false);
  const [mentionWatchError, setMentionWatchError] = useState("");
  const mentionWatchSaved = useRef<boolean | null>(mode === "create" && !initialCompanyId ? false : null);
  const mentionLoadSequence = useRef(0);
  const savingRef = useRef(false);
  const loadSequence = useRef(0);
  // Dès qu'un identifiant a été obtenu, les sauvegardes suivantes sont des mises à jour.
  const isCreate = mode === "create" && !companyId;

  const loadCompany = useCallback(async (id: string) => {
    const sequence = ++loadSequence.current;
    const c = await api.get(`/company/${encodeURIComponent(id)}`);
    if (sequence !== loadSequence.current) return;
    setCompany({
      name: c.name ?? "",
      type: c.type ?? "",
      description: c.description ?? "",
      wiki_content: c.wiki_content ?? "",
      linkedin_url: c.linkedin_url ?? "",
      website_url: c.website_url ?? "",
      is_partner: c.is_partner ?? false,
      universes: c.universes ?? [],
      aliases: c.aliases ?? [],
    });
    setLogoFilename(c.media_logo_rectangle_id ?? null);
    // Utiliser les URL enregistrées, pas les modifications non sauvegardées de la fiche.
    setSavedWatchCompany({
      id_company: id,
      name: c.name ?? "",
      website_url: c.website_url ?? null,
      linkedin_url: c.linkedin_url ?? null,
    });
  }, []);

  // Kept apart from identity rereads: an alias/logo update must not reset an
  // unsaved eligibility choice. The same API is used by the Companies list.
  const loadMentionWatch = useCallback(async (id: string) => {
    const sequence = ++mentionLoadSequence.current;
    setMentionWatchLoading(true);
    setMentionWatchError("");
    try {
      const result = await api.get(`/company/${encodeURIComponent(id)}/mention-watch`);
      if (typeof result.is_enabled !== "boolean") throw new Error("Réponse de configuration invalide");
      if (sequence !== mentionLoadSequence.current) return;
      mentionWatchSaved.current = result.is_enabled;
      setMentionWatchEnabled(result.is_enabled);
      setMentionWatchLoaded(true);
    } catch (error) {
      console.error(error);
      if (sequence !== mentionLoadSequence.current) return;
      setMentionWatchLoaded(false);
      setMentionWatchError(error instanceof Error ? error.message : "Erreur chargement de la veille Mentions.");
    } finally {
      if (sequence === mentionLoadSequence.current) setMentionWatchLoading(false);
    }
  }, []);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setLoadError("");
      const [typesRes, universesRes] = await Promise.all([
        api.get("/company/types"), api.get("/universe/list"),
      ]);
      setCompanyTypes(typesRes.types ?? []);
      setAvailableUniverses(universesRes.universes ?? []);
      if (initialCompanyId) await Promise.all([loadCompany(initialCompanyId), loadMentionWatch(initialCompanyId)]);
    } catch (error) {
      console.error(error);
      setLoadError("Erreur chargement société.");
    } finally {
      setLoading(false);
    }
  }, [initialCompanyId, loadCompany, loadMentionWatch]);

  useEffect(() => {
    setCompanyId(initialCompanyId ?? null);
    setSavedWatchCompany(null);
    setNotice("");
    setSaveError("");
    setMentionWatchEnabled(false);
    setMentionWatchError("");
    setMentionWatchLoaded(!initialCompanyId);
    mentionWatchSaved.current = initialCompanyId ? null : false;
    setCompany(EMPTY_COMPANY);
    load();
    return () => { loadSequence.current += 1; mentionLoadSequence.current += 1; };
  }, [initialCompanyId, load]);

  function getCreatePayload() {
    return {
      name: company.name,
      type: company.type || null,
      description: company.description || null,
      linkedin_url: company.linkedin_url || null,
      website_url: company.website_url || null,
      is_partner: company.is_partner,
      universes: company.universes,
      aliases: company.aliases.map(alias => alias.alias),
    };
  }
  function getUpdatePayload() {
    return { ...getCreatePayload(), wiki_content: company.wiki_content || null };
  }

  async function handleSave() {
    if (savingRef.current) return;
    savingRef.current = true;
    setSaving(true);
    setNotice("");
    setSaveError("");
    const desiredMentionWatch = mentionWatchEnabled;
    let stage: "identity" | "mentions" | "reload" = "identity";
    let savedId = companyId;
    let persisted = false;
    try {
      if (isCreate) {
        const response = await api.post("/company/create", getCreatePayload());
        if (!response.id_company) throw new Error("Missing company id.");
        savedId = response.id_company as string;
        setCompanyId(savedId);
      } else {
        if (!savedId) throw new Error("Missing company id.");
        await api.put(`/company/update/${encodeURIComponent(savedId)}`, getUpdatePayload());
      }
      persisted = true;
      // Rendre immédiatement la section accessible après une création réussie,
      // même si la relecture du backend échoue ensuite.
      setSavedWatchCompany({ id_company: savedId!, name: company.name,
        website_url: company.website_url || null, linkedin_url: company.linkedin_url || null });
      if (mentionWatchLoaded && mentionWatchSaved.current !== desiredMentionWatch) {
        stage = "mentions";
        const config = await api.put(`/company/${encodeURIComponent(savedId!)}/mention-watch`, {
          is_enabled: desiredMentionWatch,
        });
        if (config.is_enabled !== desiredMentionWatch) throw new Error("Le réglage de veille Mentions n’a pas été confirmé.");
        mentionWatchSaved.current = config.is_enabled;
        setMentionWatchError("");
      }
      stage = "reload";
      await loadCompany(savedId!);
      setNotice(isCreate ? "Société créée. Vous pouvez maintenant ajouter ses points de collecte." : "Société enregistrée.");
    } catch (error) {
      console.error(error);
      if (persisted && stage === "mentions") mentionWatchSaved.current = null;
      const detail = error instanceof Error ? error.message : "Erreur inconnue";
      setSaveError(persisted
        ? stage === "mentions"
          ? `Société enregistrée. Le réglage de veille Mentions n’a pas été confirmé : ${detail}. Votre choix est conservé ; réessayez Save changes sans recréer la société.`
          : `Société enregistrée, mais sa relecture a échoué : ${detail}. Vous pouvez réessayer sans recréer la société.`
        : `Erreur sauvegarde société : ${detail}`);
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  }

  async function handleAddAlias(alias: string) {
    if (!companyId) {
      setCompany(previous => ({ ...previous, aliases: [...previous.aliases, { alias }] }));
      return;
    }
    await api.post(`/company/${encodeURIComponent(companyId)}/alias`, { alias });
    await loadCompany(companyId);
  }
  async function handleDeleteAlias(alias: string) {
    if (!companyId) {
      setCompany(previous => ({ ...previous, aliases: previous.aliases.filter(item => item.alias !== alias) }));
      return;
    }
    await api.delete(`/company/${encodeURIComponent(companyId)}/alias?alias=${encodeURIComponent(alias)}`);
    await loadCompany(companyId);
  }
  async function handleVisualUpdated() {
    if (companyId) await loadCompany(companyId);
  }

  if (loading) return <div className="text-gray-500">Chargement...</div>;
  if (loadError) return <div role="alert" className="space-y-3 text-red-700">
    <p>{loadError}</p><button type="button" onClick={load} className="underline">Réessayer</button>
  </div>;

  return (
    <div className="space-y-10">
      <CompanyIdentity company={company} setCompany={setCompany}
        companyTypes={companyTypes} universes={availableUniverses} />
      <CompanyKnowledge company={company} setCompany={setCompany} />
      <section className="border rounded bg-white p-5 space-y-3" aria-label="Veille Mentions">
        <h2 className="text-xl font-semibold text-ratecard-blue">Veille Mentions</h2>
        <p className="text-sm text-gray-500">Rendre cette société éligible aux collectes de mentions dans Google Actualités.</p>
        <label className="flex items-center gap-3">
          <input type="checkbox" checked={mentionWatchEnabled}
            disabled={saving || mentionWatchLoading || !mentionWatchLoaded}
            onChange={event => setMentionWatchEnabled(event.target.checked)} />
          <span>Activer la veille Mentions pour cette société</span>
        </label>
        {mentionWatchLoading && <p className="text-sm text-gray-500">Chargement du réglage…</p>}
        {mentionWatchError && <div role="alert" className="text-sm text-red-700 space-y-2">
          <p>Le réglage de veille Mentions n’a pas pu être chargé : {mentionWatchError}</p>
          <p>La sauvegarde de la fiche société ne modifiera pas ce réglage tant qu’il n’aura pas été chargé.</p>
          {companyId && <button type="button" className="underline" disabled={mentionWatchLoading || saving}
            onClick={() => loadMentionWatch(companyId)}>Réessayer le chargement</button>}
        </div>}
        {!mentionWatchLoading && mentionWatchLoaded && mentionWatchSaved.current !== mentionWatchEnabled &&
          <p className="text-sm text-amber-800">Modification à enregistrer avec le formulaire.</p>}
        <p className="text-xs text-gray-500">{isCreate
          ? "Le choix sera enregistré après la création de la société."
          : "L’activation ou la suspension sera enregistrée avec Save changes."} L’activation ne lance pas de collecte automatique. Les historiques sont conservés.</p>
      </section>
      <CompanyAliases aliases={company.aliases} onAdd={handleAddAlias} onDelete={handleDeleteAlias} />
      <CompanyVisuals companyId={companyId} logoFilename={logoFilename} onUpdated={handleVisualUpdated} />
      {saveError && <p role="alert" className="text-red-700 bg-red-50 border rounded p-3">{saveError}</p>}
      {notice && <p role="status" className="text-green-800 bg-green-50 border rounded p-3">{notice}</p>}
      <div className="flex justify-end pt-8 border-t">
        <button type="button" onClick={handleSave} disabled={saving}
          className="bg-ratecard-blue text-white px-6 py-3 rounded disabled:opacity-50">
          {saving ? "Saving..." : isCreate ? "Create company" : "Save changes"}
        </button>
      </div>
      {companyId && savedWatchCompany ? (
        <section className="pt-8 border-t">
          <CompanyWatchManager key={companyId} company={savedWatchCompany} />
        </section>
      ) : (
        <section className="border rounded bg-white p-5 space-y-2">
          <h2 className="text-xl font-semibold text-ratecard-blue">Veille Corpo</h2>
          <p className="text-gray-500">Enregistrez la société pour ajouter ses pages, comptes et newsletters à suivre.</p>
        </section>
      )}
    </div>
  );
}
