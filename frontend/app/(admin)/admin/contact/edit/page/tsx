"use client";
import Link from "next/link";
import {useParams} from "next/navigation";
import ContactForm from "@/components/admin/contact/ContactForm";
export default function EditContactPage(){const params=useParams();const id=typeof params?.id==='string'?params.id:'';return <div className="space-y-6"><header className="flex justify-between"><h1 className="text-2xl font-semibold">Modifier le contact</h1><Link className="underline" href="/admin/contact">← Contacts</Link></header>{id&&<ContactForm key={id} id={id}/>}</div>;}
