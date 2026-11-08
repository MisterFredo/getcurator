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
