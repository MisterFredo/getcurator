// components/admin/company/CompanyIdentity.tsx

"use client";

import {
  CompanyFormData,
  CompanyType,
  Universe,
} from "@/types/company";

/* ========================================================= */

type Props = {
  company: CompanyFormData;

  setCompany: React.Dispatch<
    React.SetStateAction<CompanyFormData>
  >;

  companyTypes: CompanyType[];

  universes: Universe[];
};

/* ========================================================= */

export default function CompanyIdentity({

  company,

  setCompany,

  companyTypes,

  universes,

}: Props) {

  /* =======================================================
     TOGGLE UNIVERSE
  ======================================================= */

  function toggleUniverse(
    id: string,
  ) {

    const selected =
      company.universes.includes(id);

    setCompany((prev) => ({

      ...prev,

      universes: selected

        ? prev.universes.filter(
            (u) => u !== id
          )

        : [
            ...prev.universes,
            id,
          ],

    }));

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <section className="space-y-8">

      {/* =================================================== */}
      {/* IDENTITY */}
      {/* =================================================== */}

      <div>

        <h2 className="text-lg font-semibold">
          Identity
        </h2>

        <p className="text-sm text-gray-500">
          Main information describing the company.
        </p>

      </div>

      {/* NAME */}

      <div className="space-y-2">

        <label className="text-sm font-medium">
          Name
        </label>

        <input
          value={company.name}
          onChange={(e) =>
            setCompany((prev) => ({

              ...prev,

              name:
                e.target.value,

            }))
          }
          className="w-full border rounded px-3 py-2"
          placeholder="Company name"
        />

      </div>

      {/* TYPE */}

      <div className="space-y-2">

        <label className="text-sm font-medium">
          Type
        </label>

        <select
          value={company.type}
          onChange={(e) =>
            setCompany((prev) => ({

              ...prev,

              type:
                e.target.value,

            }))
          }
          className="w-full border rounded px-3 py-2"
        >

          <option value="">
            —
          </option>

          {companyTypes.map((type) => (

            <option
              key={type.id_type}
              value={type.id_type}
            >
              {type.label}
            </option>

          ))}

        </select>

      </div>

      {/* =================================================== */}
      {/* CLASSIFICATION */}
      {/* =================================================== */}

      <div className="space-y-4">

        <div>

          <h2 className="text-lg font-semibold">
            Classification
          </h2>

          <p className="text-sm text-gray-500">
            Select the universes associated with this company.
          </p>

        </div>

        <div className="flex flex-wrap gap-2">

          {universes.map((u) => {

            const selected =
              company.universes.includes(
                u.id_universe
              );

            return (

              <button
                key={u.id_universe}
                type="button"
                onClick={() =>
                  toggleUniverse(
                    u.id_universe
                  )
                }
                className={`
                  px-3 py-1 rounded border transition
                  ${
                    selected
                      ? "bg-ratecard-blue text-white border-ratecard-blue"
                      : "bg-white hover:bg-gray-50"
                  }
                `}
              >
                {u.label}
              </button>

            );

          })}

        </div>

      </div>

      {/* =================================================== */}
      {/* LINKS */}
      {/* =================================================== */}

      <div className="space-y-4">

        <div>

          <h2 className="text-lg font-semibold">
            External links
          </h2>

          <p className="text-sm text-gray-500">
            Public resources associated with the company.
          </p>

        </div>

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Website
          </label>

          <input
            value={company.website_url}
            onChange={(e) =>
              setCompany((prev) => ({

                ...prev,

                website_url:
                  e.target.value,

              }))
            }
            className="w-full border rounded px-3 py-2"
            placeholder="https://..."
          />

        </div>

        <div className="space-y-2">

          <label className="text-sm font-medium">
            LinkedIn
          </label>

          <input
            value={company.linkedin_url}
            onChange={(e) =>
              setCompany((prev) => ({

                ...prev,

                linkedin_url:
                  e.target.value,

              }))
            }
            className="w-full border rounded px-3 py-2"
            placeholder="https://linkedin.com/company/..."
          />

        </div>

      </div>

      {/* =================================================== */}
      {/* SETTINGS */}
      {/* =================================================== */}

      <div className="space-y-4">

        <h2 className="text-lg font-semibold">
          Settings
        </h2>

        <label className="flex items-center gap-3">

          <input
            type="checkbox"
            checked={company.is_partner}
            onChange={(e) =>
              setCompany((prev) => ({

                ...prev,

                is_partner:
                  e.target.checked,

              }))
            }
          />

          <span>
            Partner company
          </span>

        </label>

      </div>

    </section>

  );

}
