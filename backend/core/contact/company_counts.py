"""Current contact affiliations, one aggregate query for the company list."""
from core.contact import service

def get_company_contact_counts():
    rows=service.query(f'''SELECT a.ID_COMPANY,COUNT(DISTINCT a.ID_CONTACT) AS CONTACT_COUNT
      FROM `{service.AFFILIATION}` a
      INNER JOIN `{service.CONTACT}` c ON c.ID_CONTACT=a.ID_CONTACT
      WHERE a.ENDED_AT IS NULL
      GROUP BY a.ID_COMPANY''')
    return {'status':'ok','counts':{r['ID_COMPANY']:int(r['CONTACT_COUNT']) for r in rows}}
