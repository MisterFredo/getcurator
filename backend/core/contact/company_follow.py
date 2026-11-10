"""Employee following is exclusively opt-in. Company eligibility never grants it.

Keep these two functions for existing import, matching and employer-check callers.
They deliberately perform no writes and cannot reactivate a contact.
"""

def sync_sql(scope='TRUE'):
    return '-- Employee following requires an explicit contact selection.\n'


def default_follow(company_id, linkedin_url, active=True):
    return False
