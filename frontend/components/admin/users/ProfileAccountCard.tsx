"use client";

const LANGUAGES = [
  { value: "fr", label: "Français" },
  { value: "en", label: "English" },
];

const ROLES = [
  { value: "user", label: "User" },
  { value: "admin", label: "Admin" },
];

const PROFILE_TYPES = [
  { value: "USER", label: "User" },
  { value: "EXPERT", label: "Expert" },
];

const FREQUENCIES = [
  { value: "WEEKLY", label: "Weekly" },
  { value: "MONTHLY", label: "Monthly" },
  { value: "DISABLED", label: "Disabled" },
];

type Props = {
  profileType: "USER" | "EXPERT";
  setProfileType: (
    value: "USER" | "EXPERT"
  ) => void;

  role: string;
  setRole: (
    value: string
  ) => void;

  language: string;
  setLanguage: (
    value: string
  ) => void;

  frequency: string;
  setFrequency: (
    value: string
  ) => void;

  isActive: boolean;
  setIsActive: (
    value: boolean
  ) => void;
};

export default function ProfileAccountCard({
  profileType,
  setProfileType,

  role,
  setRole,

  language,
  setLanguage,

  frequency,
  setFrequency,

  isActive,
  setIsActive,
}: Props) {

  return (

    <div className="bg-white border rounded-xl p-6 space-y-6">

      {/* ===================================================== */}
      {/* HEADER */}
      {/* ===================================================== */}

      <div>

        <h2 className="text-lg font-semibold">
          Account
        </h2>

        <p className="text-sm text-gray-500 mt-1">
          Configure how this profile behaves inside GetCurator.
        </p>

      </div>

      {/* ===================================================== */}
      {/* GRID */}
      {/* ===================================================== */}

      <div className="grid grid-cols-2 gap-6">

        {/* PROFILE TYPE */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Profile Type
          </label>

          <select
            value={profileType}
            onChange={(e) =>
              setProfileType(
                e.target.value as
                  "USER" | "EXPERT"
              )
            }
            className="w-full border rounded-lg px-3 py-2"
          >
            {PROFILE_TYPES.map((p) => (
              <option
                key={p.value}
                value={p.value}
              >
                {p.label}
              </option>
            ))}
          </select>

        </div>

        {/* ROLE */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Role
          </label>

          <select
            value={role}
            onChange={(e) =>
              setRole(
                e.target.value
              )
            }
            className="w-full border rounded-lg px-3 py-2"
          >
            {ROLES.map((r) => (
              <option
                key={r.value}
                value={r.value}
              >
                {r.label}
              </option>
            ))}
          </select>

        </div>

        {/* LANGUAGE */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Language
          </label>

          <select
            value={language}
            onChange={(e) =>
              setLanguage(
                e.target.value
              )
            }
            className="w-full border rounded-lg px-3 py-2"
          >
            {LANGUAGES.map((l) => (
              <option
                key={l.value}
                value={l.value}
              >
                {l.label}
              </option>
            ))}
          </select>

        </div>

        {/* DIGEST */}

        <div className="space-y-2">

          <label className="text-sm font-medium">
            Digest Frequency
          </label>

          <select
            value={frequency}
            onChange={(e) =>
              setFrequency(
                e.target.value
              )
            }
            className="w-full border rounded-lg px-3 py-2"
          >
            {FREQUENCIES.map((f) => (
              <option
                key={f.value}
                value={f.value}
              >
                {f.label}
              </option>
            ))}
          </select>

        </div>

      </div>

      {/* ===================================================== */}
      {/* ACTIVE */}
      {/* ===================================================== */}

      <div className="flex items-center justify-between border rounded-lg px-4 py-3">

        <div>

          <div className="font-medium">
            Active
          </div>

          <div className="text-sm text-gray-500">
            Inactive profiles are ignored by digest generation and MCP.
          </div>

        </div>

        <input
          type="checkbox"
          checked={isActive}
          onChange={(e) =>
            setIsActive(
              e.target.checked
            )
          }
          className="h-5 w-5"
        />

      </div>

    </div>

  );

}
