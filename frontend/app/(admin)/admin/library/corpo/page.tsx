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

function QualificationTypes({ rows }: { rows: QualificationCount[] }) {
  const counts = new Map<string, number>();
  for (const row of rows) {
    const type = row.post_type ?? "INDETERMINE";
    counts.set(type, (counts.get(type) ?? 0) + row.total);
  }
  const types = Array.from(counts.entries());
  types.sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  if (types.length === 0) return null;

  const items = types.map(([type, count]) => (
    <li key={type}>{postTypes[type] ?? type} <strong>{count}</strong></li>
  ));
  return <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">{items}</ul>;
}

function QualificationSummary({ rows }: { rows: QualificationCount[] }) {
  if (rows.length === 0) return null;

  const employee = rows.filter(row => row.role === "EMPLOYEE");
  const corporate = rows.filter(row => row.role === "CORPORATE");
  const total = (items: QualificationCount[]) => items.reduce((sum, row) => sum + row.total, 0);
  const go = employee.filter(row => isGo(row.verdict));
  const employeeTotal = total(employee);
  const employeePending = total(employee.filter(row => row.verdict === null));
  const corporateTotal = total(corporate);
  const corporateQualified = corporate.filter(row => row.verdict !== null);
  const corporateDone = total(corporateQualified);

  const employeeCounts = [
    { label: "Go", count: total(go) },
    { label: "No go", count: total(employee.filter(row => row.verdict === "BRUIT")) },
    { label: "À vérifier", count: total(employee.filter(row => row.verdict === "A_VERIFIER")) },
    { label: "En attente", count: employeePending },
  ];
  const cards = employeeCounts.map(({ label, count }) => (
    <div key={label} className="rounded bg-gray-50 p-2">
      <dt>{label}</dt>
      <dd className="font-semibold">{count}</dd>
    </div>
  ));
