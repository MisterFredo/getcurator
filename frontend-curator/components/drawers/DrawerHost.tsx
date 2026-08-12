"use client";

import { useDrawer } from "@/contexts/DrawerContext";

// ============================================================
// LEFT DRAWERS
// ============================================================

import CompanyDrawer from "@/components/drawers/CompanyDrawer";
import TopicDrawer from "@/components/drawers/TopicDrawer";
import SolutionDrawer from "@/components/drawers/SolutionDrawer";
import ExpertDrawer from "@/components/expert/ExpertDrawer";

import ContentDrawer from "@/components/content/ContentDrawer";

import NumberDrawer from "@/components/drawers/NumberDrawer";

/* ============================================================
   DRAWER HOST
============================================================ */

export default function DrawerHost() {

  const {

    leftDrawer,

    rightDrawer,

    closeLeftDrawer,

    closeRightDrawer,

  } = useDrawer();

  console.log(
    "RIGHT DRAWER",
    rightDrawer,
  );

  return (

    <>

      {/* =====================================================
          LEFT — COMPANY
      ===================================================== */}

      {leftDrawer.type === "company"
        && leftDrawer.id && (

        <CompanyDrawer

          id={leftDrawer.id}

          onClose={closeLeftDrawer}

        />

      )}

      {/* =====================================================
          LEFT — TOPIC
      ===================================================== */}

      {leftDrawer.type === "topic"
        && leftDrawer.id && (

        <TopicDrawer

          id={leftDrawer.id}

          onClose={closeLeftDrawer}

        />

      )}

      {/* =====================================================
          LEFT — SOLUTION
      ===================================================== */}

      {leftDrawer.type === "solution"
        && leftDrawer.id && (

        <SolutionDrawer

          id={leftDrawer.id}

          onClose={closeLeftDrawer}

        />

      )}

      {/* =====================================================
          LEFT — EXPERT
      ===================================================== */}

      {leftDrawer.type === "expert"
        && leftDrawer.id && (

        <ExpertDrawer
          expertId={leftDrawer.id}
        />

      )}

      {/* =====================================================
          RIGHT — CONTENT
      ===================================================== */}

      {rightDrawer.type === "content"
        && rightDrawer.id && (

        <ContentDrawer

          contentId={rightDrawer.id}

          onClose={closeRightDrawer}

        />

      )}

      {/* =====================================================
          RIGHT — NUMBERS
      ===================================================== */}

      {rightDrawer.type === "numbers"
        && rightDrawer.id && (

        <NumberDrawer

          id={rightDrawer.id}

          entityType={
            rightDrawer.payload?.entityType
          }

          onClose={closeRightDrawer}

        />

      )}

    </>

  );

}
