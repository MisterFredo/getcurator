import {api} from '@/lib/api';
import type {CompanyWatch, CorpoDiscovery, WatchCompany} from '@/lib/companyWatch';
export type WatchChannel = 'ALL'|'WEB'|'LINKEDIN';
export type WatchKind = 'ALL'|'PUBLICATIONS'|'SINGLE_PAGE';
export type SourceDiagnostic = {status:string;last_attempt_at?:string;last_success_at?:string;error?:string|null;warnings?:string[];new?:number;known?:number;unchanged?:number;legacy?:boolean};
export type MonitoredWatch = CompanyWatch & {watch_channel:string;watch_kind:string;diagnostic?:SourceDiagnostic|null};
export type WatchJobSource = {id_company:string;id_company_watch:string;label:string;company_name?:string;channel:string;kind:string;status:string;new:number;known:number;unchanged:number;error?:string;warnings?:string[]};
export type WatchJob = {id_job:string;status:string;kind:WatchKind;channel:WatchChannel;failed_only:boolean;updated_at:string;sources:WatchJobSource[];reused?:boolean};
export function watchClass(watch:CompanyWatch):{channel:WatchChannel;kind:WatchKind}{
 const host=(()=>{try{return new URL(watch.source_url).hostname.toLowerCase();}catch{return '';}})();
 const linked=host==='linkedin.com'||host.endsWith('.linkedin.com');
 const single=watch.collection_method!=='BRIGHTDATA'&&(watch.collection_config?.mode==='SINGLE_PAGE'||(!watch.collection_config?.mode&&linked));
 return {channel:linked?'LINKEDIN':'WEB',kind:single?'SINGLE_PAGE':'PUBLICATIONS'};
}
function query(values:Record<string,string|number|boolean|undefined>){
 const params=new URLSearchParams();Object.entries(values).forEach(([k,v])=>{if(v!==undefined&&v!=='')params.set(k,String(v));});return params.toString();
}
export function listMonitoredWatches(options:{id_company?:string;is_active?:boolean;channel?:WatchChannel;kind?:WatchKind;offset?:number;limit?:number}):Promise<{watches:MonitoredWatch[];has_more:boolean}>{
 const {id_company,...rest}=options;return api.get(`/company/watch/operations/sources?${query({company_id:id_company,...rest})}`);
}
export function listWatchItems(options:{companyId?:string;watchId?:string;status?:string;channel?:WatchChannel;kind?:WatchKind;offset?:number}):Promise<{items:CorpoDiscovery[];has_more:boolean}>{
 const {companyId,watchId,...rest}=options;return api.get(`/company/watch/operations/items?${query({company_id:companyId,watch_id:watchId,limit:50,...rest})}`);
}
export function listWatchJobs(company_id?:string,watch_id?:string):Promise<{jobs:WatchJob[]}>{return api.get(`/company/watch/operations/jobs?${query({company_id,watch_id})}`);}
export function launchWatchJob(options:{kind:WatchKind;channel:WatchChannel;company_id?:string;watch_id?:string;failed_only?:boolean;recover_only?:boolean}):Promise<WatchJob>{return api.post('/company/watch/operations/start',options);}
export function resumeWatchJob(id:string):Promise<WatchJob>{return api.post(`/company/watch/operations/jobs/${encodeURIComponent(id)}/resume`,{});}

export function pauseWatchJob(id:string):Promise<WatchJob>{return api.post(`/company/watch/operations/jobs/${encodeURIComponent(id)}/pause`,{});}

export async function listActiveWatchCompanies():Promise<WatchCompany[]>{
 const result=await api.get('/company/watch/operations/companies');return result.companies||[];
}
