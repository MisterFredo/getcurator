"use client";

import { useEffect, useState } from "react";

import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  Eye,
  EyeOff,
} from "lucide-react";

import { api } from "@/lib/api";

/* ========================================================= */

type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export default function CreateUser() {

  const router = useRouter();

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
    useState(false);

  /* ---------------------------------------------------------
     LOAD UNIVERS
  --------------------------------------------------------- */

  useEffect(() => {

    async function loadUniverses() {

      try {

        const res = await api.get(
          "/universe/list"
        );

        setAvailableUniverses(
          res?.universes ?? []
        );

      } catch (e) {

        console.error(
          "Erreur chargement univers",
          e
        );

        setAvailableUniverses([]);
      }
    }

    loadUniverses();

  }, []);

  /* ---------------------------------------------------------
     HANDLE MULTI SELECT
  --------------------------------------------------------- */

  function toggleUniverse(id: string) {

    setUniverses((prev) =>
      prev.includes(id)
        ? prev.filter(
            (u) => u !== id
          )
        : [...prev, id]
    );
  }

  /* ---------------------------------------------------------
     PASSWORD GENERATOR
  --------------------------------------------------------- */

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

  /* ---------------------------------------------------------
     SAVE
  --------------------------------------------------------- */

  async function save() {

    if (
      !email.trim() ||
      !password.trim()
    ) {

      alert(
        "Email et mot de passe requis"
      );

      return;
    }

    try {

      setLoading(true);

      const res = await api.post(
        "/user/create",
        {
          email,
          password,

          name:
            name || null,

          company:
            company || null,

          language,

          role,

          universes,
        }
      );

      if (!res?.user_id) {

        throw new Error(
          "ID user manquant"
        );
      }

      alert(
        "Utilisateur créé"
      );

      router.push(
        "/admin/users"
      );

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur création"
      );

    } finally {

      setLoading(false);

    }
  }

  /* ---------------------------------------------------------
     UI
  --------------------------------------------------------- */

  return (

    <div className="
      space-y-10
    ">

      <div className="
        flex
        justify-between
      ">

        <h1 className="
          text-2xl
          font-semibold
        ">
          Ajouter un utilisateur
        </h1>

        <Link
          href="/admin/users"
          className="underline"
        >
          ← Retour
        </Link>

      </div>

      {/* EMAIL */}

      <input
        className="
          border
          p-2
          w-full
          rounded
        "
        placeholder="Email"
        value={email}
        onChange={(e) =>
          setEmail(
            e.target.value
          )
        }
      />

      {/* PASSWORD */}

      <div className="
        space-y-2
      ">

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
            placeholder="Mot de passe"
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

      <input
        className="
          border
          p-2
          w-full
          rounded
        "
        placeholder="Nom"
        value={name}
        onChange={(e) =>
          setName(
            e.target.value
          )
        }
      />

      {/* COMPANY */}

      <input
        className="
          border
          p-2
          w-full
          rounded
        "
        placeholder="Société"
        value={company}
        onChange={(e) =>
          setCompany(
            e.target.value
          )
        }
      />

      {/* LANGUAGE */}

      <select
        className="
          border
          p-2
          rounded
          w-full
          max-w-xs
        "
        value={language}
        onChange={(e) =>
          setLanguage(
            e.target.value
          )
        }
      >

        <option value="fr">
          Français
        </option>

        <option value="en">
          English
        </option>

      </select>

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
          block
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
        disabled={loading}
        className="
          bg-ratecard-blue
          px-6
          py-2
          text-white
          rounded
        "
      >

        {loading
          ? "Création…"
          : "Créer"}

      </button>

    </div>
  );
}
