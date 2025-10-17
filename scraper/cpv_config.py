"""
Shared CPV configuration for scrapers
Contains optimized CPV codes verified to work in current tender data (2025)
Also contains comprehensive keywords for Evergabe scraping
"""

# OPTIMIZED CPV codes - VERIFIED to work in current TED data (2025)
# 13 out of 19 optimized CPVs are found in today's TED data (68.4% success rate)
# Using the working subset of optimized CPV codes from SIMAP analysis
OPTIMIZED_CPV_CODES = [
    "71311200", "72322000", "73100000", "79300000", "79310000", "79311000", 
    "79311200", "79311400", "79311410", "79320000", "79416000", "79419000", "98300000"
]

# Original CPV codes (for reference)
ORIGINAL_CPV_CODES = [
    "72000000", "79300000", "73100000", "79311400", "72314000",
    "79416000", "72320000", "98300000", "79310000", "79000000", "79311410"
]

# CPV code descriptions for reference
CPV_DESCRIPTIONS = {
    "71311200": "Services provided by engineering design services",
    "72322000": "Data storage services", 
    "73100000": "Research and experimental development services",
    "79300000": "Market and economic research; polling and statistics",
    "79310000": "Market research services",
    "79311000": "Market research services",
    "79311200": "Market research services",
    "79311400": "Market research services",
    "79311410": "Market research services",
    "79320000": "Market and economic research; polling and statistics",
    "79416000": "Business and management consultancy and related services",
    "79419000": "Evaluation consultancy services",
    "98300000": "Miscellaneous services"
}

# WORKING KEYWORDS from old scraper that found 10+ results
EVERGABE_KEYWORDS = [
    # Study / Studie
    "study", "studie", "étude", "etude", "studio",

    # Analysis / Analyse
    "analysis", "analyse", "analisi",

    # Economy / Wirtschaft / Ökonomie
    "economy", "economics", "wirtschaft", "ökonomie", "economie", "economia",

    # Benchmarking
    "benchmark", "benchmarking",

    # Wirtschaftsberatung (economic/business consulting)
    "wirtschaftsberatung", "consulting", "conseil", "consulenza",

    # CPV & categories
    "72000000", "79300000",
    "it-dienste",
    "beratung, software-entwicklung, internet und hilfestellung",
    "markt- und wirtschaftsforschung", "umfragen und statistiken",

    # Dienstleistung
    "dienstleistung", "service", "prestation", "prestazione",

    # Ausschreibung
    "ausschreibung", "appel d'offres", "appels d'offres", "gara", "procurement",

    # Offenes Verfahren
    "offenes verfahren", "procédure ouverte", "procedure ouverte", "procedura aperta",

    # BKS / Bundesamt für Statistik / OFS
    "bks",
    "bundesamt für statistik",
    "office fédéral de la statistique", "office federal de la statistique",
    "ufficio federale di statistica",
    "federal statistical office", "ofs", "bfs",

    # SECO / Staatssekretariat für Wirtschaft
    "seco", "staatssekretariat für wirtschaft",
    "secrétariat d'état à l'économie", "secretariat d'etat a l'economie",
    "segretariato di stato dell'economia",

    # Cantons / regions (Zürich, Luzern, generic canton/region)
    "kanton zürich", "kanton zuerich", "canton de zurich", "cantone zurigo",
    "kanton luzern", "canton de lucerne", "cantone lucerna",
    "kanton", "canton", "cantone",
    "region", "regionen", "région", "regione",

    # Bundesamt für… (generic)
    "bundesamt für", "bundesamt fuer",

    # BBL
    "bundesamt für bauten und logistik", "bundesamt fuer bauten und logistik", "bbl",

    # Index (e.g. Verbraucherindex)
    "index", "verbraucherindex", "price index", "indice des prix", "indice dei prezzi",

    # Wirtschaftsforschung
    "wirtschaftsforschung", "economic research", "recherche économique",
    "recherche economique", "ricerca economica"
]
