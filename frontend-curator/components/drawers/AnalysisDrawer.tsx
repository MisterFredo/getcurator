"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api } from "@/lib/api";
import { X } from "lucide-react";
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

type AnalysisData = {
  id_content: string;
  title: string;

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
  id: string;
  onClose: () => void;
};

/* ========================================================= */

export default function AnalysisDrawer({ id, onClose }: Props) {
  const router = useRouter();
  const pathname = usePathname();

  const { rightDrawer, closeRightDrawer } = useDrawer();

  const [data, setData] = useState<AnalysisData | null>(null);
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
      try {
        const res = await api.get(
          `/curator/item/${id}/detail?type=analysis`
        );

        const payload = res?.data ?? res;

        setData(payload);
        requestAnimationFrame(() => setIsOpen(true));
      } catch (e) {
        console.error("❌ AnalysisDrawer load error", e);
      }
    }

    load();
  }, [id]);

  if (!data) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40">
        <div className="bg-white px-4 py-2 rounded text-sm">
          Loading…
        </div>
      </div>
    );
  }

  const badges = [
    ...(data.companies ?? []).map((c) => ({
      label: c.name,
      type: "company",
    })),
    ...(data.topics ?? []).map((t) => ({
      label: t.label,
      type: "topic",
    })),
    ...(data.solutions ?? []).map((s) => ({
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
      <div className="absolute inset-0 bg-black/40" onClick={close} />

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
              {data.title}
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
                    px-2 py-0.5 text-[10px] rounded-full uppercase tracking-wide
                    ${getBadgeClass(b.type)}
                  `}
                >
                  {b.label}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="px-5 py-6 space-y-8">

          {data.excerpt && (
            <p className="text-base font-medium text-gray-800 max-w-2xl">
              {data.excerpt}
            </p>
          )}

          {data.signal_analytique && (
            <div className="bg-teal-50 border border-teal-100 p-4 rounded">
              <h3 className="text-xs uppercase text-teal-600 mb-1">
                Signal
              </h3>
              <p className="text-sm text-teal-800">
                {data.signal_analytique}
              </p>
            </div>
          )}

          {/* 🔥 CONCEPTS STRUCTURÉS UNIQUEMENT */}
          {data.concepts?.length > 0 && (
            <div>
              <h3 className="text-xs uppercase text-gray-500 mb-2">
                Concepts clés
              </h3>

              <div className="flex flex-wrap gap-2">
                {data.concepts.map((c) => (
                  <span
                    key={c.id_concept}
                    className="px-2 py-1 text-xs rounded bg-gray-200 text-gray-800"
                  >
                    {c.label}
                  </span>
                ))}
              </div>
            </div>
          )}

          {data.mecanique_expliquee && (
            <div>
              <h3 className="text-xs uppercase text-gray-500 mb-2">
                Mécanique expliquée
              </h3>
              <p className="text-sm text-gray-700">
                {data.mecanique_expliquee}
              </p>
            </div>
          )}

          {data.enjeu_strategique && (
            <div>
              <h3 className="text-xs uppercase text-gray-500 mb-2">
                Enjeu stratégique
              </h3>
              <p className="text-sm text-gray-700">
                {data.enjeu_strategique}
              </p>
            </div>
          )}

          {data.point_de_friction && (
            <div>
              <h3 className="text-xs uppercase text-gray-500 mb-2">
                Point de friction
              </h3>
              <p className="text-sm text-gray-700">
                {data.point_de_friction}
              </p>
            </div>
          )}

          {data.content_body && (
            <div
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{
                __html: data.content_body,
              }}
            />
          )}

          {data.chiffres?.length > 0 && (
            <div>
              <h2 className="text-xs uppercase text-gray-500 mb-2">
                Chiffres clés
              </h2>
              <ul className="space-y-2">
                {data.chiffres.map((c, i) => (
                  <li
                    key={i}
                    className="border rounded p-3 text-sm bg-gray-50"
                  >
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.acteurs_cites?.length > 0 && (
            <div className="text-sm text-gray-600">
              <strong>Acteurs :</strong>{" "}
              {data.acteurs_cites.join(", ")}
            </div>
          )}

          {data.published_at && (
            <div className="pt-4 border-t text-xs text-gray-400">
              Publié le{" "}
              {new Date(data.published_at).toLocaleDateString("fr-FR")}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
