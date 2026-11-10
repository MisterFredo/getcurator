"use client";

import {
  useEffect,
  useState,
  useRef,
} from "react";

import {
  api,
} from "@/lib/api";

import {mediaLinkedInScan,mediaLinkedInAttach} from "@/lib/mediaLinkedIn";
import DiscoverySources from "@/components/admin/discovery/DiscoverySources";
import DiscoveryStats from "@/components/admin/discovery/DiscoveryStats";
import DiscoveryActions from "@/components/admin/discovery/DiscoveryActions";
import DiscoveryTable from "@/components/admin/discovery/DiscoveryTable";


/* =========================================================
   TYPES
========================================================= */

type DiscoveryItem = {

  id_discovery: string;

  source_id: string;
  source_name?: string | null;

  url: string;
  title?: string | null;

  status: string;

  date_found?: string | null;
  published_at?: string | null;
  created_at?: string | null;

};

type Source = {

  source_id: string;
  name: string;

  domain?: string | null;
  acquisition_mode?: string | null;

  universe_id?: string | null;

};


type Universe = {

  id_universe: string;
  label: string;

};


type LinkedInReport = {
  sourceId:string; name:string; status:string; received?:number|null; known?:number;
  added:number; issues?:number|null; reused?:boolean; error?:string;
};
type LinkedInResult = Awaited<ReturnType<typeof mediaLinkedInScan>> & {
  added_this_call?:number; received?:number|null; issue_count?:number|null; reused_result?:boolean;
};

type SourceMode =
  | "AUTOMATIC"
  | "MANUAL";


/* =========================================================
   PAGE
========================================================= */

