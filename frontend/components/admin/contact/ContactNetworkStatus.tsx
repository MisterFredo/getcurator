import type {Contact} from '@/lib/contacts';
export default function ContactNetworkStatus({contact}:{contact?:Contact|null}){
 const origin=contact?.contact_origin||(contact?.import_source==='LINKEDIN_CONNECTIONS'?'LINKEDIN_IMPORT':'MANUAL');
 const status=contact?.network_status||'NOT_VERIFIED';
 const originLabel=origin==='LINKEDIN_IMPORT'?'Import LinkedIn':origin==='MANUAL'?'Création manuelle':contact?.import_source==='CSV'?'Import CSV':'Autre import';
 const statusLabel=status==='CONFIRMED'?'Présence dans ton réseau confirmée':status==='NOT_FOUND'?'Non retrouvé lors de la dernière récupération':'Réseau LinkedIn non vérifié';
 const color=status==='CONFIRMED'?'text-green-800 bg-green-50':status==='NOT_FOUND'?'text-amber-800 bg-amber-50':'text-gray-600 bg-gray-100';
 const date=contact?.network_checked_at?new Date(contact.network_checked_at):null;
 return <div className="space-y-1 text-xs"><div className="font-medium text-gray-600">{originLabel}</div><span className={`inline-block rounded px-2 py-1 ${color}`}>{statusLabel}</span>{date&&!Number.isNaN(date.getTime())&&<div className="text-gray-500">Vérifié au {date.toLocaleString('fr-FR')}</div>}</div>;
}
