type Item={id_discovery:string;source_name?:string|null;url:string;title?:string|null;status:string;published_at?:string|null};
type Props={items:Item[];selectedIds:string[];onToggle:(id:string)=>void;onToggleAll:()=>void;disabled?:boolean};
export default function DiscoveryTable({items,selectedIds,onToggle,onToggleAll,disabled=false}:Props){
  const allSelected=items.length>0&&items.every(item=>selectedIds.includes(item.id_discovery));
  return <div className="bg-white border rounded overflow-x-auto"><table className="w-full text-sm"><thead><tr className="bg-gray-50 border-b">
    <th className="p-3"><input aria-label="Tout sélectionner" type="checkbox" checked={allSelected} disabled={disabled} onChange={onToggleAll}/></th>
    {['Source','Titre','URL','Parution','Status'].map(label=><th key={label} className="p-3 text-left">{label}</th>)}</tr></thead>
    <tbody>{items.map(item=><tr key={item.id_discovery} className="border-b hover:bg-gray-50"><td className="p-3"><input aria-label={`Sélectionner ${item.title||item.url}`} type="checkbox" disabled={disabled} checked={selectedIds.includes(item.id_discovery)} onChange={()=>onToggle(item.id_discovery)}/></td>
      <td className="p-3">{item.source_name}</td><td className="p-3">{item.title}</td><td className="p-3"><a href={item.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline break-all">{item.url}</a></td>
      <td className="p-3 whitespace-nowrap">{item.published_at?new Date(item.published_at).toLocaleString('fr-FR',{timeZone:'Europe/Paris'}):'—'}</td><td className="p-3">{item.status}</td></tr>)}</tbody></table></div>;
}
