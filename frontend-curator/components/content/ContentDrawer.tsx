"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useUser } from "@/hooks/useUser";

import {
  getContent,
} from "@/lib/watch";
import { X, ExternalLink } from "lucide-react";
import { useDrawer } from "@/contexts/DrawerContext";

/* ========================================================= */

type Topic = {
  id_topic: string;
  label: string;
};

type Company = {
  id_company: string;
  name: string;
};

type Solution = {
  id_solution: string;
  name: string;
};

type Concept = {
  id_concept: string;
  label: string;
};

type Content = {
  id_content: string;
  title: string;

  source_url?: string;
  source_title?: string;

  excerpt?: string;
  content_body?: string;

  mecanique_expliquee?: string;
  enjeu_strategique?: string;
  point_de_friction?: string;
  signal_analytique?: string;

  chiffres?: string[];
  citations?: string[];
  acteurs_cites?: string[];

  topics?: Topic[];
  companies?: Company[];
  solutions?: Solution[];
  concepts?: Concept[];

  published_at?: string;
};

/* ========================================================= */

type Props = {
    contentId: string;
    onClose: () => void;
}

/* ========================================================= */

export default function ContentDrawer({

    contentId,
  
    onClose,
  
  }: Props) {
  const router = useRouter();
  const pathname = usePathname();

  const { rightDrawer, closeRightDrawer } = useDrawer();
  const {
    user,
  } = useUser();

  const [content, setContent] =
    useState<Content | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  function close() {
    setIsOpen(false);
    onClose?.();
    closeRightDrawer();

    if (
      rightDrawer.mode === "route" &&
      pathname.startsWith("/")
    ) {
      router.replace(pathname, { scroll: false });
    }
  }

  useEffect(() => {
    async function load() {

      if (!user) {
    
        return;
    
      }
    
      try {
    
        const res =
          await getContent(
    
            contentId,
    
            user.user_id,
    
          );
    
        setContent(
          res,
        );
    
        requestAnimationFrame(
          () => setIsOpen(true),
        );
    
      } catch (e) {
    
        console.error(
          "❌ ContentDrawer load error",
          e,
        );
    
      }
    
    }

    load();
  }, [

    contentId,
  
    user,
  
  ]);

  if (!content) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40">
        <div className="bg-white px-4 py-2 rounded text-sm">
          Loading…
        </div>
      </div>
    );
  }

  const badges = [
    ...(content.companies ?? []).map((c) => ({
      label: c.name,
      type: "company",
    })),

    ...(content.topics ?? []).map((t) => ({
      label: t.label,
      type: "topic",
    })),

    ...(content.solutions ?? []).map((s) => ({
      label: s.name,
      type: "solution",
    })),
  ];

  function getBadgeClass(type?: string) {
    switch (type) {
      case "company":
        return "bg-blue-50 text-blue-600 border border-blue-100";

      case "solution":
        return "bg-purple-50 text-purple-600 border border-purple-100";

      case "topic":
        return "bg-gray-100 text-gray-700 border border-gray-200";

      default:
        return "bg-gray-100 text-gray-600";
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex">
      <div
        className="absolute inset-0 bg-black/40"
        onClick={close}
      />

      <aside
        className={`
          relative ml-auto w-full md:w-[780px]
          bg-white shadow-xl overflow-y-auto
          transform transition-transform duration-300 ease-out
          ${isOpen ? "translate-x-0" : "translate-x-full"}
        `}
      >
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-5 py-4 space-y-3">
          <div className="flex justify-between items-start">
            <h1 className="text-xl font-semibold text-gray-900 max-w-xl">
              {content.title}
            </h1>

            <button onClick={close}>
              <X size={18} />
            </button>
          </div>

          {badges.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {badges.map((b, i) => (
                <span
                  key={`${b.label}-${i}`}
                  className={`
                    px-2 py-0.5 text-[10px]
                    rounded-full uppercase tracking-wide
                    ${getBadgeClass(b.type)}
                  `}
                >
                  {b.label}
                </span>
              ))}
            </div>
          )}

          {content.source_url && (
            <div className="flex items-center">
              <a
                href={content.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="
                  inline-flex items-center gap-1
                  text-xs text-blue-600
                  hover:text-blue-800
                  hover:underline
                "
              >
                <ExternalLink size={12} />

                {content.source_title || "Read source article"}
              </a>
            </div>
          )}
        </div>

        <div className="px-5 py-6 space-y-8">

          {content.excerpt && (
            <p className="text-base font-medium text-gray-800 max-w-2xl">
              {content.excerpt}
            </p>
          )}

          {content.content_body && (
            <div
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{
                __html: content.content_body,
              }}
            />
          )}

          {content.signal_analytique && (
            <div className="bg-teal-50 border border-teal-100 p-4 rounded">
              <h3 className="text-xs uppercase text-teal-600 mb-1">
                Insight
              </h3>

              <p className="text-sm text-teal-800">
                {content.signal_analytique}
              </p>
            </div>
          )}

          {/* 🔥 CONCEPTS STRUCTURÉS UNIQUEMENT */}
          {content.concepts?.length > 0 && (
            <div>
              <h3 className="text-xs uppercase text-gray-500 mb-2">
                Key Concepts
              </h3>

              <div className="flex flex-wrap gap-2">
                {content.concepts.map((c) => (
                  <span
                    key={c.id_concept}
                    className="
                      px-2 py-1 text-xs rounded
                      bg-gray-200 text-gray-800
                    "
                  >
                    {c.label}
                  </span>
                ))}
              </div>
            </div>
          )}

          {content.mecanique_expliquee && (
            <div>
              <h3 className="text-xs uppercase text-gray-500 mb-2">
                Mechanism Explained
              </h3>

              <p className="text-sm text-gray-700">
                {content.mecanique_expliquee}
              </p>
            </div>
          )}

          {content.enjeu_strategique && (
            <div>
              <h3 className="text-xs uppercase text-gray-500 mb-2">
                Strategic Implication
              </h3>

              <p className="text-sm text-gray-700">
                {content.enjeu_strategique}
              </p>
            </div>
          )}

          {content.point_de_friction && (
            <div>
              <h3 className="text-xs uppercase text-gray-500 mb-2">
                Friction Point
              </h3>

              <p className="text-sm text-gray-700">
                {content.point_de_friction}
              </p>
            </div>
          )}

          {content.chiffres?.length > 0 && (
            <div>
              {/* HEADER + LEGEND */}
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xs uppercase text-gray-500">
                  Key Figures
                </h2>

                <div className="text-[10px] text-gray-400 hidden md:flex gap-2">
                  <span>Label</span>
                  <span>•</span>
                  <span>Value</span>
                  <span>•</span>
                  <span>Unit</span>
                  <span>•</span>
                  <span>Actor</span>
                  <span>•</span>
                  <span>Market</span>
                  <span>•</span>
                  <span>Period</span>
                </div>
              </div>

              {/* LIST */}
              <ul className="space-y-2">
                {content.chiffres.map((c, i) => {
                  const parts = c
                    .split("|")
                    .map((p) => p.trim());

                  return (
                    <li
                      key={i}
                      className="
                        border rounded p-3
                        text-sm bg-gray-50
                      "
                    >
                      {/* LABEL */}
                      <div className="font-medium text-gray-900">
                        {parts[0]}
                      </div>

                      {/* META */}
                      {parts.length > 1 && (
                        <div className="text-xs text-gray-500 mt-1 flex flex-wrap gap-2">
                          {parts.slice(1).map((p, idx) => (
                            <span key={idx}>
                              {p}
                              {idx < parts.length - 2 && " •"}
                            </span>
                          ))}
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {content.acteurs_cites?.length > 0 && (
            <div className="text-sm text-gray-600">
              <strong>Actors:</strong>{" "}
              {content.acteurs_cites.join(", ")}
            </div>
          )}

          {content.published_at && (
            <div className="pt-4 border-t text-xs text-gray-400">
              Published on{" "}
              {new Date(content.published_at).toLocaleDateString("en-GB")}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
