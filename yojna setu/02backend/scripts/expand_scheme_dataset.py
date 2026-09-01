"""
Task-034 Scheme Dataset Expansion Script
Appends 8 new verified government schemes (SIH26092-057 to SIH26092-064)
without modifying any of the 56 existing schemes.
"""

import os
import sys
import json
import csv
from datetime import datetime, timezone

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "04data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.session import SessionLocal
from app.models import Scheme, SchemeRule, SchemeDocument, SchemeVerification, SchemeChangelog

NEW_SCHEMES = [
    {
        "scheme_id": "SIH26092-057",
        "scheme_code": "NSFDC-MSY",
        "scheme_name": "NSFDC Mahila Samriddhi Yojana (MSY)",
        "scheme_type": "MICRO_FINANCE; LOAN; SUBSIDY",
        "short_description": "Concessional micro-credit assistance up to ₹1,40,000 for Scheduled Caste women entrepreneurs and Self-Help Groups (SHGs) for income generation activities.",
        "detailed_description": "NSFDC provides financial assistance in the form of micro-credit through State Channelizing Agencies (SCAs) to eligible Scheduled Caste women entrepreneurs and women SHGs at 4% per annum interest rate.",
        "purpose": "Empowering women from the Scheduled Caste community by providing micro-credit support at concessional interest rates for small businesses and self-employment.",
        "source_organization": "National Scheduled Castes Finance and Development Corporation (NSFDC)",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "State Channelizing Agencies (SCAs) / RRBs / Nationalized Banks",
        "target_beneficiary": "Scheduled Caste Women Entrepreneurs and Women Self-Help Groups",
        "applicant_types": "INDIVIDUAL, SHG, WOMAN",
        "marginalized_group": "SC",
        "target_groups": "SC, WOMEN, SHG",
        "entrepreneur_type": "MICRO_ENTERPRISE",
        "sc_required": "TRUE",
        "social_category": "SC",
        "gender_condition": "FEMALE_ONLY",
        "gender_requirement": "FEMALE",
        "age_min": 18,
        "age_max": 50,
        "income_limit": 300000.0,
        "income_operator": "<=",
        "income_definition": "Annual Family Income",
        "support_type": "MICRO_CREDIT",
        "loan_available": "TRUE",
        "min_loan_amount": 10000.0,
        "max_loan_amount": 140000.0,
        "minimum_loan_amount": 10000.0,
        "maximum_loan_amount": 140000.0,
        "financing_percentage": 90.0,
        "beneficiary_contribution_percentage": 10.0,
        "interest_rate_min": 4.0,
        "interest_rate_max": 4.0,
        "interest_rate_type": "FIXED",
        "repayment_period_min_months": 36,
        "repayment_period_max_months": 48,
        "moratorium_min_months": 3,
        "moratorium_max_months": 6,
        "collateral_required": "FALSE",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://pmsuraj.dosje.gov.in/",
        "official_portal": "https://pmsuraj.dosje.gov.in/",
        "official_source_url": "https://nsfdc.nic.in/",
        "source_document": "NSFDC Mahila Samriddhi Yojana Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-058",
        "scheme_code": "NSFDC-GBS",
        "scheme_name": "NSFDC Green Business Scheme (GBS)",
        "scheme_type": "TERM_LOAN; CONCESSIONAL_FINANCE",
        "short_description": "Concessional term loans up to ₹30 Lakh covering up to 90% of unit costs for Scheduled Caste entrepreneurs undertaking climate change mitigation and green energy enterprises.",
        "detailed_description": "NSFDC provides financial assistance for climate adaptation, solar gadgets, battery electric vehicles (E-rickshaws), poly houses, and eco-friendly income-generating units.",
        "purpose": "Promoting green entrepreneurship and sustainable livelihood for Scheduled Caste beneficiaries through climate-friendly business models.",
        "source_organization": "National Scheduled Castes Finance and Development Corporation (NSFDC)",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "State Channelizing Agencies (SCAs)",
        "target_beneficiary": "Scheduled Caste individuals and enterprise units in green / climate-friendly sectors",
        "applicant_types": "INDIVIDUAL, ENTREPRENEUR, MSME",
        "marginalized_group": "SC",
        "target_groups": "SC, ENTREPRENEURS",
        "entrepreneur_type": "GREEN_ENTERPRISE",
        "sc_required": "TRUE",
        "social_category": "SC",
        "age_min": 18,
        "age_max": 55,
        "income_limit": 300000.0,
        "income_operator": "<=",
        "income_definition": "Annual Family Income",
        "sector": "GREEN_ENERGY; ENVIRONMENT; TRANSPORT",
        "support_type": "TERM_LOAN",
        "loan_available": "TRUE",
        "min_project_cost": 50000.0,
        "max_project_cost": 3000000.0,
        "min_loan_amount": 45000.0,
        "max_loan_amount": 2700000.0,
        "minimum_loan_amount": 45000.0,
        "maximum_loan_amount": 2700000.0,
        "financing_percentage": 90.0,
        "beneficiary_contribution_percentage": 10.0,
        "interest_rate_min": 4.0,
        "interest_rate_max": 6.0,
        "interest_rate_type": "CONCESSIONAL",
        "repayment_period_min_months": 60,
        "repayment_period_max_months": 120,
        "moratorium_min_months": 6,
        "moratorium_max_months": 12,
        "collateral_required": "CONDITIONAL",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://pmsuraj.dosje.gov.in/",
        "official_portal": "https://pmsuraj.dosje.gov.in/",
        "official_source_url": "https://nsfdc.nic.in/",
        "source_document": "NSFDC Green Business Scheme Policy Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-059",
        "scheme_code": "NSTFDC-ASRY",
        "scheme_name": "NSTFDC Adivasi Shiksha Rrinn Yojana (ASRY)",
        "scheme_type": "EDUCATION_LOAN; CONCESSIONAL_FINANCE",
        "short_description": "Concessional education loan up to ₹10 Lakh per eligible ST family for pursuing professional and technical higher education in India.",
        "detailed_description": "NSTFDC extends concessional education loans to Scheduled Tribe students at 6% p.a. interest, with interest subsidy during moratorium eligible under Ministry of Education guidelines.",
        "purpose": "Financial assistance for technical and professional higher education (including engineering, medical, MBA, MCA, PhD) for tribal students.",
        "source_organization": "National Scheduled Tribes Finance and Development Corporation (NSTFDC)",
        "ministry": "Ministry of Tribal Affairs",
        "implementing_agency": "State Channelizing Agencies (SCAs)",
        "target_beneficiary": "Scheduled Tribe (ST) students pursuing professional or technical higher education",
        "applicant_types": "STUDENT, INDIVIDUAL",
        "marginalized_group": "ST",
        "target_groups": "ST, STUDENTS, YOUTH",
        "social_category": "ST",
        "education_applicable": "TRUE",
        "age_min": 18,
        "age_max": 35,
        "income_limit": 300000.0,
        "income_operator": "<=",
        "income_definition": "Annual Family Income",
        "support_type": "EDUCATION_LOAN",
        "loan_available": "TRUE",
        "min_loan_amount": 50000.0,
        "max_loan_amount": 1000000.0,
        "minimum_loan_amount": 50000.0,
        "maximum_loan_amount": 1000000.0,
        "financing_percentage": 90.0,
        "beneficiary_contribution_percentage": 10.0,
        "interest_rate_min": 6.0,
        "interest_rate_max": 6.0,
        "interest_rate_type": "CONCESSIONAL",
        "repayment_period_min_months": 60,
        "repayment_period_max_months": 120,
        "moratorium_min_months": 12,
        "moratorium_max_months": 24,
        "collateral_required": "FALSE",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://nstfdc.tribal.gov.in/",
        "official_portal": "https://nstfdc.tribal.gov.in/",
        "official_source_url": "https://nstfdc.tribal.gov.in/",
        "source_document": "NSTFDC Adivasi Shiksha Rrinn Yojana Operational Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-060",
        "scheme_code": "CEGSSC",
        "scheme_name": "Credit Enhancement Guarantee Scheme for Scheduled Castes (CEGSSC)",
        "scheme_type": "CREDIT_GUARANTEE; ENTREPRENEURSHIP",
        "short_description": "Credit guarantee coverage from ₹15 Lakh to ₹5 Crore for collateral-free bank loans sanctioned to enterprises promoted by Scheduled Caste entrepreneurs.",
        "detailed_description": "Ministry of Social Justice & Empowerment initiative managed by IFCI Ltd. providing 100% to 60% credit guarantee cover on loans to SC-promoted enterprises (min 51% SC ownership).",
        "purpose": "Encouraging SC entrepreneurs to establish and expand innovation and growth-oriented manufacturing, trading, and service enterprises without third-party collateral.",
        "source_organization": "Ministry of Social Justice and Empowerment",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "IFCI Ltd. / Member Lending Institutions (MLIs)",
        "target_beneficiary": "Scheduled Caste entrepreneurs, registered proprietorships, partnerships, and companies with >51% SC stake",
        "applicant_types": "INDIVIDUAL, ENTREPRENEUR, MSME, COMPANY",
        "marginalized_group": "SC",
        "target_groups": "SC, ENTREPRENEURS, MSME",
        "sc_required": "TRUE",
        "social_category": "SC",
        "age_min": 18,
        "support_type": "CREDIT_GUARANTEE",
        "loan_available": "TRUE",
        "minimum_loan_amount": 1500000.0,
        "min_loan_amount": 1500000.0,
        "maximum_loan_amount": 50000000.0,
        "max_loan_amount": 50000000.0,
        "financing_percentage": 100.0,
        "collateral_required": "FALSE",
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://www.ifcicegssc.in/",
        "official_portal": "https://www.ifcicegssc.in/",
        "official_source_url": "https://www.ifcicegssc.in/",
        "source_document": "CEGSSC Official Scheme Guidelines (IFCI / MoSJE)",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-061",
        "scheme_code": "PMVDY",
        "scheme_name": "Pradhan Mantri Van Dhan Yojana (PMVDY)",
        "scheme_type": "LIVELIHOOD; VALUE_ADDITION; SHG_ENTERPRISE",
        "short_description": "Livelihood generation scheme for tribal forest gatherers and SHGs through Van Dhan Vikas Kendras (VDVKs) for processing, packaging, and marketing Minor Forest Produce (MFP).",
        "detailed_description": "TRIFED initiative under Ministry of Tribal Affairs setting up grassroots Van Dhan Vikas Kendras (15 SHGs of 20 gatherers each) with skill training, working capital, and processing equipment.",
        "purpose": "Transforming tribal gatherers into entrepreneurs by adding value to forest produce, ensuring fair remunerative prices, and eliminating middleman exploitation.",
        "source_organization": "TRIFED",
        "ministry": "Ministry of Tribal Affairs",
        "implementing_agency": "TRIFED / State Nodal Agencies (SND) / Van Dhan Vikas Kendras",
        "target_beneficiary": "Tribal forest gatherers, artisans, and women Self-Help Groups in tribal districts",
        "applicant_types": "SHG, INDIVIDUAL, TRIBAL_GATHERER",
        "marginalized_group": "ST",
        "target_groups": "ST, WOMEN, SHG, FOREST_GATHERERS",
        "social_category": "ST",
        "sector": "FORESTRY; AGRO_PROCESSING; RURAL_ENTERPRISE",
        "support_type": "GRANT; TOOLKIT; WORKING_CAPITAL",
        "grant_available": "TRUE",
        "training_available": "TRUE",
        "equipment_support": "TRUE",
        "market_support": "TRUE",
        "collateral_required": "FALSE",
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://trifed.tribal.gov.in/",
        "official_portal": "https://trifed.tribal.gov.in/",
        "official_source_url": "https://trifed.tribal.gov.in/",
        "source_document": "TRIFED Van Dhan Yojana Operational Manual",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-062",
        "scheme_code": "KVIC-GVY",
        "scheme_name": "Gramodyog Vikas Yojana (GVY)",
        "scheme_type": "SKILL_DEVELOPMENT; TOOLKIT_SUBSIDY; ARTISAN_SUPPORT",
        "short_description": "Skill development, technological modernization, and distribution of advanced toolkits/machinery for rural artisans in pottery, beekeeping/honey, agro-processing, and village industries.",
        "detailed_description": "Central Sector Scheme by KVIC providing customized technical training, electric pottery wheels, bee boxes, agarbatti/paper machines, and CFC infrastructure for village artisans.",
        "purpose": "Revitalizing traditional village industries, creating sustainable rural self-employment, and enhancing income levels of grassroots artisans.",
        "source_organization": "Khadi and Village Industries Commission (KVIC)",
        "ministry": "Ministry of Micro, Small and Medium Enterprises",
        "implementing_agency": "KVIC / State KVIB / DIC",
        "target_beneficiary": "Rural traditional artisans, craftspersons, unemployed rural youth, and SHGs",
        "applicant_types": "INDIVIDUAL, ARTISAN, SHG",
        "target_groups": "ARTISANS, RURAL_YOUTH, WOMEN, SC, ST, OBC",
        "sector": "VILLAGE_INDUSTRIES; ARTISAN; AGRO_PROCESSING; HANDICRAFT",
        "support_type": "TOOLKIT; TRAINING; INFRASTRUCTURE",
        "age_min": 18,
        "age_max": 55,
        "training_available": "TRUE",
        "equipment_support": "TRUE",
        "market_support": "TRUE",
        "collateral_required": "FALSE",
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://www.kviconline.gov.in/",
        "official_portal": "https://www.kviconline.gov.in/",
        "official_source_url": "https://www.kviconline.gov.in/",
        "source_document": "KVIC Gramodyog Vikas Yojana Guidelines (MSME)",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-063",
        "scheme_code": "NSFDC-MKY",
        "scheme_name": "NSFDC Mahila Kisan Yojana (MKY)",
        "scheme_type": "AGRICULTURE_LOAN; SUBSIDY; CONCESSIONAL_FINANCE",
        "short_description": "Concessional loans up to ₹50,000 with capital subsidy assistance for Scheduled Caste women engaged in agriculture, dairy farming, poultry, and allied rural activities.",
        "detailed_description": "NSFDC scheme implemented via State Channelizing Agencies offering 5% p.a. concessional loans and subsidy for rural SC women farmers and livestock rearers.",
        "purpose": "Economic upliftment and asset creation for SC women in agriculture and allied rural sectors.",
        "source_organization": "National Scheduled Castes Finance and Development Corporation (NSFDC)",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "State Channelizing Agencies (SCAs)",
        "target_beneficiary": "Scheduled Caste women farmers, dairy workers, and rural agricultural laborers",
        "applicant_types": "INDIVIDUAL, WOMAN, FARMER",
        "marginalized_group": "SC",
        "target_groups": "SC, WOMEN, FARMERS",
        "sc_required": "TRUE",
        "social_category": "SC",
        "gender_condition": "FEMALE_ONLY",
        "gender_requirement": "FEMALE",
        "age_min": 18,
        "age_max": 50,
        "income_limit": 300000.0,
        "income_operator": "<=",
        "income_definition": "Annual Family Income",
        "sector": "AGRICULTURE; DAIRY; ALLIED_FARMING",
        "support_type": "CONCESSIONAL_LOAN; SUBSIDY",
        "loan_available": "TRUE",
        "max_project_cost": 50000.0,
        "min_loan_amount": 10000.0,
        "max_loan_amount": 50000.0,
        "minimum_loan_amount": 10000.0,
        "maximum_loan_amount": 50000.0,
        "financing_percentage": 90.0,
        "beneficiary_contribution_percentage": 10.0,
        "interest_rate_min": 5.0,
        "interest_rate_max": 5.0,
        "interest_rate_type": "CONCESSIONAL",
        "repayment_period_min_months": 36,
        "repayment_period_max_months": 48,
        "moratorium_min_months": 3,
        "moratorium_max_months": 6,
        "collateral_required": "FALSE",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://pmsuraj.dosje.gov.in/",
        "official_portal": "https://pmsuraj.dosje.gov.in/",
        "official_source_url": "https://nsfdc.nic.in/",
        "source_document": "NSFDC Mahila Kisan Yojana Scheme Circular",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-064",
        "scheme_code": "NBCFDC-SHILP",
        "scheme_name": "NBCFDC Shilp Sampada Scheme",
        "scheme_type": "ARTISAN_LOAN; CONCESSIONAL_FINANCE",
        "short_description": "Concessional term loans up to ₹10 Lakh for Backward Classes (OBC) artisans and craftspersons to upgrade production technology, purchase modern tools, and establish artisan enterprises.",
        "detailed_description": "NBCFDC scheme providing financial assistance up to 85% of project cost at 6% p.a. interest to traditional artisans and craftspersons belonging to Backward Classes.",
        "purpose": "Modernization of artisan tools, working capital support, and sustainable self-employment for OBC craftspersons.",
        "source_organization": "National Backward Classes Finance and Development Corporation (NBCFDC)",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "State Channelizing Agencies (SCAs)",
        "target_beneficiary": "Backward Classes (OBC) artisans, traditional craftspeople, and weavers",
        "applicant_types": "INDIVIDUAL, ARTISAN, ENTREPRENEUR",
        "marginalized_group": "OBC",
        "target_groups": "OBC, ARTISANS, CRAFTSPERSONS",
        "social_category": "OBC",
        "sector": "ARTISAN; HANDICRAFT; TRADITIONAL_OCCUPATIONS",
        "support_type": "TERM_LOAN",
        "loan_available": "TRUE",
        "min_project_cost": 50000.0,
        "max_project_cost": 1000000.0,
        "min_loan_amount": 42500.0,
        "max_loan_amount": 850000.0,
        "minimum_loan_amount": 42500.0,
        "maximum_loan_amount": 850000.0,
        "financing_percentage": 85.0,
        "beneficiary_contribution_percentage": 15.0,
        "interest_rate_min": 6.0,
        "interest_rate_max": 6.0,
        "interest_rate_type": "CONCESSIONAL",
        "age_min": 18,
        "age_max": 55,
        "income_limit": 300000.0,
        "income_operator": "<=",
        "income_definition": "Annual Family Income",
        "repayment_period_min_months": 60,
        "repayment_period_max_months": 120,
        "moratorium_min_months": 6,
        "moratorium_max_months": 12,
        "collateral_required": "CONDITIONAL",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://nbcfdc.nic.in/",
        "official_portal": "https://nbcfdc.nic.in/",
        "official_source_url": "https://nbcfdc.nic.in/",
        "source_document": "NBCFDC Shilp Sampada Lending Guidelines",
        "scheme_status": "ACTIVE"
    }
]

