"use client";

import { useState } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  Home,
  X,
  Building2,
  Box,
  Hash,
  Sparkles,
} from "lucide-react";

import Header from "./Header";

import WorkspacePanel from "@/components/workspace/WorkspacePanel";

import { useUser } from "@/hooks/useUser";

/* ========================================================= */

const LOGO_URL =
  "/assets/brand/symbol_curator.jpeg";

/* ========================================================= */

export default function CuratorShell({
  children,
}: {
  children: React.ReactNode;
}) {

  const pathname =
    usePathname();

  const {
    user,
    loading,
  } = useUser();

  const [mobileOpen, setMobileOpen] =
    useState(false);

  /* ========================================================= */

  function isActive(path: string) {

    if (!pathname) return false;

    const clean =
      pathname.split("?")[0];

    return (
      clean === path ||
      clean.startsWith(path + "/")
    );
  }

  /* ========================================================= */

  const navData = [
    {
      href: "/feed",
      label: "Feed",
      icon: Sparkles,
    },
    {
      href: "/numbers",
      label: "Numbers",
      icon: Hash,
    },
  ];

  /* ========================================================= */

  const navEntities = [
    {
      href: "/companies",
      label: "Companies",
      icon: Building2,
    },
    {
      href: "/solutions",
      label: "Solutions",
      icon: Box,
    },

    // 🔥 TOPICS RÉACTIVÉ
    {
      href: "/topics",
      label: "Topics",
      icon: Hash,
    },
  ];

  /* ========================================================= */

  const renderNav = (
    items: any[]
  ) =>
    items.map((item) => {

      const Icon = item.icon;

      const active =
        isActive(item.href);

      return (
        <Link
          key={item.href}
          href={item.href}
          onClick={() =>
            setMobileOpen(false)
          }
          className={`
            flex items-center gap-2 px-3 py-2 rounded-md transition
            ${
              active
                ? "bg-emerald-100 text-emerald-800 font-semibold"
                : "text-gray-700 hover:bg-emerald-50"
            }
          `}
        >
          <Icon size={18} />

          <span>
            {item.label}
          </span>

        </Link>
      );
    });

  /* ========================================================= */

  const Sidebar = (
    <>

      <Link
        href="/"
        onClick={() =>
          setMobileOpen(false)
        }
        className="
          mb-10
          flex
          items-center
          gap-3
        "
      >

        <img
          src={LOGO_URL}
          className="w-8 h-8"
        />

        <span className="
          text-lg
          font-semibold
          text-gray-900
        ">
          GetCurator
        </span>

      </Link>

      {/* DATA */}
      <div>

        <div className="
          text-xs
          font-semibold
          text-gray-400
          uppercase
          mb-2
          px-3
        ">
          Data
        </div>

        <nav className="
          space-y-2
          text-sm
        ">
          {renderNav(navData)}
        </nav>

      </div>

      {/* ENTITIES */}
      <div className="mt-8">

        <div className="
          text-xs
          font-semibold
          text-gray-400
          uppercase
          mb-2
          px-3
        ">
          Entities
        </div>

        <nav className="
          space-y-2
          text-sm
        ">
          {renderNav(navEntities)}
        </nav>

      </div>

      {/* =====================================================
         🔥 MCP ASSISTANT (STAND-BY)
      ===================================================== */}

      {/*
      <div className="mt-10">

        <div className="
          text-xs
          font-semibold
          text-gray-400
          uppercase
          mb-2
          px-3
        ">
          AI
        </div>

        <a
          href="https://chatgpt.com/g/g-69c5cc7fed548191a395a92fe0fe3dbd-get-curator"
          target="_blank"
          rel="noopener noreferrer"
          className="
            flex
            items-center
            gap-2
            px-3
            py-2
            text-gray-700
            hover:bg-emerald-50
          "
        >
          <Sparkles size={18} />

          <span>
            MCP Assistant
          </span>

        </a>

      </div>
      */}

    </>
  );

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="min-h-screen flex">

      {/* SIDEBAR DESKTOP */}
      <aside className="
        hidden
        md:flex
        w-56
        bg-white
        border-r
        p-6
        flex-col
      ">
        {Sidebar}
      </aside>

      {/* MOBILE */}
      {mobileOpen && (
        <div className="
          fixed
          inset-0
          z-50
          flex
          md:hidden
        ">

          <div
            className="
              absolute
              inset-0
              bg-black/40
            "
            onClick={() =>
              setMobileOpen(false)
            }
          />

          <aside className="
            relative
            w-4/5
            max-w-xs
            bg-white
            p-6
          ">

            <button
              onClick={() =>
                setMobileOpen(false)
              }
              className="
                absolute
                top-4
                right-4
              "
            >
              <X />
            </button>

            {Sidebar}

          </aside>

        </div>
      )}

      {/* MAIN */}
      <main className="
        flex-1
        bg-gray-50
      ">

        <Header user={user} />

        {loading ? (

          <div className="
            p-6
            text-sm
            text-gray-500
          ">
            Chargement…
          </div>

        ) : (

          <div className="
            p-4
            md:p-8
            h-[calc(100vh-72px)]
          ">

            <div className="
              flex
              gap-8
              h-full
            ">

              {/* CONTENT */}
              <div className="
                flex-1
                min-w-0
                overflow-auto
              ">
                {children}
              </div>

              {/* WORKSPACE */}
              <aside className="
                hidden
                xl:block
                w-[380px]
                shrink-0
              ">
                <WorkspacePanel />
              </aside>

            </div>

          </div>

        )}

      </main>

    </div>
  );
}
