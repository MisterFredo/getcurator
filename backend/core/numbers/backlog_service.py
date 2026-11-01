from typing import List, Dict, Optional

from config import BQ_PROJECT, BQ_DATASET
from utils.bigquery_utils import query_bq


TABLE_BACKLOG = f"{BQ_PROJECT}.{BQ_DATASET}.RATECARD_NUMBERS_BACKLOG"


# ============================================================
# BACKLOG LIST
# ============================================================

def get_numbers_backlog(
    limit: int = 100,
    decision: Optional[str] = None,
    query: Optional[str] = None,
) -> List[Dict]:

    conditions = ["TRUE"]
    params = {
        "limit": limit,
    }

    # ============================================================
    # FILTER DECISION
    # ============================================================

    if decision == "NULL":
        conditions.append("DECISION IS NULL")

    elif decision:
        conditions.append("DECISION = @decision")
        params["decision"] = decision

    # ============================================================
    # SEARCH
    # ============================================================

    if query:
        conditions.append("""
        (
            LOWER(IFNULL(LABEL, '')) LIKE LOWER(@query)
            OR LOWER(IFNULL(ACTOR, '')) LIKE LOWER(@query)
            OR LOWER(IFNULL(MARKET, '')) LIKE LOWER(@query)
            OR LOWER(IFNULL(RAW_LINE, '')) LIKE LOWER(@query)
        )
        """)
        params["query"] = f"%{query}%"

    where_sql = " AND ".join(conditions)

    # ============================================================
    # QUERY
    # ============================================================

    rows = query_bq(f"""
        SELECT
            ID_BACKLOG,
            ID_CONTENT,

            RAW_LINE,

            LABEL,
            VALUE,
            UNIT,

            ACTOR,
            MARKET,
            PERIOD,

            CONFIDENCE,
            DECISION,

            CREATED_AT

        FROM `{TABLE_BACKLOG}`

        WHERE {where_sql}

        ORDER BY CREATED_AT DESC

        LIMIT @limit
    """, params)

    return rows



def build_prompt(row: dict) -> str:

    return f"""
Tu es un analyste senior spécialisé dans les données
économiques, marketing, publicitaires et technologiques.

Ta mission est de sélectionner et structurer les chiffres
factuels qui peuvent enrichir la base de connaissances
GetCurator.

Ces chiffres seront utilisés pour :
- documenter des évolutions de marché
- analyser les performances des entreprises
- identifier des tendances et des signaux
- produire des rapports et des analyses
- construire des tableaux et graphiques lorsque cela est pertinent

--------------------------------------------------

1. OBJECTIF

Conserver les chiffres factuels qui apportent une
information exploitable à une analyse professionnelle.

Un chiffre n'a PAS besoin d'être directement comparable
entre plusieurs entreprises pour être conservé.

--------------------------------------------------

2. DECISION

KEEP :
- chiffre quantifié et intelligible
- indicateur économique, financier, marketing ou business
- évolution mesurée d'un indicateur
- taille ou projection de marché
- performance d'une entreprise ou d'un produit
- résultat d'une campagne ou d'une étude
- objectif chiffré clairement identifié
- donnée utile pour comprendre une tendance

IGNORE :
- chiffre purement anecdotique
- chiffre sans signification business identifiable
- donnée trop ambiguë pour être interprétée
- nombre utilisé uniquement comme référence ou identifiant
- chiffre dont la valeur ou l'unité est incohérente
- donnée impossible à contextualiser

--------------------------------------------------

3. CONTEXTE

Un chiffre peut être conservé si au moins un des
éléments suivants est identifiable :

- acteur
- marché
- période
- indicateur clairement défini

Une période manquante ne justifie pas automatiquement
un rejet.

Une donnée propre à une entreprise peut être utile,
même si elle n'est pas comparable à d'autres entreprises.

--------------------------------------------------

4. FIDÉLITÉ DES DONNÉES

- Ne jamais inventer une valeur
- Ne jamais inventer un acteur, un marché ou une période
- Préserver le sens exact du KPI
- Ne pas transformer une croissance en valeur absolue
- Ne pas transformer un objectif en résultat réalisé
- Ne pas transformer une borne ("plus de", "jusqu'à")
  en valeur exacte sans le signaler dans le label
- Conserver les unités monétaires
- Tenir compte de l'échelle fournie

IMPORTANT :
Si la valeur est exprimée en millions ou milliards,
convertir en valeur absolue lorsque cela est possible.

Exemples :
847 millions USD → value = 847000000, unit = USD
3 milliards USD → value = 3000000000, unit = USD
50 % → value = 50, unit = PERCENT
6.87 USD → value = 6.87, unit = USD

Ne jamais supposer une devise absente des données.

--------------------------------------------------

5. STRUCTURE SI KEEP

- decision
- label
- value
- unit
- actor
- market
- period
- confidence

Le label doit être :
- explicite
- autonome
- fidèle à la donnée originale
- suffisamment précis pour être réutilisé

--------------------------------------------------

6. UNITÉS AUTORISÉES

- PERCENT
- EUR
- USD
- MULTIPLIER
- USERS
- OTHER

Utiliser OTHER lorsque l'unité ne correspond
à aucune catégorie disponible.

--------------------------------------------------

7. PRINCIPES DE SÉLECTION

- Priorité à la pertinence analytique
- Ne pas imposer de quota de KEEP
- Ne pas rejeter un chiffre uniquement parce qu'il
  est spécifique à une entreprise
- Ne pas rejeter un KPI uniquement parce qu'il
  n'est pas standardisé entre entreprises
- En cas d'ambiguïté importante, choisir IGNORE

--------------------------------------------------

8. FORMAT

Retourne UNIQUEMENT un JSON valide :

{{
  "decision": "...",
  "label": "...",
  "value": null,
  "unit": "...",
  "actor": "...",
  "market": "...",
  "period": "...",
  "confidence": "..."
}}

Pour IGNORE, les champs non pertinents peuvent être null.

--------------------------------------------------

DONNÉES :

KPI : {row.get("label")}
Valeur : {row.get("value")}
Unité : {row.get("unit")}
Échelle : {row.get("scale")}
Acteur : {row.get("actor")}
Marché : {row.get("zone")}
Période : {row.get("period")}
"""