NEW_RULES = [
    # SIH26092-057 (NSFDC MSY)
    {"rule_id": "RULE-057-01", "scheme_id": "SIH26092-057", "field": "social_category", "operator": "IN", "value": "SC", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to Scheduled Caste (SC)", "source_document": "NSFDC MSY Guidelines", "active": True},
    {"rule_id": "RULE-057-02", "scheme_id": "SIH26092-057", "field": "gender", "operator": "=", "value": "FEMALE", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Scheme is specifically for women beneficiaries", "source_document": "NSFDC MSY Guidelines", "active": True},
    {"rule_id": "RULE-057-03", "scheme_id": "SIH26092-057", "field": "annual_income", "operator": "<=", "value": "300000.0", "value_type": "FLOAT", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Annual family income must not exceed ₹3,00,000", "source_document": "NSFDC MSY Guidelines", "active": True},
    {"rule_id": "RULE-057-04", "scheme_id": "SIH26092-057", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NSFDC MSY Guidelines", "active": True},
    {"rule_id": "RULE-057-05", "scheme_id": "SIH26092-057", "field": "age", "operator": "<=", "value": "50", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Maximum age is 50 years", "source_document": "NSFDC MSY Guidelines", "active": True},

    # SIH26092-058 (NSFDC GBS)
    {"rule_id": "RULE-058-01", "scheme_id": "SIH26092-058", "field": "social_category", "operator": "IN", "value": "SC", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to Scheduled Caste (SC)", "source_document": "NSFDC GBS Guidelines", "active": True},
    {"rule_id": "RULE-058-02", "scheme_id": "SIH26092-058", "field": "annual_income", "operator": "<=", "value": "300000.0", "value_type": "FLOAT", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Annual family income must not exceed ₹3,00,000", "source_document": "NSFDC GBS Guidelines", "active": True},
    {"rule_id": "RULE-058-03", "scheme_id": "SIH26092-058", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NSFDC GBS Guidelines", "active": True},
    {"rule_id": "RULE-058-04", "scheme_id": "SIH26092-058", "field": "age", "operator": "<=", "value": "55", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Maximum age is 55 years", "source_document": "NSFDC GBS Guidelines", "active": True},

    # SIH26092-059 (NSTFDC ASRY)
    {"rule_id": "RULE-059-01", "scheme_id": "SIH26092-059", "field": "social_category", "operator": "IN", "value": "ST", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to Scheduled Tribe (ST)", "source_document": "NSTFDC ASRY Guidelines", "active": True},
    {"rule_id": "RULE-059-02", "scheme_id": "SIH26092-059", "field": "annual_income", "operator": "<=", "value": "300000.0", "value_type": "FLOAT", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Annual family income must not exceed ₹3,00,000", "source_document": "NSTFDC ASRY Guidelines", "active": True},
    {"rule_id": "RULE-059-03", "scheme_id": "SIH26092-059", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NSTFDC ASRY Guidelines", "active": True},

    # SIH26092-060 (CEGSSC)
    {"rule_id": "RULE-060-01", "scheme_id": "SIH26092-060", "field": "social_category", "operator": "IN", "value": "SC", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Promoter/Applicant must belong to Scheduled Caste (>51% equity)", "source_document": "CEGSSC Guidelines", "active": True},
    {"rule_id": "RULE-060-02", "scheme_id": "SIH26092-060", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "CEGSSC Guidelines", "active": True},

    # SIH26092-061 (PMVDY)
    {"rule_id": "RULE-061-01", "scheme_id": "SIH26092-061", "field": "social_category", "operator": "IN", "value": "ST", "value_type": "STRING", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Targeted primarily at Scheduled Tribe forest gatherers and SHGs", "source_document": "TRIFED PMVDY Manual", "active": True},

    # SIH26092-062 (KVIC GVY)
    {"rule_id": "RULE-062-01", "scheme_id": "SIH26092-062", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "KVIC GVY Guidelines", "active": True},
    {"rule_id": "RULE-062-02", "scheme_id": "SIH26092-062", "field": "age", "operator": "<=", "value": "55", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Maximum age is 55 years", "source_document": "KVIC GVY Guidelines", "active": True},

    # SIH26092-063 (NSFDC MKY)
    {"rule_id": "RULE-063-01", "scheme_id": "SIH26092-063", "field": "social_category", "operator": "IN", "value": "SC", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to Scheduled Caste (SC)", "source_document": "NSFDC MKY Circular", "active": True},
    {"rule_id": "RULE-063-02", "scheme_id": "SIH26092-063", "field": "gender", "operator": "=", "value": "FEMALE", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must be a woman farmer / agricultural worker", "source_document": "NSFDC MKY Circular", "active": True},
    {"rule_id": "RULE-063-03", "scheme_id": "SIH26092-063", "field": "annual_income", "operator": "<=", "value": "300000.0", "value_type": "FLOAT", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Annual family income must not exceed ₹3,00,000", "source_document": "NSFDC MKY Circular", "active": True},
    {"rule_id": "RULE-063-04", "scheme_id": "SIH26092-063", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NSFDC MKY Circular", "active": True},

    # SIH26092-064 (NBCFDC Shilp Sampada)
    {"rule_id": "RULE-064-01", "scheme_id": "SIH26092-064", "field": "social_category", "operator": "IN", "value": "OBC", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to Backward Classes (OBC)", "source_document": "NBCFDC Shilp Sampada Guidelines", "active": True},
    {"rule_id": "RULE-064-02", "scheme_id": "SIH26092-064", "field": "annual_income", "operator": "<=", "value": "300000.0", "value_type": "FLOAT", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Annual family income must not exceed ₹3,00,000", "source_document": "NBCFDC Shilp Sampada Guidelines", "active": True},
    {"rule_id": "RULE-064-03", "scheme_id": "SIH26092-064", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NBCFDC Shilp Sampada Guidelines", "active": True},
    {"rule_id": "RULE-064-04", "scheme_id": "SIH26092-064", "field": "age", "operator": "<=", "value": "55", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Maximum age is 55 years", "source_document": "NBCFDC Shilp Sampada Guidelines", "active": True}
]

NEW_DOCUMENTS = [
    # SIH26092-057 (NSFDC MSY)
    {"document_id": "DOC-057-01", "scheme_id": "SIH26092-057", "document_name": "Scheduled Caste Certificate", "requirement_type": "REQUIRED", "condition": "Issued by authorized revenue authority", "source_document": "NSFDC MSY Guidelines", "source_page": "1", "source_section": "Eligibility", "active": True},
    {"document_id": "DOC-057-02", "scheme_id": "SIH26092-057", "document_name": "Income Certificate", "requirement_type": "REQUIRED", "condition": "Annual family income <= ₹3,00,000", "source_document": "NSFDC MSY Guidelines", "source_page": "1", "source_section": "Income Criteria", "active": True},
    {"document_id": "DOC-057-03", "scheme_id": "SIH26092-057", "document_name": "Aadhaar Card / Identity Proof", "requirement_type": "REQUIRED", "condition": "Valid government photo identity", "source_document": "NSFDC MSY Guidelines", "source_page": "2", "source_section": "KYC", "active": True},
    {"document_id": "DOC-057-04", "scheme_id": "SIH26092-057", "document_name": "Self-Help Group Resolution (if applying via SHG)", "requirement_type": "CONDITIONAL", "condition": "Required only for group micro-credit", "source_document": "NSFDC MSY Guidelines", "source_page": "2", "source_section": "SHG Criteria", "active": True},

    # SIH26092-058 (NSFDC GBS)
    {"document_id": "DOC-058-01", "scheme_id": "SIH26092-058", "document_name": "Scheduled Caste Certificate", "requirement_type": "REQUIRED", "condition": "Issued by competent revenue authority", "source_document": "NSFDC GBS Policy Guidelines", "source_page": "1", "source_section": "Eligibility", "active": True},
    {"document_id": "DOC-058-02", "scheme_id": "SIH26092-058", "document_name": "Income Certificate", "requirement_type": "REQUIRED", "condition": "Annual family income <= ₹3,00,000", "source_document": "NSFDC GBS Policy Guidelines", "source_page": "1", "source_section": "Income Criteria", "active": True},
    {"document_id": "DOC-058-03", "scheme_id": "SIH26092-058", "document_name": "Detailed Project Report (DPR) / Unit Quotation", "requirement_type": "REQUIRED", "condition": "Quotation for green vehicle / solar unit / polyhouse", "source_document": "NSFDC GBS Policy Guidelines", "source_page": "3", "source_section": "Technical DPR", "active": True},

    # SIH26092-059 (NSTFDC ASRY)
    {"document_id": "DOC-059-01", "scheme_id": "SIH26092-059", "document_name": "Scheduled Tribe Certificate", "requirement_type": "REQUIRED", "condition": "Issued by competent revenue authority", "source_document": "NSTFDC ASRY Guidelines", "source_page": "1", "source_section": "Eligibility", "active": True},
    {"document_id": "DOC-059-02", "scheme_id": "SIH26092-059", "document_name": "Admission Letter / Proof of Enrollment", "requirement_type": "REQUIRED", "condition": "Recognized professional / technical college admission proof", "source_document": "NSTFDC ASRY Guidelines", "source_page": "2", "source_section": "Admission Proof", "active": True},
    {"document_id": "DOC-059-03", "scheme_id": "SIH26092-059", "document_name": "Course Fee Structure Breakup", "requirement_type": "REQUIRED", "condition": "Certified fee schedule from educational institution", "source_document": "NSTFDC ASRY Guidelines", "source_page": "2", "source_section": "Financials", "active": True},

    # SIH26092-060 (CEGSSC)
    {"document_id": "DOC-060-01", "scheme_id": "SIH26092-060", "document_name": "Caste Certificate of SC Promoters (>51% shareholding)", "requirement_type": "REQUIRED", "condition": "Proof of SC ownership shareholding", "source_document": "CEGSSC Guidelines", "source_page": "2", "source_section": "Shareholding", "active": True},
    {"document_id": "DOC-060-02", "scheme_id": "SIH26092-060", "document_name": "Business Registration Certificate (Udyam / ROC)", "requirement_type": "REQUIRED", "condition": "Valid enterprise registration", "source_document": "CEGSSC Guidelines", "source_page": "3", "source_section": "Entity Proof", "active": True},
    {"document_id": "DOC-060-03", "scheme_id": "SIH26092-060", "document_name": "Bank Loan Sanction Letter from Member Lending Institution", "requirement_type": "REQUIRED", "condition": "Sanction letter for loan > ₹15 Lakh", "source_document": "CEGSSC Guidelines", "source_page": "4", "source_section": "MLI Sanction", "active": True},

    # SIH26092-063 (NSFDC MKY)
    {"document_id": "DOC-063-01", "scheme_id": "SIH26092-063", "document_name": "Scheduled Caste Certificate", "requirement_type": "REQUIRED", "condition": "Issued by authorized revenue authority", "source_document": "NSFDC MKY Circular", "source_page": "1", "source_section": "Eligibility", "active": True},
    {"document_id": "DOC-063-02", "scheme_id": "SIH26092-063", "document_name": "Land Record / Agricultural Activity Proof", "requirement_type": "CONDITIONAL", "condition": "7/12 extract or livestock ownership certificate", "source_document": "NSFDC MKY Circular", "source_page": "1", "source_section": "Agri Proof", "active": True},

    # SIH26092-064 (NBCFDC Shilp Sampada)
    {"document_id": "DOC-064-01", "scheme_id": "SIH26092-064", "document_name": "OBC Certificate / Backward Class Proof", "requirement_type": "REQUIRED", "condition": "Issued by authorized state revenue authority", "source_document": "NBCFDC Shilp Sampada Guidelines", "source_page": "1", "source_section": "Eligibility", "active": True},
    {"document_id": "DOC-064-02", "scheme_id": "SIH26092-064", "document_name": "Artisan / Weaver Identity Card (or Skill Proof)", "requirement_type": "REQUIRED", "condition": "Pehchan card / DIC certificate / Trade proof", "source_document": "NBCFDC Shilp Sampada Guidelines", "source_page": "2", "source_section": "Artisan Proof", "active": True},
    {"document_id": "DOC-064-03", "scheme_id": "SIH26092-064", "document_name": "Income Certificate", "requirement_type": "REQUIRED", "condition": "Annual family income <= ₹3,00,000", "source_document": "NBCFDC Shilp Sampada Guidelines", "source_page": "1", "source_section": "Income Criteria", "active": True}
]


def expand_database():
    db = SessionLocal()
    print("=================================================================")
    print("TASK-034: EXPANDING SCHEME DATASET (ADDITIVE & SAFE)")
    print("=================================================================")

    # 1. Verify pre-existing schemes
    existing_schemes = db.query(Scheme).order_by(Scheme.scheme_id.asc()).all()
    old_count = len(existing_schemes)
    print(f"Pre-existing Schemes Count: {old_count}")
    assert old_count in (56, 64), f"Unexpected pre-existing schemes count: {old_count}"

    existing_ids = {s.scheme_id for s in existing_schemes}

    # 2. Insert new schemes safely
    added_count = 0
    for s_dict in NEW_SCHEMES:
        s_id = s_dict["scheme_id"]
        if s_id in existing_ids:
            print(f"Skipping already existing scheme: {s_id}")
            continue

        scheme_obj = Scheme(**s_dict)
        db.add(scheme_obj)

        # Add verification record
        verif_obj = SchemeVerification(
            id=f"VERIF-{s_id}",
            scheme_id=s_id,
            verification_status="VERIFIED",
            last_verified_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            data_confidence="HIGH",
            notes="Authoritatively verified from official ministry/nodal agency guidelines.",
            normalization_note="Task-034 web audit addition."
        )
        db.add(verif_obj)
        added_count += 1
        print(f"Added new scheme: {s_id} | {s_dict['scheme_name']}")

    db.commit()

    # 3. Insert rules
    existing_rule_ids = {r[0] for r in db.query(SchemeRule.rule_id).all()}
    for r_dict in NEW_RULES:
        if r_dict["rule_id"] not in existing_rule_ids:
            rule_obj = SchemeRule(**r_dict)
            db.add(rule_obj)

    # 4. Insert documents
    existing_doc_ids = {d[0] for d in db.query(SchemeDocument.document_id).all()}
    for d_dict in NEW_DOCUMENTS:
        if d_dict["document_id"] not in existing_doc_ids:
            doc_obj = SchemeDocument(**d_dict)
            db.add(doc_obj)

    db.commit()

    # 5. Final count check
    final_count = db.query(Scheme).count()
    print(f"\nFinal Total Schemes in DB: {final_count}")
    assert final_count == 64, f"Expected 64 schemes, found {final_count}"
    print(f"Successfully added {added_count} new schemes with zero changes to pre-existing schemes.")
    db.close()


if __name__ == "__main__":
    expand_database()
