"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  DrawerProvider,
} from "@/contexts/DrawerContext";

import DrawerHost from "@/components/drawers/DrawerHost";

import {
  Archive,
  BarChart3,
  BookOpen,
  Building2,
  Calendar,
  Database,
  Gauge,
  Globe,
  Languages,
  Layers,
  LayoutTemplate,
  Link as LinkIcon,
  Link2,
  Puzzle,
  Tags,
  Users,
} from "lucide-react";

export default function AdminShell({
  children,
}: {
  children: React.ReactNode;
}) {

  const pathname =
    usePathname();

  function isActive(
    href: string,
  ) {

    if (!pathname) {
      return false;
    }

    return (
      pathname === href ||
      pathname.startsWith(
        href + "/"
      )
    );
  }

  const sections = [

    {
      title: "Cockpit",

      items: [
        {
          href: "/admin/cockpit",
          label: "Dashboard",
          icon: Gauge,
        },
      ],
    },

    {
      title: "Production",

      items: [
        {
          href: "/admin/discovery",
          label: "Discovery",
          icon: Globe,
        },
        {
          href: "/admin/content/stock",
          label: "Stock",
          icon: Archive,
        },
        {
          href: "/admin/translation",
          label: "Translation",
          icon: Languages,
        },
        {
          href: "/admin/content",
          label: "Contents",
          icon: Layers,
        },
      ],
    },

    {
      title: "Knowledge",

      items: [
        {
          href: "/admin/source",
          label: "Sources",
          icon: LinkIcon,
        },
        {
          href: "/admin/company",
          label: "Companies",
          icon: Building2,
        },
        {
          href: "/admin/solution",
          label: "Solutions",
          icon: Puzzle,
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
          href: "/admin/numbers",
          label: "Numbers",
          icon: BarChart3,
        },
      ],
    },

    {
      title: "Intelligence",

      items: [
        {
          href: "/admin/digest",
          label: "Digest",
          icon: LayoutTemplate,
        },
      ],
    },

    {
      title: "Administration",

      items: [
        {
          href: "/admin/users",
          label: "Users",
          icon: Users,
        },
        {
          href: "/admin/matching",
          label: "Matching",
          icon: Link2,
        },
        {
          href: "/admin/vector",
          label: "Vectorization",
          icon: Database,
        },
        {
          href: "/admin/radar",
          label: "Radar",
          icon: Calendar,
        },
      ],
    },

  ];

  return (

  <DrawerProvider>

    <div className="min-h-screen flex">

      {/* ===================================================== */}
      {/* SIDEBAR */}
      {/* ===================================================== */}

      <aside className="w-64 bg-ratecard-blue text-white p-6 flex flex-col">

        {/* ... tout ton code existant de la sidebar ... */}

      </aside>

      {/* ===================================================== */}
      {/* MAIN */}
      {/* ===================================================== */}

      <main className="flex-1 p-10 bg-gray-50">
        {children}
      </main>

      {/* ===================================================== */}
      {/* DRAWERS */}
      {/* ===================================================== */}

      <DrawerHost />

    </div>

  </DrawerProvider>

);
}
