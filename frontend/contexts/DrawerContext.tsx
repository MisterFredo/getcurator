"use client";

import {
  createContext,
  useContext,
  useState,
  ReactNode,
} from "react";

import type {
  KnowledgeEntitySummary,
} from "@/types/knowledge";

/* =========================================================
   TYPES
========================================================= */

type DrawerTypeLeft =
  | "member"
  | null;

type DrawerTypeRight =
  | "news"
  | "analysis"
  | "newsletter"
  | "digest-preview"
  | "knowledge"
  | null;

type DrawerMode =
  | "silent"
  | "route";

type DrawerSlot = {

  type: DrawerTypeLeft | DrawerTypeRight;

  id: string | null;

  entityType?:
    | "company"
    | "topic"
    | "solution";

  knowledgeEntity?:
    | KnowledgeEntitySummary;

  mode: DrawerMode | null;

};

type DrawerContextType = {

  leftDrawer: DrawerSlot;

  rightDrawer: DrawerSlot;

  openLeftDrawer: (

    type: "member",

    id: string,

    mode?: DrawerMode,

  ) => void;

  openRightDrawer: (

    type:
      | "news"
      | "analysis"
      | "digest-preview"
      | "knowledge",

    id: string,

    mode?: DrawerMode,

    entityType?:
      | "company"
      | "topic"
      | "solution",

    knowledgeEntity?:
      | KnowledgeEntitySummary,

  ) => void;

  openNewsletterDrawer: (
    mode?: DrawerMode,
  ) => void;

  closeLeftDrawer: () => void;

  closeRightDrawer: () => void;

};

/* ========================================================= */

const DrawerContext =
  createContext<DrawerContextType | null>(
    null,
  );

/* ========================================================= */

export function DrawerProvider({
  children,
}: {
  children: ReactNode;
}) {

  const [
    leftDrawer,
    setLeftDrawer,
  ] =
    useState<DrawerSlot>({
      type: null,
      id: null,
      entityType: undefined,
      knowledgeEntity: undefined,
      mode: null,
    });

  const [
    rightDrawer,
    setRightDrawer,
  ] =
    useState<DrawerSlot>({
      type: null,
      id: null,
      entityType: undefined,
      knowledgeEntity: undefined,
      mode: null,
    });

  /* =======================================================
     LEFT
  ======================================================= */

  function openLeftDrawer(
    type: "member",
    id: string,
    mode: DrawerMode = "silent",
  ) {

    setLeftDrawer({

      type,

      id,

      entityType: undefined,

      knowledgeEntity: undefined,

      mode,

    });

  }

  function closeLeftDrawer() {

    setLeftDrawer({

      type: null,

      id: null,

      entityType: undefined,

      knowledgeEntity: undefined,

      mode: null,

    });

  }

  /* =======================================================
     RIGHT
  ======================================================= */

  function openRightDrawer(

    type:
      | "news"
      | "analysis"
      | "digest-preview"
      | "knowledge",

    id: string,

    mode: DrawerMode = "silent",

    entityType?:
      | "company"
      | "topic"
      | "solution",

    knowledgeEntity?:
      | KnowledgeEntitySummary,

  ) {

    setRightDrawer({

      type,

      id,

      entityType,

      knowledgeEntity,

      mode,

    });

  }

  function openNewsletterDrawer(
    mode: DrawerMode = "silent",
  ) {

    setRightDrawer({

      type: "newsletter",

      id: null,

      entityType: undefined,

      knowledgeEntity: undefined,

      mode,

    });

  }

  function closeRightDrawer() {

    setRightDrawer({

      type: null,

      id: null,

      entityType: undefined,

      knowledgeEntity: undefined,

      mode: null,

    });

  }

  return (

    <DrawerContext.Provider
      value={{
        leftDrawer,
        rightDrawer,
        openLeftDrawer,
        openRightDrawer,
        openNewsletterDrawer,
        closeLeftDrawer,
        closeRightDrawer,
      }}
    >

      {children}

    </DrawerContext.Provider>

  );

}

/* ========================================================= */

export function useDrawer() {

  const ctx =
    useContext(
      DrawerContext,
    );

  if (!ctx) {

    throw new Error(
      "useDrawer must be used within DrawerProvider",
    );

  }

  return ctx;

}
