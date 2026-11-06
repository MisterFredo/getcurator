import {api} from "@/lib/api";
export type MediaScanResult={status:string;discovered_urls:number;known?:number;warnings?:string[];message?:string};
export async function mediaLinkedInScan(sourceId:string,resume=false):Promise<MediaScanResult>{
  const path=`/discovery/linkedin-brightdata/${resume?'status':'scan'}/${encodeURIComponent(sourceId)}`;
  return resume?api.get(path):api.post(path,{});
}
export async function mediaLinkedInAttach(sourceId:string,snapshotId:string):Promise<MediaScanResult>{
  return api.post(`/discovery/linkedin-brightdata/attach/${encodeURIComponent(sourceId)}`,{snapshot_id:snapshotId});
}
