"use client";
import {useEffect,useRef,useState} from "react";
import Link from "next/link";
import ContactNetworkStatus from "@/components/admin/contact/ContactNetworkStatus";
import {useRouter} from "next/navigation";
import {getContact,saveContact,listContactCompanies,errorText} from "@/lib/contacts";
import type {Contact,ContactPayload,CompanyChoice} from "@/lib/contacts";
const empty:ContactPayload={first_name:'',last_name:'',email:null,linkedin_url:null,job_title:null,id_company:null,is_active:true,linkedin_follow_enabled:false};
const field='border rounded px-3 py-2 w-full';
export default function ContactForm({id}:{id?:string}){
 const router=useRouter();const [draft,setDraft]=useState<ContactPayload>({...empty});const [saved,setSaved]=useState<Contact|null>(null);
 const [companies,setCompanies]=useState<CompanyChoice[]>([]);const [loading,setLoading]=useState(true);const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [notice,setNotice]=useState('');const [retry,setRetry]=useState(0);
 const running=useRef(false);const mounted=useRef(true);
 useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;};},[]);
 useEffect(()=>{
  let stopped=false;setLoading(true);setError('');
  async function load(){try{
   const [choices,contact]=await Promise.all([listContactCompanies(),id?getContact(id):Promise.resolve(null)]);
   if(stopped)return;setCompanies(choices);setSaved(contact);
   if(contact)setDraft({first_name:contact.first_name||'',last_name:contact.last_name||'',email:contact.email,linkedin_url:contact.linkedin_url,job_title:contact.job_title,id_company:contact.id_company,is_active:contact.is_active,linkedin_follow_enabled:contact.linkedin_follow_enabled});
   else setDraft({...empty,id_company:new URLSearchParams(window.location.search).get('id_company')||null});
  }catch(e){if(!stopped)setError(errorText(e));}finally{if(!stopped)setLoading(false);}}
  void load();return()=>{stopped=true;};
 },[id,retry]);
 function update<K extends keyof ContactPayload>(key:K,value:ContactPayload[K]){setDraft(old=>({...old,[key]:value,...((key==='id_company'||key==='linkedin_url'||key==='is_active')&&!value?{linkedin_follow_enabled:false}:{})}));}
 async function save(event:React.FormEvent){
  event.preventDefault();if(running.current)return;running.current=true;setBusy(true);setError('');setNotice('');
  try{const contact=await saveContact(draft,id||saved?.id_contact,saved?.updated_at);if(!mounted.current)return;setSaved(contact);setDraft({first_name:contact.first_name,last_name:contact.last_name,email:contact.email,linkedin_url:contact.linkedin_url,job_title:contact.job_title,id_company:contact.id_company,is_active:contact.is_active,linkedin_follow_enabled:contact.linkedin_follow_enabled});setNotice('Contact enregistré. Aucun scan n’a été déclenché.');if(!id)router.replace(`/admin/contact/edit/${encodeURIComponent(contact.id_contact)}`);}
  catch(e){if(mounted.current)setError(errorText(e));}finally{running.current=false;if(mounted.current)setBusy(false);}
 }
 if(loading)return <p>Chargement du contact…</p>;
 if(error&&!companies.length)return <div role="alert"><p className="text-red-700">{error}</p><button className="underline" onClick={()=>setRetry(v=>v+1)}>Réessayer</button></div>;
 const canFollow=!!draft.id_company&&!!draft.linkedin_url&&draft.is_active&&companies.find(c=>c.id_company===draft.id_company)?.is_active!==false;
 return <form onSubmit={save} className="space-y-6"><section className="border rounded bg-white p-4"><ContactNetworkStatus contact={saved}/><p className="text-xs text-gray-500 mt-2">L’origine et la présence dans ton réseau sont indépendantes du suivi des publications.</p>{saved&&draft.linkedin_url!==saved.linkedin_url&&<p className="text-xs text-amber-800 mt-2">Le statut affiché concerne le profil enregistré. Il sera réévalué après l’enregistrement de la nouvelle URL.</p>}</section><fieldset disabled={busy} className="border rounded bg-white p-5 grid md:grid-cols-2 gap-4">
 <label>Prénom<input className={field} value={draft.first_name} maxLength={150} onChange={e=>update('first_name',e.target.value)}/></label>
 <label>Nom *<input required className={field} value={draft.last_name} maxLength={150} onChange={e=>update('last_name',e.target.value)}/></label>
 <label>E-mail professionnel<input className={field} type="email" maxLength={320} value={draft.email||''} onChange={e=>update('email',e.target.value||null)}/></label>
 <label>Fonction<input className={field} maxLength={250} value={draft.job_title||''} onChange={e=>update('job_title',e.target.value||null)}/></label>
 <label>Société<select className={field} value={draft.id_company||''} onChange={e=>update('id_company',e.target.value||null)}><option value="">Sans rattachement</option>{companies.map(c=><option key={c.id_company} value={c.id_company}>{c.name}{c.is_active===false?' — inactive':''}</option>)}</select></label>
 <label>Profil LinkedIn personnel<input className={field} type="url" maxLength={4096} placeholder="https://www.linkedin.com/in/…" value={draft.linkedin_url||''} onChange={e=>update('linkedin_url',e.target.value||null)}/></label>
 <label className="flex gap-2 items-center"><input type="checkbox" checked={draft.is_active} onChange={e=>update('is_active',e.target.checked)}/>Contact actif</label>
 <div className="md:col-span-2 border-t pt-4 space-y-2"><label className="flex gap-2 items-center"><input type="checkbox" disabled={!canFollow&&!draft.linkedin_follow_enabled} checked={draft.linkedin_follow_enabled} onChange={e=>update('linkedin_follow_enabled',e.target.checked)}/>Suivi automatique LinkedIn</label><p className="text-sm text-gray-500">Nécessite une société, un profil LinkedIn et un contact actif. Le réglage est aussi modifiable depuis la fiche société. L’enregistrement ne lance pas de scan.</p><p className="text-sm text-gray-500">Un changement de société ou de profil suspend l’ancien point et conserve ses publications. Si le suivi reste activé, le nouveau point devient disponible pour les prochaines collectes.</p></div>
 </fieldset>
 {error&&<p role="alert" className="text-red-700">{error}</p>}{notice&&<p role="status" className="text-green-800">{notice}</p>}
 <div className="flex flex-wrap items-center gap-4"><button disabled={busy} className="bg-ratecard-blue text-white rounded px-5 py-2 disabled:opacity-50">{busy?'Enregistrement…':id?'Enregistrer les modifications':'Créer le contact'}</button>{saved?.id_company&&<Link className="underline" href={`/admin/company/edit/${encodeURIComponent(saved.id_company)}`}>Fiche société</Link>}{saved?.id_company_watch&&<Link className="underline" href="/admin/discovery/corpo">Ouvrir Discovery Corpo pour lancer un scan</Link>}</div>
 </form>;
}
