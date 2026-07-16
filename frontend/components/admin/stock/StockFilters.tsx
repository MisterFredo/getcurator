"use client";

type SourceItem = {
  id_source: string;
  label: string;
};

type CompanyItem = {
  id_company: string;
  name: string;
};

export default function StockFilters({
  sources,
  companies,
  status,
  sourceId,
  importType,
  primaryCompanyId,
  total,
  onStatusChange,
  onSourceChange,
  onImportTypeChange,
  onPrimaryCompanyChange,
}: {
  sources: SourceItem[];
  companies: CompanyItem[];
  status: string;
  sourceId: string;
  importType: string;
  primaryCompanyId: string;
  total: number;
  onStatusChange: (v: string) => void;
  onSourceChange: (v: string) => void;
  onImportTypeChange: (v: string) => void;
  onPrimaryCompanyChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-4 items-center">

      {/* STATUS */}
      <select
        value={status}
        onChange={(e) => onStatusChange(e.target.value)}
        className="border rounded p-2 text-sm"
      >
        <option value="">Tous statuts</option>
        <option value="ERROR">Erreur</option>
        <option value="STORED">Stored</option>
        <option value="PROCESSING">Processing</option>
        <option value="PROCESSED">Processed</option>
      </select>

      {/* SOURCE */}
      <select
        value={sourceId}
        onChange={(e) => onSourceChange(e.target.value)}
        className="border rounded p-2 text-sm"
      >
        <option value="">Toutes sources</option>

        {sources.map((s) => (
          <option
            key={s.id_source}
            value={s.id_source}
          >
            {s.label}
          </option>
        ))}
      </select>

      {/* IMPORT TYPE */}
      <select
        value={importType}
        onChange={(e) => onImportTypeChange(e.target.value)}
        className="border rounded p-2 text-sm"
      >
        <option value="">Tous imports</option>
        <option value="FILE">Fichier</option>
        <option value="URL">URL</option>
      </select>

      {/* PRIMARY COMPANY */}
      <select
        value={primaryCompanyId}
        onChange={(e) => onPrimaryCompanyChange(e.target.value)}
        className="border rounded p-2 text-sm"
      >
        <option value="">
          Toutes primary companies
        </option>

        {companies.map((c) => (
          <option
            key={c.id_company}
            value={c.id_company}
          >
            {c.name}
          </option>
        ))}
      </select>

      {/* TOTAL */}
      <div className="ml-auto text-sm text-gray-600">
        {total} résultat(s)
      </div>

    </div>
  );
}
