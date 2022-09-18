"""Enumerations of valid field values."""

US_STATES: dict[str, str] = {
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
}
"""Mapping of US state abbreviations to their full names."""

US_TERRITORIES: dict[str, str] = {
    "AS": "American Samoa",
    "DC": "District of Columbia",
    "GU": "Guam",
    "MP": "Northern Mariana Islands",
    "PR": "Puerto Rico",
    "VI": "Virgin Islands",
}
"""Mapping of US territory abbreviations to their full names."""

US_STATES_TERRITORIES: dict[str, str] = {**US_STATES, **US_TERRITORIES}

EPACEMS_STATES: list[str] = [
    state
    for state in US_STATES_TERRITORIES
    # AK and PR have data but only a few years, and that breaks the Datastore.
    # See https://github.com/catalyst-cooperative/pudl/issues/1264
    if state not in {"AK", "AS", "GU", "HI", "MP", "PR", "VI"}
]
"""The US states and territories that are present in the EPA CEMS dataset."""

CANADA_PROVINCES_TERRITORIES: dict[str, str] = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "CN": "Canada",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NS": "Nova Scotia",
    "NL": "Newfoundland and Labrador",
    "NT": "Northwest Territories",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edwards Island",
    "QC": "Quebec",
    "SK": "Saskatchewan",
    "YT": "Yukon Territory",
}
"""Mapping of Canadian province and territory abbreviations to their full names"""

NERC_REGIONS: list[str] = [
    "BASN",  # ASSESSMENT AREA Basin (WECC)
    "CALN",  # ASSESSMENT AREA California (WECC)
    "CALS",  # ASSESSMENT AREA California (WECC)
    "DSW",  # ASSESSMENT AREA Desert Southwest (WECC)
    "ASCC",  # Alaska
    "ISONE",  # ISO New England (NPCC)
    "ERCOT",  # lumped under TRE in 2017 Form instructions
    "NORW",  # ASSESSMENT AREA Northwest (WECC)
    "NYISO",  # ISO (NPCC)
    "PJM",  # RTO
    "ROCK",  # ASSESSMENT AREA Rockies (WECC)
    "ECAR",  # OLD RE Now part of RFC and SERC
    "FRCC",  # included in 2017 Form instructions, recently joined with SERC
    "HICC",  # Hawaii
    "MAAC",  # OLD RE Now part of RFC
    "MAIN",  # OLD RE Now part of SERC, RFC, MRO
    "MAPP",  # OLD/NEW RE Became part of MRO, resurfaced in 2010
    "MRO",  # RE included in 2017 Form instructions
    "NPCC",  # RE included in 2017 Form instructions
    "RFC",  # RE included in 2017 Form instructions
    "SERC",  # RE included in 2017 Form instructions
    "SPP",  # RE included in 2017 Form instructions
    "TRE",  # RE included in 2017 Form instructions (included ERCOT)
    "WECC",  # RE included in 2017 Form instructions
    "WSCC",  # OLD RE pre-2002 version of WECC
    "MISO",  # ISO unclear whether technically a regional entity, but lots of entries
    "ECAR_MAAC",
    "MAPP_WECC",
    "RFC_SERC",
    "SPP_WECC",
    "MRO_WECC",
    "ERCOT_SPP",
    "SPP_TRE",
    "ERCOT_TRE",
    "MISO_TRE",
    "VI",  # Virgin Islands
    "GU",  # Guam
    "PR",  # Puerto Rico
    "AS",  # American Samoa
    "UNK",
]
"""
North American Reliability Corporation (NERC) regions.

See https://www.eia.gov/electricity/data/eia411/#tabs_NERC-3.
"""

CUSTOMER_CLASSES: list[str] = [
    "commercial",
    "industrial",
    "direct_connection",
    "other",
    "residential",
    "total",
    "transportation",
]

TECH_CLASSES: list[str] = [
    "backup",  # WHERE Is this used? because removed from DG table b/c not a real component
    "chp_cogen",
    "combustion_turbine",
    "fuel_cell",
    "hydro",
    "internal_combustion",
    "other",
    "pv",
    "steam",
    "storage_pv",
    "all_storage",  # need 'all' as prefix so as not to confuse with other storage category
    "total",
    "virtual_pv",
    "wind",
]

REVENUE_CLASSES: list[str] = [
    "credits_or_adjustments",
    "delivery_customers",
    "other",
    "retail_sales",
    "sales_for_resale",
    "total",
    "transmission",
    "unbundled",
]

RELIABILITY_STANDARDS: list[str] = ["ieee_standard", "other_standard"]

FUEL_CLASSES: list[str] = [
    "gas",
    "oil",
    "other",
    "renewable",
    "water",
    "wind",
    "wood",
]

RTO_CLASSES: list[str] = [
    "caiso",
    "ercot",
    "isone",
    "miso",
    "nyiso",
    "other",
    "pjm",
    "spp",
]

EPACEMS_MEASUREMENT_CODES: list[str] = [
    "Calculated",
    "LME",
    "Measured",
    "Measured and Substitute",
    "Other",  # ¿Should be replaced with NA?
    "Substitute",
    "Undetermined",  # Should be replaced with NA
    "Unknown Code",  # Should be replaced with NA
]
"""Valid emissions measurement codes for the EPA CEMS hourly data."""

TECH_DESCRIPTIONS: set[str] = {
    "Conventional Hydroelectric",
    "Conventional Steam Coal",
    "Natural Gas Steam Turbine",
    "Natural Gas Fired Combustion Turbine",
    "Natural Gas Internal Combustion Engine",
    "Nuclear",
    "Natural Gas Fired Combined Cycle",
    "Petroleum Liquids",
    "Hydroelectric Pumped Storage",
    "Solar Photovoltaic",
    "Batteries",
    "Geothermal",
    "Municipal Solid Waste",
    "Wood/Wood Waste Biomass",
    "Onshore Wind Turbine",
    "Coal Integrated Gasification Combined Cycle",
    "Other Gases",
    "Landfill Gas",
    "All Other",
    "Other Waste Biomass",
    "Petroleum Coke",
    "Solar Thermal without Energy Storage",
    "Solar Thermal with Energy Storage",
    "Other Natural Gas",
    "Flywheels",
    "Offshore Wind Turbine",
    "Natural Gas with Compressed Air Storage",
    "Hydrokinetic",
}
"""Valid technology descriptions from the EIA plant parts list."""

PLANT_PARTS: set[str] = {
    "plant",
    "plant_unit",
    "plant_prime_mover",
    "plant_technology",
    "plant_prime_fuel",
    "plant_ferc_acct",
    "plant_operating_year",
    "plant_gen",
}

"""The plant parts in the EIA plant parts list."""
