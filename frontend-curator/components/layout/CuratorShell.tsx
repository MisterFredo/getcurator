"use client";

import { useState } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  X,
  Building2,
  Box,
  Hash,
  Sparkles,
  PlayCircle,
  Users,
  Newspaper,
  MessageSquare,
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

  const hideWorkspace = [

    "/login",

    "/register",

    "/forgot-password",

    "/reset-password",

    "/product-tour",

  ].includes(pathname);

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
      clean.startsWith(
        path + "/"
      )
    );

  }

  /* =========================================================
     GETCURATOR
  ========================================================= */

  const navMain = [

    {
      href: "/watch",
      label: "Watch",
      icon: Sparkles,
    },

    {
      href: "/digests",
      label: "Digests",
      icon: Newspaper,
    },

    {
      href: "/conversation",
      label: "Conversation",
      icon: MessageSquare,
    },

    /*
    {
      href: "/numbers",
      label: "Numbers",
      icon: Hash,
    },
    */

  ];

  /* =========================================================
     EXPLORE
  ========================================================= */

  const navExplore = [

    {
      href: "/settings",
      label: "Experts",
      icon: Users,
    },

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

    {
      href: "/topics",
      label: "Topics",
      icon: Hash,
    },

  ];

  /* ========================================================= */

  const navLearn = [

    {
      href: "/product-tour",
      label: "Product Tour",
      icon: PlayCircle,
    },

  ];

  /* ========================================================= */

  const renderNav = (
    items: any[],
  ) =>
    items.map((item) => {

      const Icon =
        item.icon;

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
            flex
            items-center
            gap-2
            px-3
            py-2
            rounded-md
            transition

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

      {/* =====================================================
          GETCURATOR (HOME)
      ===================================================== */}

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
          alt="GetCurator"
        />

        <span
          className="
            text-lg
            font-semibold
            text-gray-900
          "
        >
          GetCurator
        </span>

      </Link>

      {/* =====================================================
          MAIN
      ===================================================== */}

      <nav
        className="
          space-y-2
          text-sm
        "
      >
        {renderNav(navMain)}
      </nav>

      {/* =====================================================
          EXPLORE
      ===================================================== */}

      <div className="mt-8">

        <div
          className="
            text-xs
            font-semibold
            text-gray-400
            uppercase
            mb-2
            px-3
          "
        >
          Explore
        </div>

        <nav
          className="
            space-y-2
            text-sm
          "
        >
          {renderNav(navExplore)}
        </nav>

      </div>

      {/* =====================================================
          LEARN
      ===================================================== */}

      <div className="mt-8">

        <div
          className="
            text-xs
            font-semibold
            text-gray-400
            uppercase
            mb-2
            px-3
          "
        >
          Learn
        </div>

        <nav
          className="
            space-y-2
            text-sm
          "
        >
          {renderNav(navLearn)}
        </nav>

      </div>

      {/* =====================================================
          MCP ASSISTANT (STAND-BY)
      ===================================================== */}

      {/*
      <div className="mt-10">

        <div
          className="
            text-xs
            font-semibold
            text-gray-400
            uppercase
            mb-2
            px-3
          "
        >
          AI
        </div>

        <a
          href="https://chatgpt.com/g/..."
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

      {/* DESKTOP */}

      <aside
        className="
          hidden
          md:flex
          w-56
          bg-white
          border-r
          p-6
          flex-col
        "
      >
        {Sidebar}
      </aside>

      {/* MOBILE */}

      {mobileOpen && (

        <div
          className="
            fixed
            inset-0
            z-50
            flex
            md:hidden
          "
        >

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

          <aside
            className="
              relative
              w-4/5
              max-w-xs
              bg-white
              p-6
            "
          >

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

      <main
        className="
          flex-1
          bg-gray-50
        "
      >

        <Header user={user} />

        {loading ? (

          <div className="p-6 text-sm text-gray-500">
            Loading...
          </div>

        ) : (

          <div
            className="
              p-4
              md:p-8
              h-[calc(100vh-72px)]
            "
          >

            <div
              className={`
                flex
                h-full
                ${hideWorkspace ? "" : "gap-8"}
              `}
            >

              <div
                className="
                  flex-1
                  min-w-0
                  overflow-auto
                "
              >
                {children}
              </div>

              {!hideWorkspace && (

                <aside
                  className="
                    hidden
                    xl:block
                    w-[380px]
                    shrink-0
                  "
                >
                  <WorkspacePanel />
                </aside>

              )}

            </div>

          </div>

        )}

      </main>

    </div>

  );

}
