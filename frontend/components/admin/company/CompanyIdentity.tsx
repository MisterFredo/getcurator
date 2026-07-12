// components/admin/company/CompanyIdentity.tsx

"use client";

type Universe = {
  id_universe: string;
  label: string;
};

type Props = {
  name: string;
  setName: (value: string) => void;

  type: string;
  setType: (value: string) => void;

  universes: Universe[];

  selectedUniverses: string[];
  setSelectedUniverses: (
    values: string[]
  ) => void;

  isPartner: boolean;
  setIsPartner: (
    value: boolean
  ) => void;

  websiteUrl: string;
  setWebsiteUrl: (
    value: string
  ) => void;

  linkedinUrl: string;
  setLinkedinUrl: (
    value: string
  ) => void;
};

export default function CompanyIdentity({

  name,
  setName,

  type,
  setType,

  universes,

  selectedUniverses,
  setSelectedUniverses,

  isPartner,
  setIsPartner,

  websiteUrl,
  setWebsiteUrl,

  linkedinUrl,
  setLinkedinUrl,

}: Props) {

  function toggleUniverse(
    id: string,
  ) {

    if (
      selectedUniverses.includes(id)
    ) {

      setSelectedUniverses(
        selectedUniverses.filter(
          (u) => u !== id
        )
      );

      return;

    }

    setSelectedUniverses([
      ...selectedUniverses,
      id,
    ]);

  }

  return (

    <div className="space-y-8">

      {/* ===================================================== */}
      {/* IDENTITY */}
      {/* ===================================================== */}

      <section className="space-y-6">

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
            value={name}
            onChange={(e) =>
              setName(
                e.target.value
              )
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

          <input
            value={type}
            onChange={(e) =>
              setType(
                e.target.value
              )
            }
            className="w-full border rounded px-3 py-2"
            placeholder="Retailer, Brand, Agency..."
          />

        </div>

      </section>

      {/* ===================================================== */}
      {/* CLASSIFICATION */}
      {/* ===================================================== */}

      <section className="space-y-6">

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
              selectedUniverses.includes(
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
                  px-3
                  py-1
                  rounded
                  border
                  transition
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

      </section>

      {/* ===================================================== */}
      {/* LINKS */}
      {/* ===================================================== */}

      <section className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            External links
          </h2>

          <p className="text-sm text-gray-500">
            Public resources associated with the company.
          </p>

        </div>

        {/* WEBSITE */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Website
          </label>

          <input
            value={websiteUrl}
            onChange={(e) =>
              setWebsiteUrl(
                e.target.value
              )
            }
            className="w-full border rounded px-3 py-2"
            placeholder="https://..."
          />

        </div>

        {/* LINKEDIN */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            LinkedIn
          </label>

          <input
            value={linkedinUrl}
            onChange={(e) =>
              setLinkedinUrl(
                e.target.value
              )
            }
            className="w-full border rounded px-3 py-2"
            placeholder="https://linkedin.com/company/..."
          />

        </div>

      </section>

      {/* ===================================================== */}
      {/* SETTINGS */}
      {/* ===================================================== */}

      <section className="space-y-6">

        <div>

          <h2 className="text-lg font-semibold">
            Settings
          </h2>

        </div>

        <label className="flex items-center gap-3">

          <input
            type="checkbox"
            checked={isPartner}
            onChange={(e) =>
              setIsPartner(
                e.target.checked
              )
            }
          />

          <span>
            Partner company
          </span>

        </label>

      </section>

    </div>

  );

}
