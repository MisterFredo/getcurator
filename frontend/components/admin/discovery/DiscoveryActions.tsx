type Props={selectedCount:number;onStore:()=>void;onManual:()=>void;onDismiss:()=>void;disabled?:boolean};
export default function DiscoveryActions({selectedCount,onStore,onManual,onDismiss,disabled=false}:Props){
  return <div className="flex gap-3"><button onClick={onStore} disabled={disabled||selectedCount===0} className="bg-green-600 text-white px-4 py-2 rounded disabled:opacity-50">STOCKER ({selectedCount})</button>
    <button onClick={onManual} disabled={disabled||selectedCount===0} className="bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50">STUDIO ({selectedCount})</button>
    <button onClick={onDismiss} disabled={disabled||selectedCount===0} className="bg-red-600 text-white px-4 py-2 rounded disabled:opacity-50">DISMISS ({selectedCount})</button></div>;
}
