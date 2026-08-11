"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  usePathname,
  useRouter,
} from "next/navigation";

import { api } from "@/lib/api";

import {
  watchLatest,
} from "@/lib/watch";

import type {
  WatchItem,
} from "@/types/watch";

import EntityDrawer from "@/components/drawers/EntityDrawer";
import DrawerHeader from "@/components/drawers/DrawerHeader";
import WatchList from "@/components/watch/WatchList";

import { useDrawer } from "@/contexts/DrawerContext";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { useUser } from "@/hooks/useUser";

/* ========================================================= */

const GCS_BASE_URL =
  process.env.NEXT_PUBLIC_GCS_BASE_URL!;

/* ========================================================= */

type CompanyData = {

  id_company: string;

  name: string;

  type?: string | null;

  description?: string | null;

  media_logo_rectangle_id?:
    string | null;

  website_url?: string | null;

  linkedin_url?: string | null;

  universes?: any[];

  nb_analyses?: number;

  delta_30d?: number;

};

/* ========================================================= */

export default function CompanyDrawer({
  id,
  onClose,
}: any) {

  const router =
    useRouter();

  const pathname =
    usePathname();

  const {
    user,
  } = useUser();

  const {
    leftDrawer,
    openRightDrawer,
    closeLeftDrawer,
  } = useDrawer();

  const {
    selectedContentItems,
    toggleContent,
  } = useWorkspace();

  const [
    data,
    setData,
  ] = useState<CompanyData | null>(
    null,
  );

  const [
    items,
    setItems,
  ] = useState<WatchItem[]>([]);

  const [
    total,
    setTotal,
  ] = useState(0);

  const [
    loading,
    setLoading,
  ] = useState(true);

  /* =========================================================
     DESCRIPTION
  ========================================================= */

  const [
    expanded,
    setExpanded,
  ] = useState(false);

  const [
    showToggle,
    setShowToggle,
  ] = useState(false);

  const descRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  /* =========================================================
     CLOSE
  ========================================================= */

  function close() {

    onClose?.();

    closeLeftDrawer();

    if (
      leftDrawer.mode === "route"
      && pathname.startsWith(
        "/companies",
      )
    ) {

      router.push(
        "/companies",
        {
          scroll: false,
        },
      );

    }

  }

  /* =========================================================
     LOAD COMPANY
  ========================================================= */

  useEffect(() => {

    async function loadCompany() {

      try {

        const res =
          await api.get(
            `/company/${id}/view`,
          );

        setData(
          res,
        );

      } catch (e) {

        console.error(
          "❌ Company load error:",
          e,
        );

        setData(
          null,
        );

      }

    }

    loadCompany();

  }, [
    id,
  ]);

  /* =========================================================
     LOAD WATCH
  ========================================================= */

  useEffect(() => {

    if (!user) {

      return;

    }

    async function loadContents() {

      setLoading(
        true,
      );

      try {

        const res =
          await watchLatest({

            user_id:
              user.user_id,

            company_id:
              id,

            limit:
              20,

          });

        setItems(
          res.items,
        );

        setTotal(
          res.count,
        );

      } catch (e) {

        console.error(
          "❌ Company contents error:",
          e,
        );

        setItems(
          [],
        );

        setTotal(
          0,
        );

      } finally {

        setLoading(
          false,
        );

      }

    }

    loadContents();

  }, [
    id,
    user,
  ]);

  /* =========================================================
     DESCRIPTION OVERFLOW
  ========================================================= */

  useEffect(() => {

    if (!data?.description) {

      setShowToggle(
        false,
      );

      return;

    }

    setShowToggle(
      data.description.length > 350,
    );

  }, [
    data?.description,
  ]);

  /* =========================================================
     CONTENT
  ========================================================= */

  function openContent(
    item: WatchItem,
  ) {

    openRightDrawer(
      "content",
      item.id,
    );

  }

  const selectedIds =
    selectedContentItems.map(
      (item) => item.id,
    );

  function toggleSelect(
    item: WatchItem,
  ) {

    toggleContent(
      item,
    );

  }

  /* ========================================================= */

  if (!data) {

    return null;

  }

  const logoUrl =
    data.media_logo_rectangle_id

      ? `${GCS_BASE_URL}/companies/${data.media_logo_rectangle_id}`

      : null;

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <EntityDrawer

      onClose={
        close
      }

      header={

        <DrawerHeader
          title={data.name}
          onClose={close}
        />

      }

    >

      {/* =====================================================
          LOGO
      ===================================================== */}

      {logoUrl && (

        <div className="
          w-full
          border-b
          border-gray-200
          flex
          justify-center
          py-4
        ">

          <img

            src={
              logoUrl
            }

            alt={
              data.name
            }

            className="
              h-16
              object-contain
            "

          />

        </div>

      )}

      {/* =====================================================
          DESCRIPTION
      ===================================================== */}

      {data.description && (

        <div className="
          border-b
          border-gray-200
          py-4
        ">

          <div

            ref={
              descRef
            }

            className={`
              prose
              prose-sm
              max-w-none
              transition-all
              duration-300

              ${
                expanded
                  ? ""
                  : "max-h-32 overflow-hidden"
              }
            `}

            dangerouslySetInnerHTML={{
              __html:
                data.description,
            }}

          />

          {showToggle && (

            <button

              onClick={() =>
                setExpanded(
                  !expanded,
                )
              }

              className="
                mt-3
                text-xs
                font-medium
                text-ratecard-blue
                hover:underline
              "

            >

              {
                expanded
                  ? "Voir moins"
                  : "Voir plus"
              }

            </button>

          )}

        </div>

      )}

      {/* =====================================================
          CONTENTS
      ===================================================== */}

      <section className="
        pt-4
      ">

        <WatchList

          title="Key Contents"

          total={
            total
          }

          items={
            items
          }

          loading={
            loading
          }

          hasMore={
            false
          }

          onLoadMore={() => {}}

          onSelect={
            openContent
          }

          selectedIds={
            selectedIds
          }

          onToggleSelect={
            toggleSelect
          }

        />

      </section>

    </EntityDrawer>

  );

}
