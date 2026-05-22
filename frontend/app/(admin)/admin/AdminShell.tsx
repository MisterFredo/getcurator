"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  Building2,
  Tags,
  Layers,
  Newspaper,
  Mail,
  Share2,
  BookOpen,
  Puzzle,
  Link as LinkIcon,
  Archive,
  Search,
  Link2,
  Database,
  Calendar,
  BarChart3,
  Image,
  LayoutTemplate,
  Users,
  Languages, // 🔥 NEW
} from "lucide-react";

export default function AdminShell({
  children,
}: {
  children: React.ReactNode;
}) {

  const pathname = usePathname();

  function isActive(href: string) {

    if (!pathname) return false;

    return (
      pathname === href
      || pathname.startsWith(
        href + "/"
      )
    );
  }

  const navItems = [

    // =====================================================
    // CONTENT
    // =====================================================

    {
      href: "/admin/content",
      label: "Contenus",
      icon: Layers,
    },

    {
      href: "/admin/content/stock",
      label: "Stock",
      icon: Archive,
    },

    {
      href: "/admin/news",
      label: "News",
      icon: Newspaper,
    },

    {
      href: "/admin/search",
      label: "Search",
      icon: Search,
    },

    // =====================================================
    // DATA LAYER
    // =====================================================

    {
      href: "/admin/vector",
      label: "Vectorisation",
      icon: Database,
    },

    {
      href: "/admin/radar",
      label: "Radar",
      icon: Calendar,
    },

    {
      href: "/admin/numbers",
      label: "Numbers",
      icon: BarChart3,
    },

    // 🔥 NEW
    {
      href: "/admin/translation",
      label: "Translations",
      icon: Languages,
    },

    // =====================================================
    // DISTRIBUTION
    // =====================================================

    {
      href: "/admin/linkedin/compose",
      label: "LinkedIn",
      icon: Share2,
    },

    {
      href: "/admin/digest",
      label: "Digest (Adhoc)",
      icon: Mail,
    },

    {
      href: "/admin/digest/runs",
      label: "Runs Digest",
      icon: Calendar,
    },

    {
      href: "/admin/digest/templates",
      label: "Templates Digest",
      icon: LayoutTemplate,
    },

    {
      href: "/admin/event",
      label: "Events (assets)",
      icon: Image,
    },

    // =====================================================
    // ENTITIES
    // =====================================================

    {
      href: "/admin/company",
      label: "Sociétés",
      icon: Building2,
    },

    {
      href: "/admin/solution",
      label: "Solutions",
      icon: Puzzle,
    },

    {
      href: "/admin/matching",
      label: "Matching",
      icon: Link2,
    },

    {
      href: "/admin/topic",
      label: "Topics",
      icon: Tags,
    },

    {
      href: "/admin/concept",
      label: "Concepts",
      icon: BookOpen,
    },

    {
      href: "/admin/source",
      label: "Sources",
      icon: LinkIcon,
    },

    // =====================================================
    // USERS
    // =====================================================

    {
      href: "/admin/users",
      label: "Users",
      icon: Users,
    },
  ];

  return (

    <div className="min-h-screen flex">

      {/* SIDEBAR */}

      <aside className="w-64 bg-ratecard-blue text-white p-6 space-y-10 flex flex-col">

        {/* HEADER */}

        <div>

          <h1 className="text-xl font-semibold">
            Ratecard Admin
          </h1>

          <p className="text-xs opacity-80 mt-1">
            Gestion éditoriale
          </p>

        </div>

        {/* NAV */}

        <nav className="space-y-1 text-sm flex-1">

          {navItems.map((item) => {

            const Icon = item.icon;

            const active = isActive(
              item.href
            );

            return (

              <Link
                key={item.href}
                href={item.href}
                className={`
                  flex items-center gap-2 px-3 py-2 rounded transition
                  ${
                    active
                      ? "bg-white text-ratecard-blue font-semibold"
                      : "hover:bg-ratecard-green/20"
                  }
                `}
              >

                <Icon size={18} />

                <span>
                  {item.label}
                </span>

              </Link>

            );
          })}

        </nav>

        {/* FOOTER */}

        <div className="text-xs opacity-60">

          © {new Date().getFullYear()} Ratecard

        </div>

      </aside>

      {/* MAIN */}

      <main className="flex-1 p-10 bg-gray-50">

        {children}

      </main>

    </div>
  );
}
