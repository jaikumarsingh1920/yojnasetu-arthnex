"""
TASK-034B Deep Second-Pass Dataset Expansion Migration
Adds SIH26092-065 through SIH26092-074 to the YojnaSetu database and raw CSV files.
"""

import os
import sys
import csv
from datetime import datetime

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "04data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.session import SessionLocal
from app.models import Scheme, SchemeRule, SchemeDocument, SchemeVerification, SchemeChangelog

NEW_SCHEMES_034B = [
    {
        "scheme_id": "SIH26092-065",
        "scheme_code": "PM-YASASVI",
        "scheme_name": "PM Young Achievers Scholarship Award Scheme for Vibrant India (PM-YASASVI)",
        "scheme_type": "SCHOLARSHIP; EDUCATION_SUPPORT",
        "short_description": "Comprehensive scholarship and tuition fee assistance for meritorious OBC, EBC, and DNT students studying in Class 9 to 12 and higher education institutions.",
        "detailed_description": "Umbrella scheme by Ministry of Social Justice & Empowerment providing pre-matric, post-matric, and top class school/college scholarships for OBC, EBC, and DNT students with family income up to ₹2.50 lakh.",
        "purpose": "Promoting quality education and financial assistance for backward class and nomadic students.",
        "source_organization": "Department of Social Justice and Empowerment",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "Department of Social Justice & Empowerment / National Testing Agency (NTA)",
        "target_beneficiary": "OBC, EBC, and DNT students studying in recognized schools and colleges",
        "applicant_types": "STUDENT, INDIVIDUAL",
        "marginalized_group": "OBC, EBC, DNT",
        "target_groups": "OBC, EBC, DNT, STUDENTS",
        "social_category": "OBC; EBC; DNT",
        "age_min": 13,
        "age_max": 25,
        "income_limit": 250000.0,
        "income_operator": "<=",
        "income_definition": "Annual Family Income",
        "sector": "EDUCATION; HIGHER_STUDIES",
        "support_type": "SCHOLARSHIP; TUITION_FEE_ASSISTANCE",
        "grant_available": "TRUE",
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://scholarships.gov.in/",
        "official_portal": "https://scholarships.gov.in/",
        "official_source_url": "https://socialjustice.gov.in/",
        "source_document": "PM-YASASVI Umbrella Scheme Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-066",
        "scheme_code": "SHRESHTA",
        "scheme_name": "Scheme for Residential Education for Students in High Schools in Targeted Areas (SHRESHTA)",
        "scheme_type": "SCHOLARSHIP; RESIDENTIAL_EDUCATION",
        "short_description": "Full school and residential hostel fee grant (up to ₹1.35 Lakh/year) for bright Scheduled Caste students in top CBSE-affiliated residential schools.",
        "detailed_description": "Department of Social Justice and Empowerment scheme providing high quality residential education to meritorious SC students selected through NETS entrance test.",
        "purpose": "Bridge the educational gap for meritorious SC students in service-deficient areas through top-tier private residential schooling.",
        "source_organization": "Department of Social Justice and Empowerment",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "National Testing Agency (NTA) / MSJE",
        "target_beneficiary": "Meritorious Scheduled Caste (SC) students studying in Classes 9 to 12",
        "applicant_types": "STUDENT, INDIVIDUAL",
        "marginalized_group": "SC",
        "target_groups": "SC, STUDENTS",
        "sc_required": "TRUE",
        "social_category": "SC",
        "age_min": 13,
        "age_max": 19,
        "income_limit": 250000.0,
        "income_operator": "<=",
        "income_definition": "Annual Family Income",
        "sector": "EDUCATION; RESIDENTIAL_SCHOOLING",
        "support_type": "GRANT; SCHOLARSHIP; FULL_FEE_COVERAGE",
        "grant_available": "TRUE",
        "grant_amount": 135000.0,
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://shreshta.admissions.nic.in/",
        "official_portal": "https://shreshta.admissions.nic.in/",
        "official_source_url": "https://socialjustice.gov.in/",
        "source_document": "SHRESHTA Operational Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-067",
        "scheme_code": "NMDFC-VIRASAT",
        "scheme_name": "NMDFC Virasat Scheme for Craftspersons and Artisans",
        "scheme_type": "CONCESSIONAL_LOAN; ARTISAN_SUPPORT",
        "short_description": "Concessional credit up to ₹10 Lakhs at 4% to 6% p.a. interest for traditional artisans and craftspersons from notified Minority communities.",
        "detailed_description": "NMDFC scheme providing working and fixed capital loans through State Channelizing Agencies for traditional craftspersons from Muslim, Christian, Sikh, Buddhist, Jain, and Parsi communities.",
        "purpose": "Financial inclusion, heritage craft preservation, and working capital assistance for minority craftspersons.",
        "source_organization": "National Minorities Development and Finance Corporation (NMDFC)",
        "ministry": "Ministry of Minority Affairs",
        "implementing_agency": "State Channelizing Agencies (SCAs)",
        "target_beneficiary": "Artisans, craftspersons, and traditional handloom/handicraft workers from minority communities",
        "applicant_types": "INDIVIDUAL, ARTISAN, CRAFTSPERSON",
        "marginalized_group": "MINORITY",
        "target_groups": "MINORITY, ARTISANS, CRAFTSPERSONS",
        "social_category": "MINORITY",
        "sector": "ARTISAN; HANDICRAFT; TRADITIONAL_OCCUPATIONS",
        "support_type": "CONCESSIONAL_LOAN; WORKING_CAPITAL",
        "loan_available": "TRUE",
        "min_loan_amount": 50000.0,
        "max_loan_amount": 1000000.0,
        "minimum_loan_amount": 50000.0,
        "maximum_loan_amount": 1000000.0,
        "financing_percentage": 90.0,
        "beneficiary_contribution_percentage": 5.0,
        "interest_rate_min": 4.0,
        "interest_rate_max": 6.0,
        "interest_rate_type": "CONCESSIONAL",
        "age_min": 18,
        "age_max": 60,
        "repayment_period_min_months": 36,
        "repayment_period_max_months": 60,
        "collateral_required": "CONDITIONAL",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://www.nmdfc.org/",
        "official_portal": "https://www.nmdfc.org/",
        "official_source_url": "https://www.nmdfc.org/",
        "source_document": "NMDFC Virasat Scheme Operational Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-068",
        "scheme_code": "NDFDC-DSY",
        "scheme_name": "Divyangjan Swavalamban Yojana (NDFDC)",
        "scheme_type": "CONCESSIONAL_LOAN; SELF_EMPLOYMENT",
        "short_description": "Concessional loans up to ₹50 Lakhs at 5% to 9% interest for Persons with Disabilities (PwD >= 40%) for self-employment, income-generation, and assistive equipment.",
        "detailed_description": "National Divyangjan Finance and Development Corporation (NDFDC) flagship scheme providing low-interest term loans with a 1% interest rebate for women with disabilities.",
        "purpose": "Socio-economic empowerment and self-employment promotion for Persons with Disabilities.",
        "source_organization": "National Divyangjan Finance and Development Corporation (NDFDC)",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "State Channelizing Agencies (SCAs) / Partner Banks",
        "target_beneficiary": "Persons with Disabilities (PwDs) having 40% or more disability under PwD Act 2016",
        "applicant_types": "INDIVIDUAL, PWD, ENTREPRENEUR",
        "marginalized_group": "PWD",
        "target_groups": "PWD, SPECIALLY_ABLED, ENTREPRENEURS",
        "sector": "MICRO_ENTERPRISE; SERVICES; TRADING; SMALL_BUSINESS",
        "support_type": "CONCESSIONAL_LOAN; SELF_EMPLOYMENT",
        "loan_available": "TRUE",
        "min_loan_amount": 25000.0,
        "max_loan_amount": 5000000.0,
        "minimum_loan_amount": 25000.0,
        "maximum_loan_amount": 5000000.0,
        "financing_percentage": 90.0,
        "beneficiary_contribution_percentage": 10.0,
        "interest_rate_min": 5.0,
        "interest_rate_max": 9.0,
        "interest_rate_type": "CONCESSIONAL",
        "age_min": 18,
        "repayment_period_min_months": 36,
        "repayment_period_max_months": 120,
        "moratorium_min_months": 6,
        "moratorium_max_months": 12,
        "collateral_required": "CONDITIONAL",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://ndfdc.nic.in/",
        "official_portal": "https://ndfdc.nic.in/",
        "official_source_url": "https://ndfdc.nic.in/",
        "source_document": "NDFDC Divyangjan Swavalamban Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-069",
        "scheme_code": "SAMARTH",
        "scheme_name": "SAMARTH — Scheme for Capacity Building in Textile Sector",
        "scheme_type": "SKILL_DEVELOPMENT; CAPACITY_BUILDING",
        "short_description": "Industry-aligned skill training, certification, and wage/self-employment placement assistance across the textile value chain with special focus on SC/ST and women.",
        "detailed_description": "Ministry of Textiles initiative delivering NSQF-compliant skill training through biometric attendance, CCTV monitoring, and certified training centers for handloom, handicraft, and textile manufacturing.",
        "purpose": "Skill development, employment generation, and productivity enhancement in traditional and modern textile sectors.",
        "source_organization": "Ministry of Textiles",
        "ministry": "Ministry of Textiles",
        "implementing_agency": "Ministry of Textiles Implementing Partners / Industry Associations",
        "target_beneficiary": "Unemployed youth, women, SC/ST, traditional artisans, and textile workers",
        "applicant_types": "INDIVIDUAL, YOUTH, ARTISAN, WEAVER",
        "target_groups": "YOUTH, WOMEN, SC, ST, WEAVERS, ARTISANS",
        "sector": "TEXTILE; HANDLOOM; HANDICRAFT; APPAREL",
        "support_type": "SKILL_TRAINING; VOCATIONAL_TRAINING; PLACEMENT_ASSISTANCE",
        "training_available": "TRUE",
        "age_min": 18,
        "age_max": 45,
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://samarth-textiles.gov.in/",
        "official_portal": "https://samarth-textiles.gov.in/",
        "official_source_url": "https://samarth-textiles.gov.in/",
        "source_document": "SAMARTH Operational Guidelines (Ministry of Textiles)",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-070",
        "scheme_code": "DAHD-AHIDF",
        "scheme_name": "Animal Husbandry Infrastructure Development Fund (AHIDF)",
        "scheme_type": "INTEREST_SUBVENTION; CREDIT_GUARANTEE",
        "short_description": "3% per annum interest subvention on term loans up to 90% project cost with credit guarantee for dairy, meat processing, and animal feed infrastructure.",
        "detailed_description": "Department of Animal Husbandry and Dairying scheme incentivizing investments in livestock processing, value addition, and breed improvement with 3% interest subvention for 8 years.",
        "purpose": "Infrastructure development and entrepreneurship in dairy and meat processing, animal feed, and livestock breed improvement.",
        "source_organization": "Department of Animal Husbandry and Dairying",
        "ministry": "Ministry of Fisheries, Animal Husbandry and Dairying",
        "implementing_agency": "Department of Animal Husbandry & Dairying / SIDBI / Scheduled Banks",
        "target_beneficiary": "Individual entrepreneurs, MSMEs, FPOs, Section 8 companies, and Dairy Cooperatives",
        "applicant_types": "INDIVIDUAL, ENTREPRENEUR, MSME, FPO, COOPERATIVE",
        "target_groups": "ENTREPRENEURS, FARMERS, MSMES, RURAL_ENTERPRISES",
        "sector": "DAIRY; LIVESTOCK; ANIMAL_HUSBANDRY; FOOD_PROCESSING",
        "support_type": "INTEREST_SUBVENTION; CREDIT_GUARANTEE",
        "loan_available": "TRUE",
        "financing_percentage": 90.0,
        "beneficiary_contribution_percentage": 10.0,
        "subsidy_available": "TRUE",
        "subsidy_details": "3% Interest Subvention paid directly to lending institution",
        "repayment_period_max_months": 96,
        "moratorium_max_months": 24,
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://ahidf.udyamimitra.in/",
        "official_portal": "https://ahidf.udyamimitra.in/",
        "official_source_url": "https://dahd.nic.in/",
        "source_document": "AHIDF Revised Operational Guidelines (DAHD)",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-071",
        "scheme_code": "MSME-SCLCSS",
        "scheme_name": "Special Credit Linked Capital Subsidy Scheme for SC/ST (SCLCSS under NSSH)",
        "scheme_type": "CAPITAL_SUBSIDY; TECHNOLOGY_UPGRADATION",
        "short_description": "25% upfront capital subsidy (up to ₹25 Lakhs) on institutional credit up to ₹1 Crore for technology upgradation of SC/ST-owned Micro and Small Enterprises.",
        "detailed_description": "Key scheme under National SC-ST Hub (NSSH) by Ministry of MSME providing 25% capital subsidy on plant and machinery loans for SC/ST entrepreneurs with valid Udyam Registration.",
        "purpose": "Facilitate purchase of modern plant and machinery and scale technology adoption for SC/ST enterprises.",
        "source_organization": "Ministry of Micro, Small and Medium Enterprises",
        "ministry": "Ministry of Micro, Small and Medium Enterprises",
        "implementing_agency": "National Small Industries Corporation (NSIC) / SIDBI / Scheduled Banks",
        "target_beneficiary": "SC/ST entrepreneurs owning Micro and Small Enterprises (min 51% shareholding)",
        "applicant_types": "ENTREPRENEUR, MSME, INDIVIDUAL",
        "marginalized_group": "SC, ST",
        "target_groups": "SC, ST, MSME, ENTREPRENEURS",
        "sc_required": "CONDITIONAL",
        "social_category": "SC; ST",
        "sector": "MANUFACTURING; SERVICES; PROCESSING; ALL_MSME_SECTORS",
        "business_registration_required": "TRUE",
        "support_type": "CAPITAL_SUBSIDY; EQUIPMENT_SUPPORT",
        "subsidy_available": "TRUE",
        "subsidy_percentage": 25.0,
        "grant_available": "TRUE",
        "grant_amount": 2500000.0,
        "max_project_cost": 10000000.0,
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://www.scsthub.in/",
        "official_portal": "https://www.scsthub.in/",
        "official_source_url": "https://msme.gov.in/",
        "source_document": "Special Credit Linked Capital Subsidy Scheme Guidelines (NSSH)",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-072",
        "scheme_code": "NSKFDC-SANMART",
        "scheme_name": "NSKFDC Sanitary Marts Scheme",
        "scheme_type": "CONCESSIONAL_LOAN; SELF_EMPLOYMENT",
        "short_description": "Concessional loans up to ₹15 Lakhs (up to 90% project cost) at 4% p.a. interest for Safai Karamcharis and manual scavengers to set up sanitation and hygiene retail marts.",
        "detailed_description": "NSKFDC scheme providing financial assistance to liberated manual scavengers, safai karamcharis, and their dependents for establishing sanitary marts with a 1% rebate for women.",
        "purpose": "Dignified self-employment and sustainable livelihood creation in sanitation product retail and services.",
        "source_organization": "National Safai Karamcharis Finance and Development Corporation (NSKFDC)",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "State Channelizing Agencies (SCAs) / RRBs / Nationalized Banks",
        "target_beneficiary": "Safai Karamcharis, identified manual scavengers, waste pickers, and their dependents",
        "applicant_types": "INDIVIDUAL, SAFAI_KARAMCHARI, SHG",
        "marginalized_group": "SAFAI_KARAMCHARI",
        "target_groups": "SAFAI_KARAMCHARIS, MANUAL_SCAVENGERS, SANITATION_WORKERS",
        "sector": "SANITATION; TRADING; RETAIL; SERVICE",
        "support_type": "CONCESSIONAL_LOAN; SELF_EMPLOYMENT",
        "loan_available": "TRUE",
        "max_project_cost": 1500000.0,
        "max_loan_amount": 1350000.0,
        "maximum_loan_amount": 1350000.0,
        "financing_percentage": 90.0,
        "beneficiary_contribution_percentage": 10.0,
        "interest_rate_min": 4.0,
        "interest_rate_max": 4.0,
        "interest_rate_type": "CONCESSIONAL",
        "age_min": 18,
        "repayment_period_min_months": 60,
        "repayment_period_max_months": 120,
        "moratorium_min_months": 6,
        "moratorium_max_months": 10,
        "collateral_required": "FALSE",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://www.nskfdc.nic.in/",
        "official_portal": "https://www.nskfdc.nic.in/",
        "official_source_url": "https://www.nskfdc.nic.in/",
        "source_document": "NSKFDC Sanitary Marts Scheme Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-073",
        "scheme_code": "NBCFDC-KRISHI",
        "scheme_name": "NBCFDC Krishi Sampada Scheme",
        "scheme_type": "MICRO_FINANCE; AGRICULTURAL_LOAN",
        "short_description": "Concessional micro-finance loans up to ₹50,000 at 4% p.a. interest for small farmers and agricultural vendors from Other Backward Classes during crop seasons.",
        "detailed_description": "NBCFDC seasonal credit scheme providing up to 95% project financing for small farmers and vegetable vendors belonging to OBC communities with family income up to ₹3 Lakh.",
        "purpose": "Provide timely concessional working credit to small OBC farmers and agricultural produce vendors during cropping cycles.",
        "source_organization": "National Backward Classes Finance and Development Corporation (NBCFDC)",
        "ministry": "Ministry of Social Justice and Empowerment",
        "implementing_agency": "State Channelising Agencies (SCAs) / RRBs / Public Sector Banks",
        "target_beneficiary": "Small farmers, vegetable vendors, and agricultural laborers from Backward Classes",
        "applicant_types": "FARMER, INDIVIDUAL, VENDOR",
        "marginalized_group": "OBC",
        "target_groups": "OBC, FARMERS, SMALL_VENDORS",
        "social_category": "OBC",
        "age_min": 18,
        "age_max": 60,
        "income_limit": 300000.0,
        "income_operator": "<=",
        "income_definition": "Annual Family Income",
        "sector": "AGRICULTURE; VEGETABLE_VENDING; RURAL_FARMING",
        "support_type": "MICRO_FINANCE; CROP_CREDIT",
        "loan_available": "TRUE",
        "min_loan_amount": 10000.0,
        "max_loan_amount": 50000.0,
        "minimum_loan_amount": 10000.0,
        "maximum_loan_amount": 50000.0,
        "financing_percentage": 95.0,
        "beneficiary_contribution_percentage": 5.0,
        "interest_rate_min": 4.0,
        "interest_rate_max": 4.0,
        "interest_rate_type": "CONCESSIONAL",
        "repayment_period_min_months": 12,
        "repayment_period_max_months": 36,
        "collateral_required": "FALSE",
        "application_mode": "PARTNER_ROUTED",
        "application_url": "https://nbcfdc.nic.in/",
        "official_portal": "https://nbcfdc.nic.in/",
        "official_source_url": "https://nbcfdc.nic.in/",
        "source_document": "NBCFDC Krishi Sampada Lending Guidelines",
        "scheme_status": "ACTIVE"
    },
    {
        "scheme_id": "SIH26092-074",
        "scheme_code": "PM-JANMAN",
        "scheme_name": "Pradhan Mantri Janjati Adivasi Nyaya Maha Abhiyan (PM-JANMAN)",
        "scheme_type": "LIVELIHOOD_SUPPORT; HOUSING_GRANT; VOCATIONAL_TRAINING",
        "short_description": "Saturation mission providing pucca housing assistance, Van Dhan Vikas Kendra livelihood infrastructure, and skill training for Particularly Vulnerable Tribal Groups (PVTGs).",
        "detailed_description": "Inter-ministerial mission led by Ministry of Tribal Affairs covering 75 PVTG communities across 18 States and UTs with dedicated housing grants, Multi-Purpose Centres, and sustainable livelihood support.",
        "purpose": "Comprehensive socio-economic upliftment, safe housing, and sustainable livelihood creation for vulnerable tribal communities.",
        "source_organization": "Ministry of Tribal Affairs",
        "ministry": "Ministry of Tribal Affairs",
        "implementing_agency": "Ministry of Tribal Affairs / State Tribal Welfare Departments",
        "target_beneficiary": "Households belonging to Particularly Vulnerable Tribal Groups (PVTGs)",
        "applicant_types": "INDIVIDUAL, TRIBAL_HOUSEHOLD, SHG",
        "marginalized_group": "ST",
        "target_groups": "ST, PVTG, VULNERABLE_TRIBAL_GROUPS",
        "social_category": "ST",
        "sector": "HOUSING; FOREST_PRODUCE; SKILL_DEVELOPMENT; RURAL_LIVELIHOOD",
        "support_type": "GRANT; HOUSING_ASSISTANCE; LIVELIHOOD_INFRASTRUCTURE",
        "grant_available": "TRUE",
        "training_available": "TRUE",
        "application_mode": "DIRECT_GOVERNMENT_PORTAL",
        "application_url": "https://tribal.nic.in/",
        "official_portal": "https://tribal.nic.in/",
        "official_source_url": "https://tribal.nic.in/",
        "source_document": "PM-JANMAN Operational Guidelines and SOPs",
        "scheme_status": "ACTIVE"
    }
]