export default function DiscoveryPage() {

  const [scanProgress,setScanProgress]=useState("");
  const [sourcesReady,setSourcesReady]=useState(false);
  const [linkedinReports,setLinkedinReports]=useState<Record<string,LinkedInReport>>({});
  const [scanWarnings,setScanWarnings]=useState<string[]>([]);
  const [scanErrors,setScanErrors]=useState<string[]>([]);
  const mounted=useRef(true);
  const stopScan=useRef(false);
  useEffect(()=>{mounted.current=true;return()=>{mounted.current=false;stopScan.current=true;};},[]);

  const [
    items,
    setItems,
  ] =
    useState<DiscoveryItem[]>([]);

  const [
    sources,
    setSources,
  ] =
    useState<Source[]>([]);

  const [
    universes,
    setUniverses,
  ] =
    useState<Universe[]>([]);
  
  
  const [
    universeId,
    setUniverseId,
  ] =
    useState("");

  const [
    selectedIds,
    setSelectedIds,
  ] =
    useState<string[]>([]);

  const [
    sourceMode,
    setSourceMode,
  ] =
    useState<SourceMode>(
      "AUTOMATIC"
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    scanningSourceId,
    setScanningSourceId,
  ] =
    useState<string | null>(
      null
    );

  const [
    scanningAll,
    setScanningAll,
  ] =
    useState(false);


  /* =======================================================
     SCAN STATE
  ======================================================== */

  const isScanning =
    scanningAll ||
    scanningSourceId !== null;


  /* =======================================================
     LOAD
  ======================================================== */

  async function loadData() {

    try {
  
      setLoading(true);
  
      const [
        discoveryRes,
        sourceRes,
        universeRes,
      ] =
        await Promise.all([
          api.get(
            "/discovery/list"
          ),
          api.get(
            "/source/list"
          ),
          api.get(
            "/universe/list"
          ),
        ]);
  
      setItems(
        discoveryRes.items || []
      );
  
      setSources(
        sourceRes.sources || []
      );
  
      setUniverses(
        universeRes.universes || []
      );
      setSourcesReady(true);
  
    } catch (e) {
      setSourcesReady(false);
      console.error(e);
  
      alert(
        "❌ Erreur chargement Discovery"
      );
  
    } finally {
  
      setLoading(false);
  
    }
  
  }


  /* =======================================================
     INIT
  ======================================================== */

  useEffect(() => {

    loadData();

  }, []);


  /* =======================================================
     SCAN ALL
  ======================================================== */

  const [pickedSourceId,setPickedSourceId]=useState("");

  async function collectLinkedIn(sourceId:string,name:string,resume=false) {
    let added=0;
    function observe(result:LinkedInResult) {
      if(typeof result.added_this_call!=='number')throw new Error('Mettre à jour le backend : compteur des insertions effectives absent.');
      added+=result.added_this_call;
      if(mounted.current)setLinkedinReports(previous=>({...previous,[sourceId]:{
        sourceId,name,status:result.status,received:result.received,known:result.known,
        added,issues:result.issue_count,reused:result.reused_result,
      }}));
    }
    try {
      let result:LinkedInResult=await mediaLinkedInScan(sourceId,resume);
      observe(result);
      if(result.status==='UNKNOWN') {
        const snapshot=window.prompt(`${name} : lancement incertain. Copiez le snapshot ID depuis Bright Data pour reprendre sans nouvel achat.`);
        if(!snapshot)throw new Error(result.message || 'Lancement à vérifier dans Bright Data');
        result=await mediaLinkedInAttach(sourceId,snapshot.trim());observe(result);
      }
      while(['RUNNING','STARTING'].includes(result.status) && mounted.current && !stopScan.current){
        setScanProgress(`${name} : collecte en cours chez Bright Data…`);
        for(let tick=0;tick<20 && mounted.current && !stopScan.current;tick++) await new Promise<void>(resolve=>setTimeout(resolve,500));
        if(!mounted.current || stopScan.current)return null;
        result=await mediaLinkedInScan(sourceId,true);observe(result);
      }
      if(!mounted.current || stopScan.current)return null;
      if(!['COMPLETE','ok'].includes(result.status))throw new Error(result.message || 'Aucun résultat à reprendre ; lancer un scan si nécessaire.');
      setScanWarnings(previous=>[...previous,...(result.warnings||[]).map(w=>`${name} : ${w}`)]);
      // Accumulate only writes performed during this invocation, not a stored run total.
      return {...result,discovered_urls:added};
    } catch(error) {
      if(mounted.current)setLinkedinReports(previous=>({...previous,[sourceId]:{
        ...previous[sourceId],sourceId,name,status:'FAILED',added,
        error:error instanceof Error?error.message:'Erreur LinkedIn',
      }}));
      throw error;
    }
  }

  async function scanAll(scope: "ALL" | "WEB" | "LINKEDIN" = "ALL") {
    if(isScanning||!sourcesReady||loading)return;
    stopScan.current=false;setScanningAll(true);setScanWarnings([]);setScanErrors([]);setLinkedinReports({});
    try {
      let found=0;let failed=0;
      if(scope!=="LINKEDIN"){
        setScanProgress('Scan des sources web…');
        try {
          const res=await api.post('/discovery/scan-all',{universe_id:universeId||null});
          found=res.discovered_urls||0;
          if(res.failed_sources){failed+=res.failed_sources;setScanErrors(previous=>[...previous,`${res.failed_sources} source(s) web en échec ; consulter les logs.`]);}
        } catch(error) {
          failed++;
          setScanErrors(previous=>[...previous,`Phase web interrompue : ${error instanceof Error?error.message:'Erreur web'}. ${scope==='ALL'?'La phase LinkedIn reste exécutée.':''}`]);
        }
      }
      const linked=scope==="WEB"?[]:Array.from(new Map(sources.filter(source=>source.acquisition_mode==='LINKEDIN_BRIGHTDATA' && (!universeId||source.universe_id===universeId)).map(source=>[source.source_id,source])).values());
      let cursor=0;let completed=0;
      const worker=async ()=>{
        while(mounted.current&&!stopScan.current){
          const source=linked[cursor++];if(!source)return;
          try{const result=await collectLinkedIn(source.source_id,source.name);if(result)found+=result.discovered_urls;}
          catch(e){failed++;if(mounted.current)setScanErrors(previous=>[...previous,`${source.name} : ${e instanceof Error?e.message:'Erreur scan'}`]);}
          completed++;
          if(mounted.current)setScanProgress(`LinkedIn : ${completed}/${linked.length} compte(s) terminé(s).`);
        }
      }
      await Promise.all(Array.from({length:Math.min(3,linked.length)},()=>worker()));
      if(mounted.current){setScanProgress(stopScan.current?'Suivi arrêté. Les collectes déjà lancées continuent chez Bright Data ; utilisez Reprendre le résultat.':`Scan terminé${failed?' avec erreurs':''} : ${found} URL ajoutée(s) pendant ce passage · ${completed}/${linked.length} compte(s) LinkedIn parcouru(s)${scope==='WEB'?' (hors périmètre)':''}.`);await loadData();}
    }catch(e){if(mounted.current)setScanErrors([e instanceof Error?e.message:'Erreur scan']);}
    finally{if(mounted.current)setScanningAll(false);}
  }

  async function scanSource(sourceId:string,sourceName:string,resume=false) {
    if(isScanning||!sourcesReady||loading)return;
    stopScan.current=false;setScanningSourceId(sourceId);setScanWarnings([]);setScanErrors([]);setLinkedinReports({});
    try{
      const source=sources.find(item=>item.source_id===sourceId);
      const res=source?.acquisition_mode==='LINKEDIN_BRIGHTDATA'
        ? await collectLinkedIn(sourceId,sourceName,resume)
        : await api.post(`/discovery/scan/${sourceId}`,{});
      if(mounted.current){
        setScanProgress(stopScan.current?'Suivi arrêté. La collecte fournisseur continue ; utilisez Reprendre le résultat.':`${sourceName} : ${res?.discovered_urls||0} URL ajoutée(s) pendant ce passage, ${res?.known||0} déjà connues dans le résultat de collecte.`);
        await loadData();
      }
    }catch(e){if(mounted.current)setScanErrors([e instanceof Error?e.message:'Erreur scan']);}
    finally{if(mounted.current)setScanningSourceId(null);}
  }

  /* =======================================================
     TOGGLE SELECTION
  ======================================================== */

  function toggleSelection(
    idDiscovery: string
  ) {

    setSelectedIds(
      (prev) =>

        prev.includes(
          idDiscovery
        )
          ? prev.filter(
              (x) =>
                x !== idDiscovery
            )
          : [
              ...prev,
              idDiscovery,
            ]
    );

  }


  function toggleAllSelections() {

    if (
      selectedIds.length ===
      items.length
    ) {

      setSelectedIds([]);

      return;

    }

    setSelectedIds(
      items.map(
        (item) =>
          item.id_discovery
      )
    );

  }


  /* =======================================================
     STORE SELECTED
  ======================================================== */

  async function storeSelected() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      const res =
        await api.post(
          "/discovery/store",
          {
            discovery_ids:
              selectedIds,
          }
        );

      alert(
        `${
          res.stored || 0
        } URL(s) stockée(s)`
      );

      setSelectedIds([]);

      await loadData();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur stockage"
      );

    }

  }


  /* =======================================================
     DISMISS SELECTED
  ======================================================== */

  async function dismissSelected() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      const res =
        await api.post(
          "/discovery/ignore",
          {
            discovery_ids:
              selectedIds,
          }
        );

      alert(
        `${
          res.ignored || 0
        } URL(s) dismiss`
      );

      setSelectedIds([]);

      await loadData();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur dismiss"
      );

    }

  }


  /* =======================================================
     SEND TO STUDIO
  ======================================================== */

  async function sendToStudio() {

    if (
      selectedIds.length === 0
    ) {
      return;
    }

    try {

      const res =
        await api.post(
          "/discovery/manual",
          {
            discovery_ids:
              selectedIds,
          }
        );

      alert(
        `${
          res.manual || 0
        } URL(s) envoyée(s) au Studio`
      );

      setSelectedIds([]);

      await loadData();

    } catch (e) {

      console.error(e);

      alert(
        "❌ Erreur Studio"
      );

    }

  }


  /* =======================================================
     SOURCE FILTER
  ======================================================== */

  const filteredSources =
    sources.filter(
      (source) => {
  
        const mode = (
          source.acquisition_mode ||
          ""
        ).toUpperCase();
  
  
        // =====================================================
        // ACQUISITION MODE
        // =====================================================
  
        const matchesMode =
          sourceMode === "MANUAL"
            ? ["MANUAL","PDF_MANUAL","LINKEDIN_PROFILE","NEWSLETTER_MANUAL"].includes(mode)
            : (
                mode !== "" &&
                !["MANUAL","PDF_MANUAL","LINKEDIN_PROFILE","NEWSLETTER_MANUAL"].includes(mode)
              );
  
  
        // =====================================================
        // UNIVERSE
        // =====================================================
  
        const matchesUniverse =
          !universeId ||
          source.universe_id ===
            universeId;
  
  
        return (
          matchesMode &&
          matchesUniverse
        );
  
      }
    );


  /* =======================================================
     UI
  ======================================================== */

  return (

    <div className="space-y-8">

      {/* ===================================================
          HEADER
      ==================================================== */}

      <div className="flex justify-between items-center">

        <div>

          <h1 className="text-3xl font-semibold text-ratecard-blue">
            Discovery
          </h1>

          <p className="text-gray-500 mt-1">
            Détection automatique des nouvelles URLs
          </p>

        </div>


        {/* ===============================================
            SCAN ALL
        ================================================ */}

        <button
          onClick={() => void scanAll("ALL")}
          disabled={
            isScanning || loading || !sourcesReady
          }
          className="
            bg-ratecard-green
            px-5
            py-2
            text-white
            rounded
            disabled:opacity-50
            disabled:cursor-not-allowed
          "
        >

          {scanningAll
            ? "SCAN ALL EN COURS..."
            : "SCAN ALL SOURCES"}

        </button>
        <button onClick={()=>void scanAll("WEB")} disabled={isScanning||loading||!sourcesReady} className="border rounded px-4 py-2 disabled:opacity-50">Scanner hors LinkedIn Bright Data</button>
        <button onClick={()=>void scanAll("LINKEDIN")} disabled={isScanning||loading||!sourcesReady} className="border rounded px-4 py-2 disabled:opacity-50">Scanner LinkedIn Bright Data uniquement</button>

      </div>


      {/* ===================================================
          SOURCE MODE
      ==================================================== */}

      <div className="flex gap-2">

        <button
          onClick={() =>
            setSourceMode(
              "AUTOMATIC"
            )
          }
          disabled={
            isScanning
          }
          className={
            `
              px-3
              py-1
              rounded
              disabled:opacity-40
              disabled:cursor-not-allowed
              ${
                sourceMode ===
                "AUTOMATIC"
                  ? "bg-ratecard-blue text-white"
                  : "bg-gray-100"
              }
            `
          }
        >
          AUTOMATIC
        </button>


        <button
          onClick={() =>
            setSourceMode(
              "MANUAL"
            )
          }
          disabled={
            isScanning
          }
          className={
            `
              px-3
              py-1
              rounded
              disabled:opacity-40
              disabled:cursor-not-allowed
              ${
                sourceMode ===
                "MANUAL"
                  ? "bg-ratecard-blue text-white"
                  : "bg-gray-100"
              }
            `
          }
        >
          MANUAL
        </button>

        <select
          value={
            universeId
          }
          onChange={(e) =>
            setUniverseId(
              e.target.value
            )
          }
          disabled={
            isScanning
          }
          className="
            border
            rounded
            px-3
            py-1
            text-sm
            disabled:opacity-40
            disabled:cursor-not-allowed
          "
        >
        
          <option value="">
            Tous les univers
          </option>
        
          {universes.map(
            (universe) => (
        
              <option
                key={
                  universe.id_universe
                }
                value={
                  universe.id_universe
                }
              >
                {universe.label}
              </option>
        
            )
          )}
        
        </select>

      </div>


      {/* ===================================================
          SOURCES
      ==================================================== */}

      <section className="space-y-3" aria-label="Choix des sources">
        <div className="flex flex-wrap items-center gap-3">
          <label htmlFor="discovery-source" className="text-sm font-medium">Source</label>
          <select id="discovery-source" className="border rounded px-3 py-2 max-w-full" disabled={isScanning||loading||!sourcesReady}
            value={filteredSources.some(source=>source.source_id===pickedSourceId)?pickedSourceId:""}
            onChange={event=>setPickedSourceId(event.target.value)}>
            <option value="">Sélectionner une source</option>
            {filteredSources.map(source=><option key={source.source_id} value={source.source_id}>{source.name}</option>)}
          </select>
          {(() => {
            const source=filteredSources.find(item=>item.source_id===pickedSourceId);
            if(!source)return null;
            const mode=(source.acquisition_mode||"").toUpperCase();
            if(["MANUAL","PDF_MANUAL","NEWSLETTER_MANUAL","LINKEDIN_PROFILE"].includes(mode))return <span className="text-sm text-gray-500">Studio / manuel</span>;
            return <><button disabled={isScanning||loading||!sourcesReady} className="border rounded px-3 py-2 disabled:opacity-50" onClick={()=>void scanSource(source.source_id,source.name)}>Scanner cette source</button>{mode==="LINKEDIN_BRIGHTDATA"&&<button disabled={isScanning||loading||!sourcesReady} className="border rounded px-3 py-2 disabled:opacity-50" onClick={()=>void scanSource(source.source_id,source.name,true)}>Reprendre le résultat</button>}</>;
          })()}
        </div>
        <details className="rounded border bg-white">
          <summary className="cursor-pointer px-4 py-3 text-sm font-medium">Afficher / masquer les sources configurées ({filteredSources.length})</summary>
      <DiscoverySources
        sources={
          filteredSources
        }
        onScan={scanSource}
        onResume={(id,name)=>void scanSource(id,name,true)}
        scanningSourceId={
          scanningSourceId
        }
        scanningAll={
          scanningAll
        }
      />
        </details>
      </section>


      {/* ===================================================
          STATS
      ==================================================== */}

      <DiscoveryStats
        total={
          items.length
        }
      />


      <p className="text-sm text-gray-500">{items.length} URL actuellement à traiter dans Discovery, tous univers et sources confondus. Ce stock peut différer des ajouts du dernier scan.</p>
      {!!Object.keys(linkedinReports).length&&<details open className="border rounded bg-white p-4">
        <summary className="cursor-pointer font-medium">Bilan LinkedIn par source — ce passage</summary>
        <div className="overflow-x-auto mt-3"><table className="w-full text-sm text-left"><thead><tr>
          <th className="p-2">Compte</th><th className="p-2">État</th><th className="p-2">Lignes fournisseur reçues</th><th className="p-2">Déjà connus</th><th className="p-2">Ajoutés pendant ce passage</th><th className="p-2">Anomalies</th><th className="p-2">Détail</th>
        </tr></thead><tbody>{Object.values(linkedinReports).map(report=><tr key={report.sourceId} className="border-t align-top">
          <td className="p-2">{report.name}</td><td className="p-2">{report.status}</td><td className="p-2">{report.received??'—'}</td><td className="p-2">{report.known??'—'}</td><td className="p-2">{report.added}</td><td className="p-2">{report.issues??'—'}</td>
          <td className="p-2 text-amber-800">{report.error||(report.reused?'Résultat déjà terminé : aucune insertion effectuée par cette récupération.':'')}</td>
        </tr>)}</tbody></table></div>
        <p className="text-xs text-gray-500 mt-2">Les lignes reçues peuvent contenir des doublons et plusieurs anomalies pour un même post. Les colonnes ne constituent pas une partition du total. Ce tableau concerne les comptes effectivement interrogés pendant ce passage et reste affiché dans cette page.</p>
      </details>}

      {/* ===================================================
          ACTIONS
      ==================================================== */}

      {scanProgress&&<p role="status" className="p-3 rounded bg-blue-50">{scanProgress}</p>}
      {isScanning&&<button className="border rounded px-3 py-2" onClick={()=>{stopScan.current=true;}}>Arrêter le suivi après l’étape en cours</button>}
      {!!scanWarnings.length&&<details><summary>Avertissements ({scanWarnings.length})</summary><ul className="list-disc pl-5">{scanWarnings.map((w,i)=><li key={i}>{w}</li>)}</ul></details>}
      {!!scanErrors.length&&<div role="alert" className="text-red-700">{scanErrors.map((e,i)=><p key={i}>{e}</p>)}</div>}
      <DiscoveryActions
        disabled={isScanning||loading||!sourcesReady}
        selectedCount={
          selectedIds.length
        }
        onStore={
          storeSelected
        }
        onManual={
          sendToStudio
        }
        onDismiss={
          dismissSelected
        }
      />


      {/* ===================================================
          TABLE
      ==================================================== */}

      {loading ? (

        <div className="text-gray-500">
          Chargement...
        </div>

      ) : items.length === 0 ? (

        <div className="bg-white border rounded p-8 text-center text-gray-500">
          Aucune URL découverte.
        </div>

      ) : (

        <DiscoveryTable
          disabled={isScanning||loading||!sourcesReady}
          items={
            items
          }
          selectedIds={
            selectedIds
          }
          onToggle={
            toggleSelection
          }
          onToggleAll={
            toggleAllSelections
          }
        />

      )}

    </div>

  );

}
