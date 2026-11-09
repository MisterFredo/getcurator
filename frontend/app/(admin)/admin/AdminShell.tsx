"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Archive, BarChart3, BookOpen, Brain, Building2, Database, Gauge,
  Globe, Languages, Layers, LayoutTemplate, Link as LinkIcon,
  Library, Presentation, Link2, Puzzle, Sparkles, Tags, Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  children?: { href: string; label: string; exact?: boolean }[];
};
type NavSection = { title: string; items: NavItem[] };

const sections: NavSection[] = [
  { title: "Cockpit", items: [
    { href: "/admin/cockpit", label: "Dashboard", icon: Gauge },
  ] },
  { title: "Production", items: [
    { href: "/admin/discovery", label: "Discovery", icon: Globe, children: [
      { href: "/admin/discovery", label: "Médias", exact: true },
      { href: "/admin/discovery/corpo", label: "Veille", exact: true },
      { href: "/admin/discovery/corpo/mentions", label: "Mentions" },
    ] },
    { href: "/admin/content/stock", label: "Stock", icon: Archive },
    { href: "/admin/translation", label: "Translation", icon: Languages },
    { href: "/admin/content", label: "Contents", icon: Layers },
  ] },
  { title: "Reference Data", items: [
    { href: "/admin/source", label: "Sources", icon: LinkIcon },
    { href: "/admin/company", label: "Companies", icon: Building2 },
    { href: "/admin/contact", label: "Contacts", icon: Users },
    { href: "/admin/solution", label: "Solutions", icon: Puzzle },
    { href: "/admin/topic", label: "Topics", icon: Tags },
    { href: "/admin/concept", label: "Concepts", icon: BookOpen },
    { href: "/admin/numbers", label: "Numbers", icon: BarChart3 },
  ] },
  { title: "Intelligence", items: [
    { href: "/admin/library", label: "Library", icon: Library, children: [
      { href: "/admin/library", label: "Documents PDF", exact: true },
      { href: "/admin/library/corpo", label: "Corpo" },
    ] },
    { href: "/admin/knowledge", label: "Knowledge", icon: Brain },
    { href: "/admin/touch", label: "GetCurator Touch", icon: Sparkles },
    { href: "/admin/production", label: "Productions", icon: Presentation },
    { href: "/admin/digest", label: "Digest", icon: LayoutTemplate },
  ] },
  { title: "Administration", items: [
    { href: "/admin/users", label: "Users", icon: Users },
    { href: "/admin/matching", label: "Matching", icon: Link2 },
    { href: "/admin/vector", label: "Vectorization", icon: Database },
  ] },
];

export default function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  function isActive(href: string, exact = false) {
    return !!pathname && (pathname === href || (!exact && pathname.startsWith(`${href}/`)));
  }
  function linkClass(active: boolean) {
    return `flex items-center gap-3 px-3 py-2 rounded transition ${
      active ? "bg-white text-ratecard-blue font-semibold" : "hover:bg-ratecard-green/20"
    }`;
  }
  return (
    <div className="min-h-screen flex">
      <aside className="w-64 shrink-0 bg-ratecard-blue text-white p-6 flex flex-col">
        <div className="mb-8">
          <h1 className="text-xl font-semibold">Curator Admin</h1>
          <p className="text-xs opacity-80 mt-1">Knowledge Platform</p>
        </div>
        <nav className="flex-1 overflow-y-auto space-y-8" aria-label="Administration">
          {sections.map(section => (
            <div key={section.title}>
              <div className="text-xs uppercase tracking-wider opacity-50 mb-2 px-3">{section.title}</div>
              <div className="space-y-1">
                {section.items.map(item => {
                  const Icon = item.icon;
                  if (item.children) return (
                    <div key={item.href}>
                      <div className={`flex items-center gap-3 px-3 py-2 ${isActive(item.href) ? "font-semibold" : ""}`}>
                        <Icon size={18} /><span>{item.label}</span>
                      </div>
                      <div className="ml-5 pl-3 border-l border-white/20 space-y-1">
                        {item.children.map(child => {
                          const active = isActive(child.href, child.exact);
                          return <Link key={child.href} href={child.href} aria-current={active ? "page" : undefined}
                            className={linkClass(active)}>{child.label}</Link>;
                        })}
                      </div>
                    </div>
                  );
                  const active = isActive(item.href);
                  return <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined}
                    className={linkClass(active)}><Icon size={18} /><span>{item.label}</span></Link>;
                })}
              </div>
            </div>
          ))}
        </nav>
        <div className="pt-8 text-xs opacity-60">© {new Date().getFullYear()} Curator</div>
      </aside>
      <main className="min-w-0 flex-1 p-10 bg-gray-50">{children}</main>
    </div>
  );
}
