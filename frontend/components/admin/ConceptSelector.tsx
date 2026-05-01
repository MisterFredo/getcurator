"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import SearchableMultiSelect, {
  SelectOption,
} from "@/components/ui/SearchableMultiSelect";

/* ---------------------------------------------------------
   TYPES
--------------------------------------------------------- */
export type Concept = {
  id_concept: string;
  label: string;
};

type Props = {
  values: Concept[];
  onChange: (concepts: Concept[]) => void;
};

type ConceptApi = {
  id_concept: string;
  label: string;
};

/* ---------------------------------------------------------
   COMPONENT
--------------------------------------------------------- */
export default function ConceptSelector({
  values,
  onChange,
}: Props) {

  const [options, setOptions] = useState<SelectOption[]>([]);
  const [loading, setLoading] = useState(true);

  /* ---------------------------------------------------------
     LOAD ALL CONCEPTS
  --------------------------------------------------------- */
  useEffect(() => {

    async function load() {

      try {

        setLoading(true);

        const res = await api.get("/concept/list");

        const concepts: ConceptApi[] = res?.concepts || [];

        const mappedOptions: SelectOption[] = concepts.map((c) => ({
          id: c.id_concept,
          label: c.label,
        }));

        setOptions(mappedOptions);

      } catch (e) {

        console.error("Erreur chargement concepts", e);
        setOptions([]);

      } finally {

        setLoading(false);

      }

    }

    load();

  }, []);

  /* ---------------------------------------------------------
     HANDLE CHANGE
  --------------------------------------------------------- */
  function handleChange(selected: SelectOption[]) {

    if (!selected || selected.length === 0) {
      onChange([]);
      return;
    }

    const mapped: Concept[] = selected.map((item) => ({
      id_concept: item.id,
      label: item.label,
    }));

    onChange(mapped);
  }

  /* ---------------------------------------------------------
     RENDER
  --------------------------------------------------------- */

  if (loading) {
    return (
      <div className="text-sm text-gray-500">
        Chargement des concepts…
      </div>
    );
  }

  return (
    <SearchableMultiSelect
      label="Axes d’analyse"
      placeholder="Rechercher un ou plusieurs axes…"
      options={options}
      values={values.map((v) => ({
        id: v.id_concept,
        label: v.label,
      }))}
      onChange={handleChange}
    />
  );
}
