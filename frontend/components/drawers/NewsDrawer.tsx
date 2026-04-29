"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api } from "@/lib/api";
import { X } from "lucide-react";
import { useDrawer } from "@/contexts/DrawerContext";
import { trackEvent } from "@/lib/analytics";

const GCS_BASE_URL = process.env.NEXT_PUBLIC_GCS_BASE_URL!;

/* =========================================================
   TYPES
========================================================= */

type NewsData = {
  id_news: string;
  title: string;
  excerpt?: string | null;
  body?: string | null;
  published_at: string;
  visual_rect_id?: string | null;

  company: {
    id_company: string;
    name: string;
    media_logo_rectangle_id?: string | null;
  };
};

type Props = {
  id: string;
  onClose?: () => void;
};

/* =========================================================
   COMPONENT
========================================================= */

export default function NewsDrawer({ id, onClose }: Props) {
  const router = useRouter();
  const pathname = usePathname();

  const {
    rightDrawer,
    openLeftDrawer,
    closeRightDrawer,
    openNewsletterDrawer,
  } = useDrawer();

  const [data, setData] = useState<NewsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  /* =========================================================
     CONTEXT (RATECARD vs CURATOR)
  ========================================================= */

  const isCurator = pathname.startsWith("/feed");

  /* =========================================================
     CLOSE
  ========================================================= */

  function close() {
    setIsOpen(false);
    onClose?.();
    closeRightDrawer();

    if (
      rightDrawer.mode === "route" &&
      pathname.startsWith("/news")
    ) {
      router.push("/news", { scroll: false });
    }
  }

  /* =========================================================
     OPEN PARTNER (LEFT DRAWER)
  ========================================================= */

  function openPartner(e: React.MouseEvent) {
    e.stopPropagation();
    if (!data?.company?.id_company) return;

    trackEvent("open_partner_from_news", {
      news_id: data.id_news,
      company_id: data.company.id_company,
      company_name: data.company.name,
      source: isCurator ? "curator" : "ratecard",
    });

    openLeftDrawer("member", data.company.id_company, "silent");
  }

  /* =========================================================
     LOAD DATA
  ========================================================= */

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get(
          isCurator
            ? `/curator/news/${id}`
            : `/public/news/${id}`
        );

        setData(res);

        trackEvent("view_news_drawer", {
          news_id: res.id_news,
          news_title: res.title,
          company_name: res.company?.name || null,
          source: isCurator ? "curator" : "ratecard",
        });

        requestAnimationFrame(() => setIsOpen(true));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id, isCurator]);

  /* =========================================================
     LOADING STATE
  ========================================================= */

  if (loading) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-white">
        <p className="text-sm text-gray-500">
          Chargement de la news…
        </p>
      </div>
    );
  }

  /* =========================================================
     EMPTY STATE
  ========================================================= */

  if (!data) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-white">
        <p className="text-sm text-gray-500">
          News indisponible
        </p>
      </div>
    );
  }

  /* =========================================================
     VISUAL
  ========================================================= */

  const visualSrc = data.visual_rect_id
    ? `${GCS_BASE_URL}/news/${data.visual_rect_id}`
    : data.company?.media_logo_rectangle_id
    ? `${GCS_BASE_URL}/companies/${data.company.media_logo_rectangle_id}`
    : null;

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="fixed inset-0 z-[100] flex">
      {/* OVERLAY */}
      <div
        className="absolute inset-0 bg-black/40 transition-opacity"
        onClick={close}
      />

      {/* DRAWER */}
      <aside
        className={`
          relative ml-auto w-full md:w-[760px]
          bg-white shadow-xl overflow-y-auto
          transform transition-transform duration-300 ease-out
          ${isOpen ? "translate-x-0" : "translate-x-full"}
        `}
      >
        {/* HEADER */}
        <div className="sticky top-0 z-10 bg-white border-b border-gray-200 px-5 py-4 flex items-start justify-between">
          <div className="space-y-1 max-w-xl">
            <button
              onClick={openPartner}
              className="text-xs uppercase tracking-wide text-gray-400 hover:text-ratecard-blue"
            >
              {data.company.name}
            </button>

            <h1 className="text-xl font-semibold leading-tight text-gray-900">
              {data.title}
            </h1>
          </div>

          <button
            onClick={close}
            aria-label="Fermer"
            className="mt-1"
          >
            <X size={18} />
          </button>
        </div>

        {/* HERO */}
        {visualSrc && (
          <div className="w-full bg-white flex items-center justify-center overflow-hidden border-b border-gray-200">
            <div className="w-full max-w-[680px] h-[260px] flex items-center justify-center">
              <img
                src={visualSrc}
                alt={data.title}
                className="max-h-[85%] max-w-[85%] object-contain"
              />
            </div>
          </div>
        )}

        {/* CONTENT */}
        <div className="px-5 py-6 space-y-8">
          {data.excerpt && (
            <p className="text-base font-medium text-gray-800 max-w-2xl">
              {data.excerpt}
            </p>
          )}

          {data.body && (
            <div
              className="
                prose prose-sm max-w-none
                prose-p:my-4
                prose-ul:my-4
                prose-ol:my-4
                prose-li:my-1
                prose-strong:font-semibold
                prose-a:text-ratecard-blue
                prose-a:no-underline
                hover:prose-a:underline
              "
              dangerouslySetInnerHTML={{
                __html: data.body,
              }}
            />
          )}

          {/* CTA NEWSLETTER */}
          <div className="border border-gray-200 rounded-xl bg-gray-50 p-6 text-center space-y-3">
            <p className="text-xs uppercase tracking-wide text-gray-500">
              Newsletter
            </p>

            <p className="text-sm text-gray-800 font-medium">
              Recevez chaque semaine la lecture stratégique
              du marché.
            </p>

            <button
              onClick={() => {
                trackEvent("newsletter_cta_click", {
                  source: isCurator ? "curator" : "ratecard",
                  news_id: data.id_news,
                  news_title: data.title,
                });

                closeRightDrawer();
                openNewsletterDrawer("silent");
              }}
              className="
                inline-block
                px-5 py-2
                rounded-full
                bg-ratecard-blue
                text-white
                text-sm
                hover:opacity-90
                transition
              "
            >
              S’inscrire
            </button>
          </div>

          {/* FOOTER */}
          <div className="pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-400">
              Publié le{" "}
              {new Date(data.published_at).toLocaleDateString("fr-FR")}
            </p>
          </div>
        </div>
      </aside>
    </div>
  );
}
