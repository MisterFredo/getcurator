"use client";

import { Suspense } from "react";

import AnalysisDrawer from "@/components/drawers/AnalysisDrawer";

function LoadingFallback() {

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-white">
      <p className="text-sm text-gray-500">
        Chargement du contenu…
      </p>
    </div>
  );
}

export default function ContentPage({
  params,
}: {
  params: { id: string };
}) {

  return (
    <Suspense fallback={<LoadingFallback />}>

      <AnalysisDrawer
        id={params.id}
        onClose={() => {}}
      />

    </Suspense>
  );
}
