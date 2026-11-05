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

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setLoadError("");
      const [typesRes, universesRes] = await Promise.all([
        api.get("/company/types"), api.get("/universe/list"),
      ]);
      setCompanyTypes(typesRes.types ?? []);
      setAvailableUniverses(universesRes.universes ?? []);
      if (initialCompanyId) await loadCompany(initialCompanyId);
    } catch (error) {
      console.error(error);
      setLoadError("Erreur chargement société.");
    } finally {
      setLoading(false);
    }
  }, [initialCompanyId, loadCompany]);

  useEffect(() => {
    setCompanyId(initialCompanyId ?? null);
    setSavedWatchCompany(null);
    setNotice("");
    setCompany(EMPTY_COMPANY);
    load();
    return () => { loadSequence.current += 1; };
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
      await loadCompany(savedId!);
      setNotice(isCreate ? "Société créée. Vous pouvez maintenant ajouter ses points de collecte." : "Société enregistrée.");
    } catch (error) {
      console.error(error);
      alert(persisted
        ? "Société enregistrée, mais sa relecture a échoué. Vous pouvez réessayer sans recréer la société."
        : "Erreur sauvegarde société.");
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
      <CompanyAliases aliases={company.aliases} onAdd={handleAddAlias} onDelete={handleDeleteAlias} />
      <CompanyVisuals companyId={companyId} logoFilename={logoFilename} onUpdated={handleVisualUpdated} />
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
