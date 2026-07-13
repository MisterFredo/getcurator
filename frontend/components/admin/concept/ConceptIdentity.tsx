"use client";

/* ========================================================= */

type Props = {
  label: string;
  setLabel: (value: string) => void;

  description: string;
  setDescription: (value: string) => void;
};

/* ========================================================= */

export default function ConceptIdentity({

  label,
  setLabel,

  description,
  setDescription,

}: Props) {

  return (

    <section className="space-y-8">

      <div>

        <h2 className="text-lg font-semibold">
          Identity
        </h2>

        <p className="text-sm text-gray-500">
          Main information describing the concept.
        </p>

      </div>

      <div className="space-y-2">

        <label className="text-sm font-medium">
          Label
        </label>

        <input
          value={label}
          onChange={(e) =>
            setLabel(e.target.value)
          }
          className="w-full border rounded px-3 py-2"
          placeholder="Concept label"
        />

      </div>

      <div className="space-y-2">

        <label className="text-sm font-medium">
          Description
        </label>

        <textarea
          rows={5}
          value={description}
          onChange={(e) =>
            setDescription(
              e.target.value
            )
          }
          className="w-full border rounded px-3 py-2"
          placeholder="Description..."
        />

      </div>

    </section>

  );

}
