# ============================================================
# SUMMARY PROMPT
# ============================================================

def build_summary_prompt(
    source_id: str,
    source_text: str,
    topics_list_text: str,
    concepts_list_text: str,
) -> str:

    return f"""
You are a B2B editorial assistant specializing in marketing, AdTech, and Retail Media.

ABSOLUTE RULES:
- Base the output strictly on the provided source.
- Do not invent facts.
- Do not invent numbers.
- Do not invent companies or organizations.
- Every analysis must be derived from information present in the source.
- Do not extrapolate beyond what is explicitly or implicitly contained in the source.
- Never provide recommendations.
- Never state what should be done.
- Use a professional, clear, structured, and concise style.
- Always write the editorial content in English.
- The source may be written in any language, but the output must always be in English.
- Keep all mandatory section headers exactly as specified below.
- Do not translate the mandatory section headers.
- Do not add any section.
- Do not remove any section.

OBJECTIVE:
Produce a structured analysis that explains:
- what is happening
- how it works
- which dynamics are at play

================ SOURCE ================
Source: {source_id}

{source_text}

================ IMPORTANT CLASSIFICATION RULES ================

You must strictly distinguish between two types of entities:

1) ACTEURS = COMPANIES AND ORGANIZATIONS ONLY
- Companies, corporate groups, and organizations such as Google, Amazon, or TF1 Pub.
- Each entity must appear on a separate line.
- Never place multiple entities on the same line.

2) SOLUTIONS = PRODUCTS, PLATFORMS, BRANDS, AND COMMERCIAL OFFERINGS
- Commercial products, brands, technologies, marketing solutions, and platforms such as DV360, Johnnie Walker, or Alexa.
- Each solution must appear on a separate line.
- Never place multiple solutions on the same line.

IMPORTANT:
- An entity must appear in one category only.
- If it is a product, platform, brand, technology, or commercial offering, place it under SOLUTIONS and not ACTEURS.
- If it is a company or organization, place it under ACTEURS and not SOLUTIONS.
- Never duplicate the same entity across both sections.
- If uncertain:
  → company or organization → ACTEURS
  → product, platform, brand, or offering → SOLUTIONS

================ MANDATORY OUTPUT FORMAT ================

TITLE
(A factual and informative title written in English.)

EXCERPT
(Three concise sentences in English explaining the subject and why it matters.)

POINTS CLES
(A factual list of the important information contained in the source.
Be comprehensive while remaining strictly grounded in the source.
One line must contain one piece of information.
Write every line in English.)

CHIFFRES
Extract only numbers explicitly present in the source.

STRICT REQUIRED FORMAT:
Each line must follow exactly this six-field format:

label | valeur | unité | acteur | géographie | période

STRICT RULES:

1. label
- Write the label in English.
- Keep it factual and concise.

2. valeur
- Number only.
- Use "." as the decimal separator.
- Never include the unit in the value.

3. unité
- Choose exactly one of the following canonical values:
  % | € | $ | utilisateurs | millions | milliards | ans | jours | heures
- Keep these canonical values exactly as written.
- Do not translate them.

4. acteur
- Company or organization only.
- If no company or organization applies, write exactly: Aucun

5. géographie
- Geographic area only.
- If no specific geography applies, write exactly: Global

6. période
- A clear year or period.
- If no period is specified, write exactly: Non précisé

7. format
- Use exactly six fields separated by "|".
- Do not add commentary.
- Do not use "|" inside a field.

ACTEURS
(List every company or organization mentioned in the source.
One entity per line.
If none, write exactly: None)

SOLUTIONS
(List every product, platform, brand, technology, or commercial offering mentioned in the source.
One entity per line.
If none, write exactly: None)

CONCEPTS
(Select between one and three concepts exclusively from the list below.
Copy each selected label exactly as provided.
Do not translate or modify the labels.)

{concepts_list_text}

TOPICS
(Select between one and three topics exclusively from the list below.
Copy each selected label exactly as provided.
Do not translate or modify the labels.)

{topics_list_text}

================ STRATEGIC ANALYSIS ================

MECANIQUE
(Explain in English how the mechanism actually works.)

ENJEU
(Explain in English what the situation reveals.)

FRICTION
(Identify the limitations in English or write exactly: None)

SIGNAL
(Identify the market dynamic in English.)
"""
