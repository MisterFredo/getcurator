"use client";

type Props = {
  topics: string[];
  companies: string[];
  types: string[];

  selectedTopics: string[];
  selectedCompanies: string[];
  selectedTypes: string[];

  onChangeTopics: (v: string[]) => void;
  onChangeCompanies: (v: string[]) => void;
  onChangeTypes: (v: string[]) => void;

  onSearch: () => void;
  loading: boolean;
};

export default function DigestFilters({
  topics,
  companies,
  types,
  selectedTopics,
  selectedCompanies,
  selectedTypes,
  onChangeTopics,
  onChangeCompanies,
  onChangeTypes,
  onSearch,
  loading,
}: Props) {
  function toggle(
    value: string,
    list: string[],
    setter: (v: string[]) => void
  ) {
    if (list.includes(value)) {
      setter(list.filter((x) => x !== value));
    } else {
      setter([...list, value]);
    }
  }

  return (
    <section className="space-y-6 border rounded-xl bg-white p-6">
      <h2 className="text-sm font-semibold">
        Moteur éditorial
      </h2>

      <div className="grid grid-cols-3 gap-8">

        {/* TOPICS */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-gray-500 uppercase">
            Topics
          </div>
          {topics.map((t) => (
            <label key={t} className="flex gap-2 text-sm">
              <input
                type="checkbox"
                checked={selectedTopics.includes(t)}
                onChange={() =>
                  toggle(t, selectedTopics, onChangeTopics)
                }
              />
              {t}
            </label>
          ))}
        </div>

        {/* COMPANIES */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-gray-500 uppercase">
            Sociétés
          </div>
          {companies.map((c) => (
            <label key={c} className="flex gap-2 text-sm">
              <input
                type="checkbox"
                checked={selectedCompanies.includes(c)}
                onChange={() =>
                  toggle(c, selectedCompanies, onChangeCompanies)
                }
              />
              {c}
            </label>
          ))}
        </div>

        {/* TYPES */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-gray-500 uppercase">
            Types
          </div>
          {types.map((t) => (
            <label key={t} className="flex gap-2 text-sm">
              <input
                type="checkbox"
                checked={selectedTypes.includes(t)}
                onChange={() =>
                  toggle(t, selectedTypes, onChangeTypes)
                }
              />
              {t}
            </label>
          ))}
        </div>

      </div>

      <button
        onClick={onSearch}
        disabled={loading}
        className="bg-black text-white text-sm px-4 py-2 rounded"
      >
        {loading ? "Recherche…" : "Rechercher"}
      </button>
    </section>
  );
}
