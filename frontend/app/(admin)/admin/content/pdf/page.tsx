import Link from "next/link";
import PDFStudio from "@/components/admin/content/PDFStudio";

export default function PDFStudioPage() {
  return (
    <div>
      <div className="px-6 pt-5">
        <Link href="/admin/content" className="text-sm underline">← Retour aux contenus</Link>
      </div>
      <PDFStudio />
    </div>
  );
}
