"use client";
import ContactList from "@/components/admin/contact/ContactList";
import LinkedInContactImport from "@/components/admin/contact/LinkedInContactImport";
export default function ContactsPage(){return <div className="space-y-6"><header><h1 className="text-3xl font-semibold text-ratecard-blue">Contacts</h1><p className="text-gray-500 mt-2">Identités professionnelles, rattachements sociétés et suivi LinkedIn.</p></header><LinkedInContactImport/><ContactList/></div>;}
