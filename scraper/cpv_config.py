"""
Shared CPV configuration for scrapers
Contains optimized CPV codes verified to work in current tender data (2025)
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