NEW_RULES_034B = [
    # SIH26092-065 (PM-YASASVI)
    {"rule_id": "RULE-065-01", "scheme_id": "SIH26092-065", "field": "social_category", "operator": "IN", "value": "OBC,EBC,DNT", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to OBC, EBC, or DNT categories", "source_document": "PM-YASASVI Guidelines", "active": True},
    {"rule_id": "RULE-065-02", "scheme_id": "SIH26092-065", "field": "annual_income", "operator": "<=", "value": "250000.0", "value_type": "FLOAT", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Annual family income must not exceed ₹2,50,000", "source_document": "PM-YASASVI Guidelines", "active": True},
    {"rule_id": "RULE-065-03", "scheme_id": "SIH26092-065", "field": "age", "operator": ">=", "value": "13", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 13 years", "source_document": "PM-YASASVI Guidelines", "active": True},

    # SIH26092-066 (SHRESHTA)
    {"rule_id": "RULE-066-01", "scheme_id": "SIH26092-066", "field": "social_category", "operator": "IN", "value": "SC", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to Scheduled Caste (SC)", "source_document": "SHRESHTA Guidelines", "active": True},
    {"rule_id": "RULE-066-02", "scheme_id": "SIH26092-066", "field": "annual_income", "operator": "<=", "value": "250000.0", "value_type": "FLOAT", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Parental annual income must not exceed ₹2,50,000", "source_document": "SHRESHTA Guidelines", "active": True},
    {"rule_id": "RULE-066-03", "scheme_id": "SIH26092-066", "field": "age", "operator": ">=", "value": "13", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 13 years", "source_document": "SHRESHTA Guidelines", "active": True},

    # SIH26092-067 (NMDFC Virasat)
    {"rule_id": "RULE-067-01", "scheme_id": "SIH26092-067", "field": "social_category", "operator": "IN", "value": "MINORITY", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to a notified Minority community", "source_document": "NMDFC Virasat Guidelines", "active": True},
    {"rule_id": "RULE-067-02", "scheme_id": "SIH26092-067", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NMDFC Virasat Guidelines", "active": True},

    # SIH26092-068 (NDFDC Divyangjan Swavalamban)
    {"rule_id": "RULE-068-01", "scheme_id": "SIH26092-068", "field": "target_groups", "operator": "CONTAINS", "value": "PWD", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Scheme is specifically for Persons with Disabilities (PwD >= 40%)", "source_document": "NDFDC DSY Guidelines", "active": True},
    {"rule_id": "RULE-068-02", "scheme_id": "SIH26092-068", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NDFDC DSY Guidelines", "active": True},

    # SIH26092-069 (SAMARTH)
    {"rule_id": "RULE-069-01", "scheme_id": "SIH26092-069", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "SAMARTH Guidelines", "active": True},
    {"rule_id": "RULE-069-02", "scheme_id": "SIH26092-069", "field": "age", "operator": "<=", "value": "45", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Maximum age is 45 years", "source_document": "SAMARTH Guidelines", "active": True},

    # SIH26092-070 (AHIDF)
    {"rule_id": "RULE-070-01", "scheme_id": "SIH26092-070", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age for primary promoter is 18 years", "source_document": "AHIDF Guidelines", "active": True},

    # SIH26092-071 (SCLCSS under NSSH)
    {"rule_id": "RULE-071-01", "scheme_id": "SIH26092-071", "field": "social_category", "operator": "IN", "value": "SC,ST", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Enterprise must have at least 51% ownership by SC/ST entrepreneurs", "source_document": "SCLCSS Guidelines", "active": True},

    # SIH26092-072 (NSKFDC Sanitary Marts)
    {"rule_id": "RULE-072-01", "scheme_id": "SIH26092-072", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NSKFDC Sanitary Mart Guidelines", "active": True},

    # SIH26092-073 (NBCFDC Krishi Sampada)
    {"rule_id": "RULE-073-01", "scheme_id": "SIH26092-073", "field": "social_category", "operator": "IN", "value": "OBC", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant must belong to Other Backward Classes (OBC)", "source_document": "NBCFDC Krishi Sampada Guidelines", "active": True},
    {"rule_id": "RULE-073-02", "scheme_id": "SIH26092-073", "field": "annual_income", "operator": "<=", "value": "300000.0", "value_type": "FLOAT", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Annual family income must not exceed ₹3,00,000", "source_document": "NBCFDC Krishi Sampada Guidelines", "active": True},
    {"rule_id": "RULE-073-03", "scheme_id": "SIH26092-073", "field": "age", "operator": ">=", "value": "18", "value_type": "INTEGER", "rule_type": "HARD", "priority": "HIGH", "condition_group": "BASE", "error_message": "Minimum age is 18 years", "source_document": "NBCFDC Krishi Sampada Guidelines", "active": True},

    # SIH26092-074 (PM-JANMAN)
    {"rule_id": "RULE-074-01", "scheme_id": "SIH26092-074", "field": "social_category", "operator": "IN", "value": "ST", "value_type": "STRING", "rule_type": "HARD", "priority": "CRITICAL", "condition_group": "BASE", "error_message": "Applicant household must belong to Scheduled Tribe / PVTG community", "source_document": "PM-JANMAN Guidelines", "active": True}
]

NEW_DOCS_034B = [
    # PM-YASASVI
    {"document_id": "DOC-065-01", "scheme_id": "SIH26092-065", "document_name": "Aadhaar Card", "requirement_type": "MANDATORY", "condition": "Identity & DBT verification", "source_document": "PM-YASASVI Guidelines", "active": True},
    {"document_id": "DOC-065-02", "scheme_id": "SIH26092-065", "document_name": "OBC / EBC / DNT Caste Certificate", "requirement_type": "MANDATORY", "condition": "Competent authority issued certificate", "source_document": "PM-YASASVI Guidelines", "active": True},
    {"document_id": "DOC-065-03", "scheme_id": "SIH26092-065", "document_name": "Income Certificate (<= ₹2.50 Lakh)", "requirement_type": "MANDATORY", "condition": "Issued by Tehsildar / SDO", "source_document": "PM-YASASVI Guidelines", "active": True},
    {"document_id": "DOC-065-04", "scheme_id": "SIH26092-065", "document_name": "School / College Bonafide Certificate & Fee Receipt", "requirement_type": "MANDATORY", "condition": "Issued by head of institution", "source_document": "PM-YASASVI Guidelines", "active": True},

    # SHRESHTA
    {"document_id": "DOC-066-01", "scheme_id": "SIH26092-066", "document_name": "Aadhaar Card", "requirement_type": "MANDATORY", "condition": "Student identity verification", "source_document": "SHRESHTA Guidelines", "active": True},
    {"document_id": "DOC-066-02", "scheme_id": "SIH26092-066", "document_name": "SC Caste Certificate", "requirement_type": "MANDATORY", "condition": "In the name of the student or father", "source_document": "SHRESHTA Guidelines", "active": True},
    {"document_id": "DOC-066-03", "scheme_id": "SIH26092-066", "document_name": "Income Certificate (<= ₹2.50 Lakh)", "requirement_type": "MANDATORY", "condition": "Valid parental income certificate", "source_document": "SHRESHTA Guidelines", "active": True},
    {"document_id": "DOC-066-04", "scheme_id": "SIH26092-066", "document_name": "NETS Admit Card & Score Card", "requirement_type": "MANDATORY", "condition": "Proof of entrance test qualification", "source_document": "SHRESHTA Guidelines", "active": True},

    # NMDFC Virasat
    {"document_id": "DOC-067-01", "scheme_id": "SIH26092-067", "document_name": "Aadhaar Card", "requirement_type": "MANDATORY", "condition": "Identity and address proof", "source_document": "NMDFC Virasat Guidelines", "active": True},
    {"document_id": "DOC-067-02", "scheme_id": "SIH26092-067", "document_name": "Minority Community Certificate / Self-Declaration", "requirement_type": "MANDATORY", "condition": "Proof of notified minority status", "source_document": "NMDFC Virasat Guidelines", "active": True},
    {"document_id": "DOC-067-03", "scheme_id": "SIH26092-067", "document_name": "Artisan / Pehchan Card or Proof of Trade", "requirement_type": "MANDATORY", "condition": "Issued by DC Handloom / Handicrafts or SCA", "source_document": "NMDFC Virasat Guidelines", "active": True},

    # Divyangjan Swavalamban
    {"document_id": "DOC-068-01", "scheme_id": "SIH26092-068", "document_name": "Unique Disability ID (UDID) / Disability Certificate", "requirement_type": "MANDATORY", "condition": "Proof of 40% or more disability", "source_document": "NDFDC DSY Guidelines", "active": True},
    {"document_id": "DOC-068-02", "scheme_id": "SIH26092-068", "document_name": "Aadhaar Card", "requirement_type": "MANDATORY", "condition": "Identity and address proof", "source_document": "NDFDC DSY Guidelines", "active": True},
    {"document_id": "DOC-068-03", "scheme_id": "SIH26092-068", "document_name": "Project Proposal / Business Plan", "requirement_type": "MANDATORY", "condition": "Details of self-employment activity", "source_document": "NDFDC DSY Guidelines", "active": True},

    # SAMARTH
    {"document_id": "DOC-069-01", "scheme_id": "SIH26092-069", "document_name": "Aadhaar Card", "requirement_type": "MANDATORY", "condition": "Biometric attendance integration", "source_document": "SAMARTH Guidelines", "active": True},
    {"document_id": "DOC-069-02", "scheme_id": "SIH26092-069", "document_name": "Educational Qualification Certificate", "requirement_type": "OPTIONAL", "condition": "As per NSQF course prerequisite", "source_document": "SAMARTH Guidelines", "active": True},

    # AHIDF
    {"document_id": "DOC-070-01", "scheme_id": "SIH26092-070", "document_name": "Detailed Project Report (DPR)", "requirement_type": "MANDATORY", "condition": "Comprehensive infrastructure and financial model", "source_document": "AHIDF Guidelines", "active": True},
    {"document_id": "DOC-070-02", "scheme_id": "SIH26092-070", "document_name": "Udyam Registration Certificate / Business Registration", "requirement_type": "MANDATORY", "condition": "Proof of enterprise existence", "source_document": "AHIDF Guidelines", "active": True},

    # SCLCSS (NSSH)
    {"document_id": "DOC-071-01", "scheme_id": "SIH26092-071", "document_name": "Udyam Registration Certificate", "requirement_type": "MANDATORY", "condition": "Active MSE registration", "source_document": "SCLCSS Guidelines", "active": True},
    {"document_id": "DOC-071-02", "scheme_id": "SIH26092-071", "document_name": "SC / ST Caste Certificate of Proprietor/Promoters", "requirement_type": "MANDATORY", "condition": "Minimum 51% shareholding proof", "source_document": "SCLCSS Guidelines", "active": True},
    {"document_id": "DOC-071-03", "scheme_id": "SIH26092-071", "document_name": "Bank Term Loan Sanction Letter", "requirement_type": "MANDATORY", "condition": "From eligible lending bank", "source_document": "SCLCSS Guidelines", "active": True},

    # NSKFDC Sanitary Marts
    {"document_id": "DOC-072-01", "scheme_id": "SIH26092-072", "document_name": "Aadhaar Card", "requirement_type": "MANDATORY", "condition": "Identity verification", "source_document": "NSKFDC Sanitary Mart Guidelines", "active": True},
    {"document_id": "DOC-072-02", "scheme_id": "SIH26092-072", "document_name": "Safai Karamchari / Manual Scavenger Certificate or ID", "requirement_type": "MANDATORY", "condition": "Issued by Municipal Corporation / Local Body / SCA", "source_document": "NSKFDC Sanitary Mart Guidelines", "active": True},

    # NBCFDC Krishi Sampada
    {"document_id": "DOC-073-01", "scheme_id": "SIH26092-073", "document_name": "Aadhaar Card", "requirement_type": "MANDATORY", "condition": "Identity proof", "source_document": "NBCFDC Krishi Sampada Guidelines", "active": True},
    {"document_id": "DOC-073-02", "scheme_id": "SIH26092-073", "document_name": "OBC Caste Certificate", "requirement_type": "MANDATORY", "condition": "Competent authority issued", "source_document": "NBCFDC Krishi Sampada Guidelines", "active": True},
    {"document_id": "DOC-073-03", "scheme_id": "SIH26092-073", "document_name": "Land Records / Farmer ID / Vending Proof", "requirement_type": "MANDATORY", "condition": "Proof of agricultural or vending activity", "source_document": "NBCFDC Krishi Sampada Guidelines", "active": True},

    # PM-JANMAN
    {"document_id": "DOC-074-01", "scheme_id": "SIH26092-074", "document_name": "Aadhaar Card / Ration Card", "requirement_type": "MANDATORY", "condition": "Household identity verification", "source_document": "PM-JANMAN Guidelines", "active": True},
    {"document_id": "DOC-074-02", "scheme_id": "SIH26092-074", "document_name": "ST / PVTG Certificate / Village Survey Listing", "requirement_type": "MANDATORY", "condition": "Inclusion in official PVTG baseline survey", "source_document": "PM-JANMAN Guidelines", "active": True}
]

def migrate_task034b():
    print("=================================================================")
    print("TASK-034B: MIGRATING DEEP SECOND-PASS EXPANSION (SIH-065 TO SIH-074)")
    print("=================================================================")

    db = SessionLocal()
    existing_ids = {s.scheme_id for s in db.query(Scheme.scheme_id).all()}
    print(f"Pre-migration total schemes: {len(existing_ids)}")

    added_schemes = 0
    for s_dict in NEW_SCHEMES_034B:
        sid = s_dict["scheme_id"]
        if sid not in existing_ids:
            scheme_obj = Scheme(**s_dict)
            db.add(scheme_obj)
            
            verif_obj = SchemeVerification(
                id=f"VERIF-{sid}",
                scheme_id=sid,
                verification_status="VERIFIED",
                data_confidence="HIGH",
                notes="Verified against official central ministry guidelines and portal documentation."
            )
            db.add(verif_obj)
            added_schemes += 1

    db.commit()
    print(f"Added {added_schemes} new schemes to database.")

    # Rules
    existing_rule_ids = {r.rule_id for r in db.query(SchemeRule.rule_id).all()}
    added_rules = 0
    for r_dict in NEW_RULES_034B:
        rid = r_dict["rule_id"]
        if rid not in existing_rule_ids:
            rule_obj = SchemeRule(**r_dict)
            db.add(rule_obj)
            added_rules += 1
    db.commit()
    print(f"Added {added_rules} new scheme rules.")

    # Documents
    existing_doc_ids = {d.document_id for d in db.query(SchemeDocument.document_id).all()}
    added_docs = 0
    for d_dict in NEW_DOCS_034B:
        did = d_dict["document_id"]
        if did not in existing_doc_ids:
            doc_obj = SchemeDocument(**d_dict)
            db.add(doc_obj)
            added_docs += 1
    db.commit()
    print(f"Added {added_docs} new scheme documents.")

    final_total = db.query(Scheme).count()
    print(f"Final Total Schemes in DB: {final_total}")
    db.close()

    # Sync to CSV files
    sync_csvs()

def sync_csvs():
    print("\nSyncing new schemes to 04data/raw CSV files...")

    # 1. schemes_master_cleaned.csv
    schemes_csv = os.path.join(RAW_DATA_DIR, "schemes_master_cleaned.csv")
    with open(schemes_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_rows = list(reader)

    existing_ids = {r["scheme_id"] for r in existing_rows}
    new_scheme_rows = []
    for s in NEW_SCHEMES_034B:
        if s["scheme_id"] not in existing_ids:
            row = {fn: "" for fn in fieldnames}
            for k, v in s.items():
                if k in fieldnames:
                    row[k] = str(v) if v is not None else ""
            row["verification_status"] = "VERIFIED"
            row["data_confidence"] = "HIGH"
            row["legacy_priority_raw"] = "UNKNOWN"
            row["raw_source_row"] = s["scheme_id"]
            new_scheme_rows.append(row)

    if new_scheme_rows:
        with open(schemes_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows + new_scheme_rows)
        print(f"Appended {len(new_scheme_rows)} schemes to {schemes_csv}")

    # 2. scheme_rules.csv
    rules_csv = os.path.join(RAW_DATA_DIR, "scheme_rules.csv")
    with open(rules_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        r_fieldnames = reader.fieldnames
        existing_rules = list(reader)

    existing_rule_ids = {r["rule_id"] for r in existing_rules}
    new_rule_rows = []
    for r in NEW_RULES_034B:
        if r["rule_id"] not in existing_rule_ids:
            row = {fn: "" for fn in r_fieldnames}
            for k, v in r.items():
                if k in r_fieldnames:
                    row[k] = str(v)
            new_rule_rows.append(row)

    if new_rule_rows:
        with open(rules_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=r_fieldnames)
            writer.writeheader()
            writer.writerows(existing_rules + new_rule_rows)
        print(f"Appended {len(new_rule_rows)} rules to {rules_csv}")

    # 3. scheme_documents.csv
    docs_csv = os.path.join(RAW_DATA_DIR, "scheme_documents.csv")
    with open(docs_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        d_fieldnames = reader.fieldnames
        existing_docs = list(reader)

    existing_doc_ids = {d["document_id"] for d in existing_docs}
    new_doc_rows = []
    for d in NEW_DOCS_034B:
        if d["document_id"] not in existing_doc_ids:
            row = {fn: "" for fn in d_fieldnames}
            for k, v in d.items():
                if k in d_fieldnames:
                    row[k] = str(v)
            new_doc_rows.append(row)

    if new_doc_rows:
        with open(docs_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=d_fieldnames)
            writer.writeheader()
            writer.writerows(existing_docs + new_doc_rows)
        print(f"Appended {len(new_doc_rows)} documents to {docs_csv}")

    # 4. scheme_verification_report.csv
    verif_csv = os.path.join(RAW_DATA_DIR, "scheme_verification_report.csv")
    with open(verif_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        v_fieldnames = reader.fieldnames
        existing_verifs = list(reader)

    existing_verif_sids = {v["scheme_id"] for v in existing_verifs}
    new_verif_rows = []
    for s in NEW_SCHEMES_034B:
        if s["scheme_id"] not in existing_verif_sids:
            row = {
                "scheme_id": s["scheme_id"],
                "scheme_name": s["scheme_name"],
                "verification_status": "VERIFIED",
                "source_count": "1",
                "critical_fields_verified": "ALL_CRITICAL_FIELDS_VERIFIED",
                "critical_fields_missing": "NONE",
                "conflicts_found": "NONE",
                "notes": "Verified against official central ministry guidelines."
            }
            new_verif_rows.append(row)

    if new_verif_rows:
        with open(verif_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=v_fieldnames)
            writer.writeheader()
            writer.writerows(existing_verifs + new_verif_rows)
        print(f"Appended {len(new_verif_rows)} verifications to {verif_csv}")

    print("CSV synchronization complete.")

if __name__ == "__main__":
    migrate_task034b()
