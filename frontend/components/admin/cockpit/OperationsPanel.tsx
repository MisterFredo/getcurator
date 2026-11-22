"use client";

import { Play } from "lucide-react";
import { useCockpitOperations } from "@/hooks/useCockpitOperations";

type Operation = { id: string; label: string; description: string };
const groups: { title: string; operations: Operation[] }[] = [
  { title: "Production", operations: [
    { id: "publish-drafts", label: "Publish Drafts", description: "Publier tous les contenus en brouillon." },
    { id: "translate-missing", label: "Translate Missing", description: "Compléter les traductions françaises manquantes." },
    { id: "restart-destock", label: "Restart Destock", description: "Réactiver les RAW STOPPED du périmètre prévu par le service existant." },
  ] },
  { title: "Digests", operations: [
    { id: "generate-user-digests-v2", label: "Générer les Digests Users", description: "Générer les V2 de la semaine précédente pour les utilisateurs éligibles. Garder cette page ouverte pendant le traitement." },
  ] },
  { title: "Touch", operations: [
    { id: "initialize-touch-histories", label: "Initialize Touch Histories", description: "Préparer les trois derniers mois complets pour revue." },
    { id: "prepare-latest-touch-editions", label: "Prepare Latest Touch Editions", description: "Préparer le dernier mois complet ; préserver les éditions existantes." },
  ] },
  { title: "Maintenance", operations: [
    { id: "rebuild-company", label: "Rebuild Company", description: "Compléter les relations Content → Company." },
    { id: "rebuild-solution", label: "Rebuild Solution", description: "Compléter les relations Content → Solution." },
    { id: "populate-content-enriched", label: "Populate CONTENT_ENRICHED", description: "Reconstruire la table enrichie." },
    { id: "matching-dismiss", label: "Matching Dismiss", description: "Rejeter tous les alias non rapprochés." },
  ] },
  { title: "Environment", operations: [
    { id: "backup", label: "Backup Production", description: "Copier PROD vers BACKUP." },
    { id: "sync-dev", label: "Sync Development", description: "Copier PROD vers DEV." },
  ] },
];

export default function OperationsPanel({ section }: { section?: "production" | "maintenance" }) {
  const selected = groups.filter(group => {
    const maintenance = group.title === "Maintenance" || group.title === "Environment";
    return !section || (section === "maintenance" ? maintenance : !maintenance);
  });
  const { loading, success, error, run } = useCockpitOperations();
  return (
    <section className="space-y-5 rounded-xl border bg-white p-6">
      <h2 className="text-xl font-semibold">{section === "production" ? "Production" : section === "maintenance" ? "Maintenance" : "Opérations"}</h2>
      {success && <p role="status" className="text-green-700">{success}</p>}
      {error && <p role="alert" className="text-red-700">{error}</p>}
      {selected.map(group => <div key={group.title}>
        <h3 className="mb-3 font-semibold">{group.title}</h3>
        <div className="space-y-3">{group.operations.map(operation => <div key={operation.id}
          className="flex flex-wrap items-center justify-between gap-3 rounded border p-4">
          <div><strong>{operation.label}</strong><p className="text-sm text-gray-500">{operation.description}</p></div>
          <button disabled={loading} onClick={() => { void run(operation.id).catch(() => {}); }}
            className="inline-flex items-center gap-2 rounded bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50">
            <Play size={16} />Run
          </button>
        </div>)}</div>
      </div>)}
    </section>
  );
}
