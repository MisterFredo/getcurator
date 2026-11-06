"use client";

import { useCallback, useState } from "react";
import type { CompanyWatch } from "@/lib/companyWatch";
import WatchDiscoveryWorkspace from "./WatchDiscoveryWorkspace";

export default function WatchCollectionPanel({ watch, onClose, onBusyChange }: {
  watch: CompanyWatch; onClose: () => void; onBusyChange: (busy: boolean) => void;
}) {
  const [busy, setBusy] = useState(false);
  const change = useCallback((value:boolean)=>{setBusy(value);onBusyChange(value);},[onBusyChange]);
  return <section className="border rounded bg-white p-5 space-y-4">
    <div className="flex justify-between items-center"><p className="text-gray-500">{watch.company_name || watch.id_company}</p>
      <button type="button" disabled={busy} onClick={onClose} className="border rounded px-3 py-2 disabled:opacity-50">Fermer</button></div>
    <WatchDiscoveryWorkspace watch={watch} onBusyChange={change}/>
  </section>;
}
