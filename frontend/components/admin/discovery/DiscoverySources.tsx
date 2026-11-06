type Source={source_id:string;name:string;domain?:string|null;acquisition_mode?:string|null};
type Props={sources:Source[];onScan:(id:string,name:string)=>void;onResume?:(id:string,name:string)=>void;scanningSourceId:string|null;scanningAll:boolean};
export default function DiscoverySources({sources,onScan,onResume,scanningSourceId,scanningAll}:Props){
  return <div className="bg-white border rounded overflow-x-auto"><div className="p-4 border-b font-semibold">Sources configurées</div>
    <table className="w-full text-sm"><thead><tr className="bg-gray-50 border-b">{['Source','Mode','Domaine','Action'].map(x=><th key={x} className="p-3 text-left">{x}</th>)}</tr></thead>
      <tbody>{!sources.length?<tr><td colSpan={4} className="p-6 text-center text-gray-400">Aucune source configurée.</td></tr>:sources.map(source=>{
        const mode=(source.acquisition_mode||'').toUpperCase();const manual=['MANUAL','PDF_MANUAL','NEWSLETTER_MANUAL','LINKEDIN_PROFILE'].includes(mode);
        const current=scanningSourceId===source.source_id;const disabled=scanningAll||scanningSourceId!==null;
        return <tr key={source.source_id} className="border-b last:border-b-0"><td className="p-3 font-medium">{source.name}</td><td className="p-3">{mode||'—'}</td><td className="p-3 break-all">{source.domain||'—'}</td>
          <td className="p-3">{manual?<span className="text-gray-400">Studio / manuel</span>:<div className="flex gap-2"><button disabled={disabled} onClick={()=>onScan(source.source_id,source.name)} className="bg-ratecard-blue text-white px-3 py-1 rounded disabled:opacity-40">{current?'EN COURS…':'SCAN'}</button>
          {mode==='LINKEDIN_BRIGHTDATA'&&onResume&&<button disabled={disabled} className="border rounded px-3 py-1 disabled:opacity-40" onClick={()=>onResume(source.source_id,source.name)}>Reprendre le résultat</button>}</div>}</td></tr>;
      })}</tbody></table></div>;
}
