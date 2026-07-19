"use client";

import { useState } from "react";

import {
  Eye,
  EyeOff,
} from "lucide-react";

import CardSection from "@/components/ui/CardSection";

/* ========================================================= */

type Props = {
  password: string;
  setPassword: (
    value: string
  ) => void;
};

/* ========================================================= */

export default function ProfileSecurityCard({
  password,
  setPassword,
}: Props) {

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  /* =====================================================
     PASSWORD GENERATOR
  ===================================================== */

  function generatePassword(
    length = 16,
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

      result +=
        chars[
          array[i] %
          chars.length
        ];

    }

    setPassword(result);

    setShowPassword(true);

  }

  /* =====================================================
     UI
  ===================================================== */

  return (

    <CardSection
      title="Security"
      description="Manage credentials for this profile."
    >

      <div className="space-y-2">

        <label className="text-sm font-medium">
          Password
        </label>

        <div className="relative">

          <input
            type={
              showPassword
                ? "text"
                : "password"
            }
            value={password}
            onChange={(e) =>
              setPassword(
                e.target.value
              )
            }
            placeholder="Leave empty to keep the current password"
            className="
              w-full
              border
              rounded-lg
              px-3
              py-2
              pr-36
            "
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
                rounded
                bg-gray-100
                px-2
                py-1
                text-xs
                transition
                hover:bg-gray-200
              "
            >
              Generate
            </button>

            <button
              type="button"
              onClick={() =>
                setShowPassword(
                  (v) => !v
                )
              }
              className="
                text-gray-500
                hover:text-gray-700
              "
            >

              {showPassword
                ? <EyeOff size={18} />
                : <Eye size={18} />}

            </button>

          </div>

        </div>

        <p className="text-xs text-gray-500">
          Leave this field empty when editing to keep the existing password.
        </p>

      </div>

    </CardSection>

  );

}
