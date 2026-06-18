"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

const VIDEO_URL =
  `${GCS_BASE_URL}/product/getcurator-tour-v1.mp4`;

export default function LoginPage() {

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
      alert("Email required");
      return;
    }

    if (!password.trim()) {
      alert("Password required");
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
        throw new Error("Login failed");
      }

      localStorage.setItem(
        "user_id",
        res.user_id
      );

      localStorage.setItem(
        "role",
        res.role || "user"
      );

      window.location.href =
        redirect;

    } catch (e) {

      console.error(e);

      alert("Access denied");

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

        {/* LEFT SIDE */}

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
            max-w-4xl
          ">

            <h1 className="
              text-4xl
              font-bold
              text-gray-900
              mb-3
            ">
              Welcome to GetCurator
            </h1>

            <p className="
              text-lg
              text-gray-600
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

        {/* RIGHT SIDE */}

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
            shadow-sm
          ">

            <h2 className="
              text-xl
              font-semibold
              text-gray-900
              mb-6
            ">
              Access Curator
            </h2>

            <div className="space-y-4">

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

              <a
                href="https://calendly.com/martin-ratecard-events/30m"
                target="_blank"
                rel="noopener noreferrer"
                className="
                  block
                  w-full
                  text-center
                  rounded-lg
                  border
                  border-emerald-600
                  text-emerald-700
                  py-2
                  text-sm
                  font-medium
                  hover:bg-emerald-50
                  transition
                "
              >
                Book a Demo
              </a>

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

    </div>

  );
}
