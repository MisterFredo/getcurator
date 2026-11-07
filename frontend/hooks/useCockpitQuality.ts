"use client";
import {useState} from "react";
import {api} from "@/lib/api";
import type {QualityRow} from "@/types/cockpit";
export function useCockpitQuality(){
 const [loading,setLoading]=useState(false);const [rows,setRows]=useState<QualityRow[]>([]);const [error,setError]=useState<string|null>(null);
 async function load(endpoint:string):Promise<QualityRow[]>{
  setLoading(true);setError(null);
  try{const res=await api.get(`/cockpit/quality/${endpoint}`);if(res.status!=="ok"||!Array.isArray(res.results))throw new Error(res.message||"Réponse du contrôle invalide.");setRows(res.results);return res.results;}
  catch(e){setError(e instanceof Error?e.message:"Contrôle indisponible.");throw e;}
  finally{setLoading(false);}
 }
 return {loading,rows,error,load};
}
