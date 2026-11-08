"""Persistent triage for normalized LinkedIn company labels; never delete contacts."""
import json
from fastapi import HTTPException
from core.contact import service as contacts
TABLE=f'{contacts.BASE}.RATECARD_CONTACT_LINKEDIN_COMPANY_RULE'

def rules():
    return {r['COMPANY_KEY']:r['DECISION'] for r in contacts.query(f'SELECT COMPANY_KEY,DECISION FROM `{TABLE}`')}

def effective(options,rule):
    if rule=='IGNORE':return [],'IGNORED'
    if len(options)==1:return options,'MATCHED'
    if rule=='LATER':return options,'LATER'
    return options,'AMBIGUOUS' if options else 'UNMATCHED'

def decide(run_id,payload):
    from core.contact import linkedin_import as m
    with m.lock(run_id),contacts.scope_lock():
        run=m.read(run_id)
        if run['status'] not in ('READY','IMPORTED') or run.get('change_job',{}).get('status')=='RUNNING':
            raise HTTPException(409,'Terminer le traitement en cours avant de modifier le tri')
        candidates,_=m.candidates(run['rows'])
        labels={r['group_key']:r['company_label'] for r in candidates}
        keys=list(dict.fromkeys(payload.group_keys))
        if any(k not in labels for k in keys):raise HTTPException(400,'Société absente de cet aperçu')
        if payload.decision=='MATCH':
            if not payload.id_company:raise HTTPException(422,'Société GetCurator obligatoire')
            company=contacts.query(f'SELECT IS_ACTIVE FROM `{contacts.COMPANY}` WHERE ID_COMPANY=@company',[contacts.p('company','STRING',payload.id_company)])
            if not company or not company[0]['IS_ACTIVE']:raise HTTPException(409,'Société GetCurator absente ou inactive')
            if any(not labels[k].strip() for k in keys):raise HTTPException(422,'Un libellé société vide ne peut pas être mémorisé comme rapprochement global')
        records=[{'key':k,'label':labels[k]} for k in keys]
        params=[contacts.p('rows','STRING',json.dumps(records,ensure_ascii=False)),contacts.p('decision','STRING',payload.decision),contacts.p('company','STRING',payload.id_company)]
        contacts.query(f'''CREATE TEMP TABLE choices AS
          SELECT JSON_VALUE(j,'$.key') COMPANY_KEY,JSON_VALUE(j,'$.label') LINKEDIN_LABEL
          FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@rows))) j;
          BEGIN TRANSACTION;
          IF @decision IN ('IGNORE','LATER') THEN
            MERGE `{TABLE}` T USING choices S ON T.COMPANY_KEY=S.COMPANY_KEY
            WHEN MATCHED THEN UPDATE SET DECISION=@decision,LINKEDIN_LABEL=S.LINKEDIN_LABEL,UPDATED_AT=CURRENT_TIMESTAMP()
            WHEN NOT MATCHED THEN INSERT(COMPANY_KEY,LINKEDIN_LABEL,DECISION,CREATED_AT,UPDATED_AT)
              VALUES(S.COMPANY_KEY,S.LINKEDIN_LABEL,@decision,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP());
            DELETE FROM `{m.MAP}` WHERE COMPANY_KEY IN (SELECT COMPANY_KEY FROM choices);
          ELSE
            DELETE FROM `{TABLE}` WHERE COMPANY_KEY IN (SELECT COMPANY_KEY FROM choices);
            IF @decision='RESET' THEN
              DELETE FROM `{m.MAP}` WHERE COMPANY_KEY IN (SELECT COMPANY_KEY FROM choices);
            END IF;
            IF @decision='MATCH' THEN
              MERGE `{m.MAP}` T USING choices S ON T.COMPANY_KEY=S.COMPANY_KEY
              WHEN MATCHED THEN UPDATE SET ID_COMPANY=@company,LINKEDIN_LABEL=S.LINKEDIN_LABEL,UPDATED_AT=CURRENT_TIMESTAMP()
              WHEN NOT MATCHED THEN INSERT(COMPANY_KEY,LINKEDIN_LABEL,ID_COMPANY,CREATED_AT,UPDATED_AT)
                VALUES(S.COMPANY_KEY,S.LINKEDIN_LABEL,@company,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP());
            END IF;
          END IF;
          COMMIT TRANSACTION;''',params)
        return {'status':'ok','decision':payload.decision,'group_keys':keys,'id_company':payload.id_company}


