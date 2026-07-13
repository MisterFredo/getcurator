// components/admin/solution/SolutionIdentity.tsx

"use client";

import { CompanyOption } from "@/types/solution";

/* ========================================================= */

type Props = {

  name: string;
  setName: (
    value: string,
  ) => void;

  idCompany: string;
  setIdCompany: (
    value: string,
  ) => void;

  companies: CompanyOption[];

};

/* ========================================================= */

export default function SolutionIdentity({

  name,
  setName,

  idCompany,
  setIdCompany,

  companies,

}: Props) {

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
            Main information describing the solution.
          </p>

        </div>

        {/* ================================================= */}
        {/* NAME */}
        {/* ================================================= */}

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
            placeholder="Solution name"
          />

        </div>

        {/* ================================================= */}
        {/* COMPANY */}
        {/* ================================================= */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Company
          </label>

          <select

            value={idCompany}

            onChange={(e) =>
              setIdCompany(
                e.target.value
              )
            }

            className="w-full border rounded px-3 py-2"

          >

            <option value="">
              Select a company...
            </option>

            {companies.map((company) => (

              <option
                key={company.id_company}
                value={company.id_company}
              >

                {company.name}

              </option>

            ))}

          </select>

        </div>

      </section>

    </div>

  );

}
