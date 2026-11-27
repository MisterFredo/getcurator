export type PdfExportContext = {
  subject: string;
  language: "fr" | "en";
  periodStart: string;
  periodEnd: string;
};

function validDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

export function pdfSubject(value: string): string {
  return value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[œŒ]/g, c => c === "œ" ? "oe" : "OE")
    .replace(/[^A-Za-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 140).replace(/-+$/g, "");
}

export function productionPdfFilename(context: PdfExportContext): string | null {
  const subject = pdfSubject(context.subject);
  const { periodStart: start, periodEnd: end } = context;
  if (!subject || !validDate(start) || !validDate(end) || start > end) return null;
  if (!["fr", "en"].includes(context.language)) return null;
  const lastDay = new Date(`${start}T00:00:00Z`);
  lastDay.setUTCMonth(lastDay.getUTCMonth() + 1, 0);
  const month = start.endsWith("-01") && end === lastDay.toISOString().slice(0, 10);
  const period = month ? start.slice(0, 7) : `${start}_to_${end}`;
  return `GetCurator_${subject}_${period}_${context.language.toUpperCase()}_Report.pdf`;
}

export function reportPeriodForExport(reports: { payload: {
  period_start?: string | null; period_end?: string | null;
  source_type?: string; monthly_period_role?: string;
} }[]): Pick<PdfExportContext, "periodStart" | "periodEnd"> {
  const empty = { periodStart: "", periodEnd: "" };
  // A comparative Monthly exports the current period, not the reference month.
  const current = reports.filter(r => r.payload.monthly_period_role === "CURRENT");
  const selected = (current.length ? current : reports).filter(r => r.payload.source_type !== "MONTHLY_REFERENCE");
  if (!selected.length) return empty;
  const ranges = selected.map(({ payload }) => {
    const start = (payload.period_start || "").slice(0, 10);
    let end = (payload.period_end || "").slice(0, 10);
    if (payload.source_type === "DIGEST_SUBJECT" && validDate(end)) {
      const exclusive = new Date(`${end}T00:00:00Z`);
      exclusive.setUTCDate(exclusive.getUTCDate() - 1);
      end = exclusive.toISOString().slice(0, 10);
    }
    return { start, end };
  });
  if (ranges.some(r => !validDate(r.start) || !validDate(r.end) || r.start > r.end)) return empty;
  return { periodStart: ranges.map(r => r.start).sort()[0], periodEnd: ranges.map(r => r.end).sort().reverse()[0] };
}
