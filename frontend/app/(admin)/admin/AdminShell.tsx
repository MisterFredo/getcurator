"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  Archive,
  BarChart3,
  BookOpen,
  Building2,
  Database,
  Globe,
  Languages,
  Layers,
  Link as LinkIcon,
  Link2,
  Puzzle,
  Tags,
  Users,
  Calendar,
  LayoutTemplate,
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
      pathname === href ||
      pathname.startsWith(href + "/")
    );
  }

  const sections = [
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
          href: "/admin/matching",
          label: "Matching",
          icon: Link2,
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
        {
          href: "/admin/users",
          label: "Users",
          icon: Users,
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
      title: "System",
      items: [
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
    <div className="min-h-screen flex">
      {/* SIDEBAR */}

      <aside className="w-64 bg-ratecard-blue text-white p-6 flex flex-col">
        {/* HEADER */}

        <div className="mb-8">
          <h1 className="text-xl font-semibold">
            Curator Admin
          </h1>

          <p className="text-xs opacity-80 mt-1">
            Knowledge Platform
          </p>
        </div>

        {/* NAVIGATION */}

        <nav className="flex-1 overflow-y-auto space-y-8">
          {sections.map((section) => (
            <div key={section.title}>
              <div className="text-xs uppercase tracking-wider opacity-50 mb-2 px-3">
                {section.title}
              </div>

              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;

                  const active =
                    isActive(item.href);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`
                        flex items-center gap-3 px-3 py-2 rounded transition
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
              </div>
            </div>
          ))}
        </nav>

        {/* FOOTER */}

        <div className="pt-8 text-xs opacity-60">
          © {new Date().getFullYear()} Curator
        </div>
      </aside>

      {/* MAIN */}

      <main className="flex-1 p-10 bg-gray-50">
        {children}
      </main>
    </div>
  );
}
