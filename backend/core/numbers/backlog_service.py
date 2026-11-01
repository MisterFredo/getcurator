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


4. FIDÉLITÉ ET NORMALISATION DES DONNÉES

RÈGLES GÉNÉRALES

- Ne jamais inventer une valeur, un acteur, un marché ou une période.
- Préserver le sens exact de l'indicateur.
- Ne jamais transformer une croissance en valeur absolue.
- Ne jamais transformer un objectif en résultat réalisé.
- Ne jamais confondre une valeur monétaire et un volume.
- Ne jamais convertir une devise dans une autre devise.
- Ne jamais modifier une valeur pour la rendre plus attractive.

VALEURS ET ÉCHELLES

Convertir les millions et milliards en valeurs absolues :

- 847 millions USD → value = 847000000, unit = USD
- 3 milliards USD → value = 3000000000, unit = USD
- 20 millions de produits → value = 20000000, unit = OTHER
- 50 % → value = 50, unit = PERCENT

DEVISES

- $ ou USD, lorsqu'ils désignent des dollars américains → USD
- € ou EUR → EUR
- Ne jamais déduire une devise uniquement du pays de l'acteur.
- Si la devise n'est pas identifiable, utiliser OTHER.
- Ne jamais confondre une valeur en dollars et un pourcentage.

QUALIFICATION DES VALEURS

Conserver explicitement dans le label les qualifications :

- "more than" / "plus de" → borne inférieure
- "less than" / "moins de" → borne supérieure
- "up to" / "jusqu'à" → plafond
- "at least" / "au moins" → minimum
- "approximately" / "environ" → estimation
- "target" / "objectif" → objectif, non résultat
- "forecast" / "prévision" → prévision, non résultat

Exemples :

"More than 80% of monetization"
→ label = "Share of monetization from logged-in users exceeds 80%"
→ value = 80
→ unit = PERCENT

"Shopping campaign capacity up to 20 million products"
→ label = "Shopping campaign capacity of up to 20 million products"
→ value = 20000000
→ unit = OTHER

"Annual revenue target of 5 billion USD"
→ label = "Annual revenue target of 5 billion USD"
→ value = 5000000000
→ unit = USD

La valeur numérique représente le seuil indiqué.
Le label doit préciser lorsqu'il ne s'agit pas d'une valeur exacte.

ACTEURS

- Utiliser l'acteur fourni lorsqu'il est identifiable.
- Si l'acteur fourni est "Aucun" mais qu'une entreprise
  est explicitement nommée dans le KPI, utiliser cette entreprise.
- Ne jamais inventer un acteur.

PÉRIODES ET MARCHÉS

- Conserver les périodes et marchés explicitement fournis.
- Ne pas inventer une année lorsque seule une période
  comme Q3 ou October est disponible.
- Ne pas transformer "Non précisé" en période supposée.


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
