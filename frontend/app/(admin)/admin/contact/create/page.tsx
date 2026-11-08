"use client";
import Link from "next/link";
import ContactForm from "@/components/admin/contact/ContactForm";
export default function CreateContactPage(){return <div className="space-y-6"><header className="flex justify-between"><h1 className="text-2xl font-semibold">Créer un contact</h1><Link className="underline" href="/admin/contact">← Contacts</Link></header><ContactForm/></div>;}
