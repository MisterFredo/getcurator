"use client";

import { useEffect, useRef, useState } from "react";
import { getCorpoLibraryDocument } from "@/lib/companyWatch";
import type { CorpoLibraryDocument, CorpoLibraryDetail, CorpoLibraryFilters, WatchCompany } from "@/lib/companyWatch";

import {api} from "@/lib/api";
type EditorialFields = {
  document_type?: string;
  editorial_status?: string;
  editorial_reason?: string;
  qualification_verdict?: string | null;
  qualification_type?: string | null;
  qualification_motif?: string | null;
};

type QualificationCount = {
  role: "EMPLOYEE" | "CORPORATE";
  verdict: string | null;
  post_type: string | null;
  total: number;
};

const postTypes: Record<string, string> = {
  EVENEMENT: "Événement",
  THOUGHT_LEADERSHIP: "Thought leadership",
  PRODUIT_OU_PARTENARIAT: "Produit ou partenariat",
  CAS_CLIENT_OU_RETOUR_EXPERIENCE: "Cas client ou retour d’expérience",
  OFFRE_EMPLOI: "Offre d’emploi",
  VIE_ENTREPRISE: "Vie d’entreprise",
  PERSONNEL: "Personnel",
  AUTRE: "Autre",
  INDETERMINE: "Indéterminé",
};

const verdictLabels: Record<string, string> = {
  SIGNAL_SOCIETE: "Go · Signal société",
  PRISE_DE_PAROLE_METIER: "Go · Prise de parole métier",
  BRUIT: "No go",
  A_VERIFIER: "À vérifier",
  CORPORATE: "Qualifié",
};

const isGo = (verdict: string | null) =>
  verdict === "SIGNAL_SOCIETE" || verdict === "PRISE_DE_PAROLE_METIER";

function qualificationLabel(post: EditorialFields) {
  const verdict = post.qualification_verdict;
  const type = post.qualification_type;
  return [
    verdict ? (verdictLabels[verdict] ?? verdict) : "En attente de qualification",
    type ? (postTypes[type] ?? type) : null,
  ].filter(Boolean).join(" · ");
}

function QualificationSummary({ rows }: { rows: QualificationCount[] }) {
  if (!rows.length) return null;

  const employee = rows.filter(row => row.role === "EMPLOYEE");
  const corporate = rows.filter(row => row.role === "CORPORATE");
  const total = (items: QualificationCount[]) => items.reduce((sum, row) => sum + row.total, 0);

  function typeCounts(items: QualificationCount[]) {
    const counts = new Map<string, number>();
    for (const item of items) {
      const type = item.post_type ?? "INDETERMINE";
      counts.set(type, (counts.get(type) ?? 0) + item.total);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  }

  function breakdown(items: QualificationCount[]) {
    const counts = typeCounts(items);
    return counts.length > 0 && (
      <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
        {counts.map(([type, count]) => <li key={type}>{postTypes[type] ?? type} <strong>{count}</strong></li>)}
      </ul>
    );
  }

  const go = employee.filter(row => isGo(row.verdict));
  const corporateQualified = corporate.filter(row => row.verdict !== null);

  return (
    <section className="space-y-4 rounded border bg-white p-4" aria-label="Bilan des qualifications LinkedIn">
      <div>
        <h2 className="font-semibold">Qualifications LinkedIn</h2>
        <p className="text-sm text-gray-500">Bilan de la sélection avant les filtres Verdict et Type principal.</p>
      </div>
      {employee.length > 0 && <div>
        <h3 className="font-medium">Salariés</h3>
        <p className="text-sm text-gray-600">
          {total(employee.filter(row => row.verdict !== null))} qualifiés sur {total(employee)}
        </p>
        <dl className="my-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
          {[
