import { buildDocumentHtml } from "@/components/admin/production/ProductionDocumentPreview";
import type { ProductionDocument } from "@/types/production-document";
const STYLES = `
.sheet{height:210mm;min-height:210mm;display:flex;flex-direction:column;padding:11mm 15mm;overflow:visible}
.header,.eyebrow,h1,.subtitle,.footer{flex:none}.header{padding-bottom:4mm}
.eyebrow{margin-top:4mm;font-size:11px}h1{font-size:30px;line-height:1.15;margin:3mm 0 5mm;overflow-wrap:anywhere}
.editorial-body{flex:1;min-height:0}.editorial-body p,.editorial-body li{font-size:17px;line-height:1.45;overflow-wrap:anywhere}
.editorial-body>p{margin-bottom:4mm}.editorial-body ul{margin-bottom:4mm}.editorial-body .bullets{gap:4mm}
.editorial-body .bullets li{padding:4mm}.editorial-body .takeaway{font-size:17px;margin-top:4mm}
.editorial-body .notes{font-size:11px;line-height:1.35;margin-bottom:2mm}.footer{margin-top:4mm;font-size:10px;padding-top:3mm}
.cover h1{font-size:42px}.cover .eyebrow{margin-top:8mm}.cover .subtitle{font-size:21px}.cover .cover-introduction p{font-size:17px}
.cover .footer{margin-top:4mm}.editorial-body .bibliography{columns:2}.editorial-body .bibliography li{font-size:12px;line-height:1.4}
.sheet.compact .editorial-body p,.sheet.compact .editorial-body li{font-size:15px;line-height:1.35}
.sheet.compact h1{font-size:27px}.sheet.compact .editorial-body .notes{font-size:10px}
@media print{.sheet{height:210mm;break-inside:avoid;margin:0}.editorial-body{min-height:0}}
`;
export function buildTouchEditorialHtml(document: ProductionDocument, filename: string, language: "fr" | "en") {
  return buildDocumentHtml(document,filename,language,true).replace("</style>",STYLES+"</style>");
}
export function checkTouchEditorialLayout(doc: Document) {
  const sheets=Array.from(doc.querySelectorAll<HTMLElement>(".sheet"));
  const overflow:number[]=[];
  sheets.forEach((sheet,index)=>{
    let body=sheet.querySelector<HTMLElement>(".editorial-body");
    if(!body){
      body=doc.createElement("div");body.className="editorial-body";
      const footer=sheet.querySelector<HTMLElement>(".footer")!;
      for(const child of Array.from(sheet.children)) if(!child.matches(".header,.eyebrow,h1,.subtitle,.footer")) body.appendChild(child);
      sheet.insertBefore(body,footer);
    }
    const fits=()=>body!.scrollHeight<=body!.clientHeight+2 && body!.scrollWidth<=body!.clientWidth+2
      && sheet.scrollHeight<=sheet.clientHeight+2;
    sheet.classList.remove("compact");
    if(!fits())sheet.classList.add("compact");
    if(!fits())overflow.push(index+1);
    const label=sheet.querySelector(".footer span:last-child");
    if(label)label.textContent=`${index+1} / ${sheets.length}`;
  });
  return {count:sheets.length,overflow};
}
