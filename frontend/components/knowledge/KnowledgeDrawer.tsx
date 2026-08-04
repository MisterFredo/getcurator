"use client";

import {
  useEffect,
  useState,
} from "react";

import { X } from "lucide-react";

import {
  getKnowledge,
} from "@/lib/knowledge";

import type {
  KnowledgeEntity,
  KnowledgeEntitySummary,
  KnowledgeBlockType,
} from "@/types/knowledge";

import KnowledgeSummary from "./KnowledgeSummary";
import KnowledgeTabs from "./KnowledgeTabs";
import KnowledgeBlockEditor from "./KnowledgeBlockEditor";
import KnowledgeFooter from "./KnowledgeFooter";

/* ========================================================= */

type Props = {

  entity: KnowledgeEntitySummary;

  onClose: () => void;

};

/* ========================================================= */

export default function KnowledgeDrawer({

  entity,

  onClose,

}: Props) {

  const [
    knowledge,
    setKnowledge,
  ] =
    useState<KnowledgeEntity | null>(
      null,
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    isOpen,
    setIsOpen,
  ] =
    useState(false);

  const [
    selectedBlock,
    setSelectedBlock,
  ] =
    useState<KnowledgeBlockType>(
      "signal_analytique",
    );

  /* =======================================================
     LOAD
  ======================================================= */

  async function loadKnowledge() {

    setLoading(
      true,
    );

    try {

      const res =
        await getKnowledge(

          entity.entity_type,

          entity.entity_id,

        );

      setKnowledge(
        res,
      );

      requestAnimationFrame(() => {

        setIsOpen(
          true,
        );

      });

    } catch (e) {

      console.error(e);

      setKnowledge(
        null,
      );

    } finally {

      setLoading(
        false,
      );

    }

  }

  useEffect(() => {

    loadKnowledge();

  }, [

    entity.entity_id,

    entity.entity_type,

  ]);

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="fixed inset-0 z-[100] flex">

      {/* =================================================== */}
      {/* OVERLAY */}
      {/* =================================================== */}

      <div

        className="absolute inset-0 bg-black/40"

        onClick={onClose}

      />

      {/* =================================================== */}
      {/* DRAWER */}
      {/* =================================================== */}

      <aside

        className={`
          relative
          ml-auto
          flex
          h-full
          w-full
          flex-col
          bg-white
          shadow-xl
          md:w-[700px]
          overflow-hidden
          transform
          transition-transform
          duration-300
          ease-out
          ${
            isOpen
              ? "translate-x-0"
              : "translate-x-full"
          }
        `}

      >

        {/* =============================================== */}
        {/* CLOSE */}
        {/* =============================================== */}

        <button

          onClick={onClose}

          className="absolute right-4 top-4 z-20 rounded p-2 hover:bg-gray-100"

        >

          <X size={18} />

        </button>

        {/* =============================================== */}
        {/* LOADING */}
        {/* =============================================== */}

        {

          loading && (

            <div className="flex flex-1 items-center justify-center">

              Loading...

            </div>

          )

        }

        {/* =============================================== */}
        {/* ERROR */}
        {/* =============================================== */}

        {

          !loading &&
          !knowledge && (

            <div className="flex flex-1 items-center justify-center">

              Unable to load Knowledge.

            </div>

          )

        }

        {/* =============================================== */}
        {/* CONTENT */}
        {/* =============================================== */}

        {

          !loading &&
          knowledge && (

            <>

              <KnowledgeSummary

                entity={entity}

                knowledge={knowledge}

                onClose={onClose}

              />

              <KnowledgeTabs

                selectedBlock={selectedBlock}

                onChange={setSelectedBlock}

              />

              <KnowledgeBlockEditor

                entity={entity}

                knowledge={knowledge}

                selectedBlock={selectedBlock}

                onReload={loadKnowledge}

              />

              <KnowledgeFooter

                entity={entity}

                onReload={loadKnowledge}

              />

            </>

          )

        }

      </aside>

    </div>

  );

}
