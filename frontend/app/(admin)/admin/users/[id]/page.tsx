"use client";

import { useEffect, useState } from "react";

import {
  useParams,
  useRouter,
} from "next/navigation";

import Link from "next/link";

import {
  Eye,
  EyeOff,
} from "lucide-react";

import { api } from "@/lib/api";
const SUPPORTED_LANGS = ["fr", "en"];

/* ========================================================= */

type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export default function EditUser() {

  const params = useParams();

  const router = useRouter();

  const userId =
    params.id as string;

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [name, setName] =
    useState("");

  const [company, setCompany] =
    useState("");

  const [language, setLanguage] =
    useState("fr");

  const [role, setRole] =
    useState("user");

  const [universes, setUniverses] =
    useState<string[]>([]);

  const [
    availableUniverses,
    setAvailableUniverses,
  ] = useState<Universe[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [saving, setSaving] =
    useState(false);

  /* =====================================================
     LOAD DATA
  ===================================================== */

  useEffect(() => {

    async function load() {

      try {

        const [
          userRes,
          universeRes,
        ] = await Promise.all([
          api.get(
            `/user/${userId}`
          ),
          api.get(
            "/universe/list"
          ),
        ]);

        const user =
          userRes?.user;

        if (!user) {

          throw new Error(
            "User not found"
          );
        }

        // USER

        setEmail(
          user.EMAIL || ""
        );

        setName(
          user.NAME || ""
        );

        setCompany(
          user.COMPANY || ""
        );

        const lang = user.LANGUAGE || "fr";
        setLanguage(
          SUPPORTED_LANGS.includes(lang)
            ? lang
            : "fr"
        );

        setRole(
          user.ROLE || "user"
        );

        // UNIVERS

        setUniverses(
          userRes?.universes ?? []
        );

        // AVAILABLE UNIVERS

        setAvailableUniverses(
          universeRes?.universes ?? []
        );

      } catch (e) {

        console.error(
          "❌ load error",
          e
        );

        alert(
          "Erreur chargement utilisateur"
        );

        router.push(
          "/admin/users"
        );

      } finally {

        setLoading(false);

      }
    }

    if (userId) {
      load();
    }

  }, [
    userId,
    router,
  ]);

  /* =====================================================
     TOGGLE UNIVERS
  ===================================================== */

  function toggleUniverse(
    id: string
  ) {

    setUniverses((prev) =>
      prev.includes(id)
        ? prev.filter(
            (u) => u !== id
          )
        : [...prev, id]
    );
  }

  /* =====================================================
     PASSWORD GENERATOR
  ===================================================== */

  function generatePassword(
    length = 16
  ) {

    const chars =
      "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*";

    let result = "";

    const array =
      new Uint32Array(length);

    crypto.getRandomValues(array);

    for (
      let i = 0;
      i < length;
      i++
    ) {

      result += chars[
        array[i] % chars.length
      ];
    }

    setPassword(result);

    setShowPassword(true);
  }

  /* =====================================================
     SAVE
  ===================================================== */

  async function save() {

    try {

      setSaving(true);

      const payload: any = {
        user_id: userId,
        name,
        company,
        language: SUPPORTED_LANGS.includes(language)
          ? language
          : "fr",
        role,
        universes,
      };

      // PASSWORD OPTIONNEL

      if (
        password.trim()
      ) {

        payload.password =
          password.trim();
      }

      const res = await api.post(
        "/user/update",
        payload
      );

      if (
        res?.status !== "ok"
      ) {

        throw new Error(
          "Update failed"
        );
      }

      alert(
        "Utilisateur mis à jour"
      );

      router.push(
        "/admin/users"
      );

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur update"
      );

    } finally {

      setSaving(false);

    }
  }

  /* =====================================================
     UI
  ===================================================== */

  if (loading) {

    return (
      <div className="p-6">
        Loading...
      </div>
    );
  }

  return (

    <div className="
      space-y-10
    ">

      {/* HEADER */}

      <div className="
        flex
        justify-between
        items-center
      ">

        <h1 className="
          text-2xl
          font-semibold
        ">
          Modifier utilisateur
        </h1>

        <Link
          href="/admin/users"
          className="
            text-sm
            underline
          "
        >
          ← Retour
        </Link>

      </div>

      {/* EMAIL */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Email
        </label>

        <input
          className="
            border
            p-2
            w-full
            rounded
            bg-gray-100
          "
          value={email}
          disabled
        />

      </div>

      {/* PASSWORD */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Nouveau mot de passe
        </label>

        <div className="
          relative
        ">

          <input
            type={
              showPassword
                ? "text"
                : "password"
            }
            className="
              border
              p-2
              w-full
              rounded
              pr-32
            "
            placeholder="
              Laisser vide
              pour conserver
              le mot de passe actuel
            "
            value={password}
            onChange={(e) =>
              setPassword(
                e.target.value
              )
            }
          />

          <div
            className="
              absolute
              right-2
              top-1/2
              -translate-y-1/2
              flex
              items-center
              gap-2
            "
          >

            <button
              type="button"
              onClick={() =>
                generatePassword()
              }
              className="
                text-xs
                px-2
                py-1
                rounded
                bg-gray-100
                hover:bg-gray-200
                transition
              "
            >
              Générer
            </button>

            <button
              type="button"
              onClick={() =>
                setShowPassword(
                  (v) => !v
                )
              }
              className="
                text-gray-400
                hover:text-gray-600
              "
            >

              {showPassword
                ? (
                  <EyeOff size={18} />
                ) : (
                  <Eye size={18} />
                )}

            </button>

          </div>

        </div>

      </div>

      {/* NAME */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Nom
        </label>

        <input
          className="
            border
            p-2
            w-full
            rounded
          "
          value={name}
          onChange={(e) =>
            setName(
              e.target.value
            )
          }
        />

      </div>

      {/* COMPANY */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Société
        </label>

        <input
          className="
            border
            p-2
            w-full
            rounded
          "
          value={company}
          onChange={(e) =>
            setCompany(
              e.target.value
            )
          }
        />

      </div>

      {/* LANGUAGE */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Langue
        </label>

        <select
          className="
            border
            p-2
            rounded
            w-full
            max-w-xs
          "
          value={language}
          onChange={(e) => {
          const value = e.target.value;
            setLanguage(
              SUPPORTED_LANGS.includes(value)
                ? value
                : "fr"
            );
          }}
        >

          <option value="fr">
            Français
          </option>

          <option value="en">
            English
          </option>

        </select>

      </div>

      {/* ROLE */}

      <div className="
        space-y-1
      ">

        <label className="
          text-sm
          text-gray-500
        ">
          Rôle
        </label>

        <select
          className="
            border
            p-2
            rounded
            w-full
            max-w-xs
          "
          value={role}
          onChange={(e) =>
            setRole(
              e.target.value
            )
          }
        >

          <option value="user">
            User
          </option>

          <option value="admin">
            Admin
          </option>

        </select>

      </div>

      {/* UNIVERS */}

      <div className="
        space-y-2
      ">

        <label className="
          font-medium
        ">
          Univers
        </label>

        <div className="
          flex
          flex-col
          gap-2
        ">

          {availableUniverses.map(
            (u) => (

            <label
              key={u.id_universe}
              className="
                flex
                items-center
                gap-2
              "
            >

              <input
                type="checkbox"
                checked={universes.includes(
                  u.id_universe
                )}
                onChange={() =>
                  toggleUniverse(
                    u.id_universe
                  )
                }
              />

              {u.label}

            </label>

          ))}

        </div>

      </div>

      {/* CTA */}

      <button
        onClick={save}
        disabled={saving}
        className="
          bg-ratecard-blue
          px-6
          py-2
          text-white
          rounded
        "
      >

        {saving
          ? "Sauvegarde…"
          : "Sauvegarder"}

      </button>

    </div>
  );
}
