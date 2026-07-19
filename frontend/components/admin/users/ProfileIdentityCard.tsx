"use client";

import CardSection from "@/components/ui/CardSection";

/* ========================================================= */

type Props = {
  email: string;
  setEmail: (value: string) => void;

  displayName: string;
  setDisplayName: (value: string) => void;

  name: string;
  setName: (value: string) => void;

  company: string;
  setCompany: (value: string) => void;

  description: string;
  setDescription: (value: string) => void;

  emailDisabled?: boolean;
};

/* ========================================================= */

export default function ProfileIdentityCard({
  email,
  setEmail,

  displayName,
  setDisplayName,

  name,
  setName,

  company,
  setCompany,

  description,
  setDescription,

  emailDisabled = false,
}: Props) {

  return (

    <CardSection
      title="Identity"
      description="Basic information describing this profile."
    >

      <div className="space-y-6">

        {/* ===================================================== */}
        {/* EMAIL */}
        {/* ===================================================== */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Email
          </label>

          <input
            type="email"
            value={email}
            disabled={emailDisabled}
            onChange={(e) =>
              setEmail(
                e.target.value
              )
            }
            className={`
              w-full
              border
              rounded-lg
              px-3
              py-2
              ${
                emailDisabled
                  ? "bg-gray-100 text-gray-500"
                  : ""
              }
            `}
          />

        </div>

        {/* ===================================================== */}
        {/* DISPLAY NAME / INTERNAL NAME */}
        {/* ===================================================== */}

        <div className="grid grid-cols-2 gap-6">

          <div className="space-y-2">

            <label className="text-sm font-medium">
              Display Name
            </label>

            <input
              value={displayName}
              onChange={(e) =>
                setDisplayName(
                  e.target.value
                )
              }
              placeholder="Retail Media Expert"
              className="
                w-full
                border
                rounded-lg
                px-3
                py-2
              "
            />

            <p className="text-xs text-gray-500">
              Public name displayed in the application.
            </p>

          </div>

          <div className="space-y-2">

            <label className="text-sm font-medium">
              Internal Name
            </label>

            <input
              value={name}
              onChange={(e) =>
                setName(
                  e.target.value
                )
              }
              placeholder="Retail Media Editorial Expert"
              className="
                w-full
                border
                rounded-lg
                px-3
                py-2
              "
            />

            <p className="text-xs text-gray-500">
              Internal administration name.
            </p>

          </div>

        </div>

        {/* ===================================================== */}
        {/* COMPANY */}
        {/* ===================================================== */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Company
          </label>

          <input
            value={company}
            onChange={(e) =>
              setCompany(
                e.target.value
              )
            }
            placeholder="GetCurator"
            className="
              w-full
              border
              rounded-lg
              px-3
              py-2
            "
          />

        </div>

        {/* ===================================================== */}
        {/* DESCRIPTION */}
        {/* ===================================================== */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Description
          </label>

          <textarea
            rows={4}
            value={description}
            onChange={(e) =>
              setDescription(
                e.target.value
              )
            }
            placeholder="Short description of this profile..."
            className="
              w-full
              border
              rounded-lg
              px-3
              py-2
              resize-none
            "
          />

          <p className="text-xs text-gray-500">
            Used to describe the profile in the admin interface and in the future Expert catalog.
          </p>

        </div>

      </div>

    </CardSection>

  );

}