def match_batch(run_id,payload):
    """One explicit approval, one BQ script, distinct target company per label."""
    from core.contact import linkedin_import as m
    from google.api_core.exceptions import BadRequest
    with m.lock(run_id),contacts.scope_lock():
        run=m.read(run_id)
        if run['status'] not in ('READY','IMPORTED') or run.get('change_job',{}).get('status')=='RUNNING':
            raise HTTPException(409,'Terminer le traitement en cours avant de valider les rapprochements')
        rows,_=m.candidates(run['rows']);labels={r['group_key']:r['company_label'] for r in rows}
        seen=set();records=[]
        for mapping in payload.mappings:
            key=mapping.group_key
            if key in seen:raise HTTPException(400,'Un libellé société figure plusieurs fois dans le lot')
            seen.add(key)
            if key not in labels or not labels[key].strip():raise HTTPException(400,'Libellé société absent ou vide dans cet aperçu')
            records.append({'key':key,'label':labels[key],'company':mapping.id_company})
        try:
            contacts.query(f"""CREATE TEMP TABLE choices AS
              SELECT JSON_VALUE(j,'$.key') COMPANY_KEY,JSON_VALUE(j,'$.label') LINKEDIN_LABEL,
                JSON_VALUE(j,'$.company') ID_COMPANY
              FROM UNNEST(JSON_QUERY_ARRAY(PARSE_JSON(@rows))) j;
              BEGIN TRANSACTION;
              ASSERT NOT EXISTS (
                SELECT 1 FROM choices s
                LEFT JOIN `{contacts.COMPANY}` c ON c.ID_COMPANY=s.ID_COMPANY AND c.IS_ACTIVE=TRUE
                WHERE c.ID_COMPANY IS NULL
              ) AS 'MATCH_BATCH_COMPANY_UNAVAILABLE';
              ASSERT NOT EXISTS (
                SELECT 1 FROM choices s INNER JOIN `{TABLE}` r ON r.COMPANY_KEY=s.COMPANY_KEY
                WHERE r.DECISION='IGNORE'
              ) AS 'MATCH_BATCH_COMPANY_IGNORED';
              DELETE FROM `{TABLE}` WHERE COMPANY_KEY IN (SELECT COMPANY_KEY FROM choices);
              MERGE `{m.MAP}` T USING choices S ON T.COMPANY_KEY=S.COMPANY_KEY
              WHEN MATCHED THEN UPDATE SET ID_COMPANY=S.ID_COMPANY,LINKEDIN_LABEL=S.LINKEDIN_LABEL,UPDATED_AT=CURRENT_TIMESTAMP()
              WHEN NOT MATCHED THEN INSERT(COMPANY_KEY,LINKEDIN_LABEL,ID_COMPANY,CREATED_AT,UPDATED_AT)
                VALUES(S.COMPANY_KEY,S.LINKEDIN_LABEL,S.ID_COMPANY,CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP());
              COMMIT TRANSACTION;""",[contacts.p('rows','STRING',json.dumps(records,ensure_ascii=False))])
        except BadRequest as exc:
            if 'MATCH_BATCH_COMPANY_UNAVAILABLE' in str(exc):raise HTTPException(409,'Une société cible est absente ou inactive ; corriger le lot puis réessayer') from exc
            if 'MATCH_BATCH_COMPANY_IGNORED' in str(exc):raise HTTPException(409,'Une société a été ignorée ; la rétablir avant de valider son rapprochement') from exc
            raise
        return {'status':'ok','updated':len(records),'mappings':[{'group_key':r['key'],'id_company':r['company']} for r in records]}
