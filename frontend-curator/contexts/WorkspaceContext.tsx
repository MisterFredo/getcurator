"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
} from "react";

/* ========================================================= */

type ContentItem = {
  id: string;
  [key: string]: any;
};

type NumberItem = {
  ID_NUMBER: string;
  [key: string]: any;
};

/* ========================================================= */

type WorkspaceContextType = {
  /* CONTENT */
  selectedContentItems: ContentItem[];
  toggleContent: (item: ContentItem) => void;
  removeContent: (id: string) => void;

  /* NUMBERS */
  selectedNumberItems: NumberItem[];
  toggleNumber: (item: NumberItem) => void;
  removeNumber: (id: string) => void;

  /* PANEL */
  panelOpen: boolean;
  setPanelOpen: (open: boolean) => void;

  /* ANALYSIS */
  analysis: string;
  setAnalysis: (value: string) => void;

  loading: boolean;
  setLoading: (value: boolean) => void;

  /* HELPERS */
  clearWorkspace: () => void;
};

/* ========================================================= */

const WorkspaceContext =
  createContext<WorkspaceContextType | null>(null);

/* ========================================================= */

export function WorkspaceProvider({
  children,
}: {
  children: React.ReactNode;
}) {

  /* =========================================================
     CONTENT
  ========================================================= */

  const [selectedContentItems, setSelectedContentItems] =
    useState<ContentItem[]>([]);

  /* =========================================================
     NUMBERS
  ========================================================= */

  const [selectedNumberItems, setSelectedNumberItems] =
    useState<NumberItem[]>([]);

  /* =========================================================
     PANEL
  ========================================================= */

  const [panelOpen, setPanelOpen] = useState(false);

  /* =========================================================
     ANALYSIS
  ========================================================= */

  const [analysis, setAnalysis] = useState("");
  const [loading, setLoading] = useState(false);

  /* =========================================================
     CONTENT ACTIONS
  ========================================================= */

  function toggleContent(item: ContentItem) {
    setSelectedContentItems((prev) => {
      const exists = prev.find((i) => i.id === item.id);

      if (exists) {
        return prev.filter((i) => i.id !== item.id);
      }

      return [...prev, item];
    });

    setPanelOpen(true);
  }

  function removeContent(id: string) {
    setSelectedContentItems((prev) =>
      prev.filter((i) => i.id !== id)
    );
  }

  /* =========================================================
     NUMBER ACTIONS
  ========================================================= */

  function toggleNumber(item: NumberItem) {
    setSelectedNumberItems((prev) => {
      const exists = prev.find(
        (i) => i.ID_NUMBER === item.ID_NUMBER
      );

      if (exists) {
        return prev.filter(
          (i) => i.ID_NUMBER !== item.ID_NUMBER
        );
      }

      return [...prev, item];
    });

    setPanelOpen(true);
  }

  function removeNumber(id: string) {
    setSelectedNumberItems((prev) =>
      prev.filter((i) => i.ID_NUMBER !== id)
    );
  }

  /* =========================================================
     HELPERS
  ========================================================= */

  function clearWorkspace() {
    setSelectedContentItems([]);
    setSelectedNumberItems([]);

    setAnalysis("");
    setLoading(false);
  }

  /* ========================================================= */

  const value = useMemo(
    () => ({
      /* CONTENT */
      selectedContentItems,
      toggleContent,
      removeContent,

      /* NUMBERS */
      selectedNumberItems,
      toggleNumber,
      removeNumber,

      /* PANEL */
      panelOpen,
      setPanelOpen,

      /* ANALYSIS */
      analysis,
      setAnalysis,

      loading,
      setLoading,

      /* HELPERS */
      clearWorkspace,
    }),
    [
      selectedContentItems,
      selectedNumberItems,
      panelOpen,
      analysis,
      loading,
    ]
  );

  /* ========================================================= */

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

/* ========================================================= */

export function useWorkspace() {
  const context = useContext(WorkspaceContext);

  if (!context) {
    throw new Error(
      "useWorkspace must be used inside WorkspaceProvider"
    );
  }

  return context;
}
