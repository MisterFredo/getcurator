"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const VIDEO_URL =
  `${GCS_BASE_URL}/product/getcurator-tour-v1.mp4`;

export default function LoginPage() {

  const router = useRouter();

  const searchParams =
    useSearchParams();

  const redirect =
    searchParams.get("redirect") || "/";

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  async function handleLogin() {

    if (!email.trim()) {
      alert("Email requis");
      return;
    }

    if (!password.trim()) {
      alert("Mot de passe requis");
      return;
    }

    setLoading(true);

    try {

      const res =
        await api.post(
          "/user/login",
          {
            email,
            password,
          }
        );

      if (!res || !res.user_id) {
        throw new Error(
          "Login failed"
        );
      }

      localStorage.setItem(
        "user_id",
        res.user_id
      );

      localStorage.setItem(
        "role",
        res.role || "user"
      );

      console.log(
        "✅ LOGIN SUCCESS",
        res
      );

      window.location.href =
        redirect;

    } catch (e) {

      console.error(e);

      alert(
        "Accès non autorisé"
      );

    } finally {

      setLoading(false);

    }
  }

  return (

    <div className="
      min-h-screen
      bg-gray-50
    ">

      <div className="
        min-h-screen
        flex
        flex-col
        lg:flex-row
      ">

        {/* VIDEO */}

        <div className="
          flex-1
          flex
          items-center
          justify-center
          p-6
          lg:p-10
        ">

          <div className="
            w-full
            max-w-5xl
          ">

            <h1 className="
              text-3xl
              font-bold
              text-gray-900
              mb-3
            ">
              Welcome to GetCurator
            </h1>

            <p className="
              text-gray-600
              text-lg
              mb-6
            ">
              Discover how to monitor companies,
              topics, solutions and strategic
              signals with GetCurator.
            </p>

            <div className="
              bg-white
              border
              rounded-xl
              overflow-hidden
              shadow-sm
            ">

              <video
                controls
                playsInline
                preload="metadata"
                className="
                  w-full
                  h-auto
                  bg-black
                "
              >

                <source
                  src={VIDEO_URL}
                  type="video/mp4"
                />

                Your browser does not support
                video playback.

              </video>

            </div>

          </div>

        </div>

        <div
          className="
            mt-6
            flex
            justify-center
          "
        >

          <a
            href="https://calendly.com/martin-ratecard-events/30m"
            target="_blank"
            rel="noopener noreferrer"
            className="
              inline-flex
              items-center
              justify-center
              px-6
              py-3
              rounded-lg
              bg-emerald-600
              text-white
              font-medium
              hover:bg-emerald-700
              transition
              shadow-sm
            "
          >
            Book a Demo
          </a>

        </div>

        {/* LOGIN */}

        <div className="
          w-full
          lg:w-[420px]
          flex
          items-center
          justify-center
          p-6
        ">

          <div className="
            w-full
            bg-white
            border
            rounded-xl
            p-6
            space-y-4
            shadow-sm
          ">

            <h2 className="
              text-lg
              font-semibold
              text-gray-900
            ">
              Access Curator
            </h2>

            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) =>
                setEmail(
                  e.target.value
                )
              }
              className="
                w-full
                border
                rounded-lg
                px-3
                py-2
                text-sm
              "
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) =>
                setPassword(
                  e.target.value
                )
              }
              className="
                w-full
                border
                rounded-lg
                px-3
                py-2
                text-sm
              "
            />

            <button
              onClick={handleLogin}
              disabled={loading}
              className="
                w-full
                bg-black
                text-white
                rounded-lg
                py-2
                text-sm
                font-medium
              "
            >
              {loading
                ? "Connecting..."
                : "Sign In"}
            </button>

          </div>

        </div>

      </div>

    </div>

  );
}
