"use client";
import {useParams} from "next/navigation";
import MediaSourceForm from "@/components/admin/source/MediaSourceForm";
export default function EditSource(){const params=useParams();return <MediaSourceForm key={String(params?.id || '')} id={params?.id as string}/>;}
