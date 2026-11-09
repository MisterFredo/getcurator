import {api} from "@/lib/api";
export type Contact={id_contact:string;first_name:string;last_name:string;display_name:string;email:string|null;linkedin_url:string|null;sales_navigator_url?:string|null;job_title:string|null;id_company:string|null;company_name:string|null;company_is_active?:boolean;is_active:boolean;linkedin_follow_enabled:boolean;id_company_watch:string|null;created_at:string;updated_at:string;import_source?:string|null;contact_origin?:'MANUAL'|'LINKEDIN_IMPORT'|'OTHER';network_status?:'CONFIRMED'|'NOT_VERIFIED'|'NOT_FOUND';network_checked_at?:string|null;employer_check_status?:string|null;employer_checked_at?:string|null;observed_company_name?:string|null};
export type ContactPayload={first_name:string;last_name:string;email:string|null;linkedin_url:string|null;sales_navigator_url?:string|null;job_title:string|null;id_company:string|null;is_active:boolean;linkedin_follow_enabled:boolean};
export type CompanyChoice={id_company:string;name:string;is_active?:boolean;mention_watch_enabled?:boolean};
const base='/contact';
export function changed(){if(typeof window!=="undefined")window.dispatchEvent(new Event('contacts-updated'));}
export async function listContacts(options:{companyId?:string;q?:string;offset?:number}={}):Promise<{contacts:Contact[];total:number;has_more:boolean}>{
 const query=new URLSearchParams({limit:'50',offset:String(options.offset||0)});if(options.companyId)query.set('id_company',options.companyId);if(options.q)query.set('q',options.q);
 return api.get(`${base}/list?${query.toString()}`);
}
export async function getContact(id:string):Promise<Contact>{return api.get(`${base}/${encodeURIComponent(id)}`);}
export async function saveContact(data:ContactPayload,id?:string,expected?:string,inheritFollow=false):Promise<Contact>{
 const {linkedin_follow_enabled:follow,...identity}=data;
 const createPayload=inheritFollow?identity:{...identity,linkedin_follow_enabled:follow};
 const res=id?await api.put(`${base}/${encodeURIComponent(id)}`,{...data,expected_updated_at:expected}):await api.post(`${base}/create`,createPayload);
 if(res.status!=="ok"||!res.contact?.id_contact)throw new Error('Enregistrement non confirmé.');changed();return res.contact;
}
export async function followContact(contact:Contact,enabled:boolean):Promise<Contact>{
 const res=await api.put(`${base}/${encodeURIComponent(contact.id_contact)}/follow`,{is_enabled:enabled,expected_company_id:contact.id_company,expected_updated_at:contact.updated_at});
 if(res.status!=="ok"||!res.contact?.id_contact)throw new Error('Modification du suivi non confirmée.');changed();return res.contact;
}
export async function listContactCompanies():Promise<CompanyChoice[]>{const res=await api.get('/company/list');return (res.companies||[]).slice().sort((a:CompanyChoice,b:CompanyChoice)=>a.name.localeCompare(b.name));}
export function errorText(e:unknown){return e instanceof Error?e.message:'Opération impossible.';}
