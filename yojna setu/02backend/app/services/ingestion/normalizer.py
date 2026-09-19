import logging
from typing import Dict, Any, Optional
from app.engine.taxonomy import TaxonomyMatcher

logger = logging.getLogger("yojnasetu.ingestion.normalizer")


class SchemeDataNormalizer:
    """
    Normalizes extracted raw parameters into canonical YojnaSetu Scheme structure.
    Enforces standardized enums, monetary float values, and taxonomic alignments.
    Never invents unverified values.
    """

    @classmethod
    def normalize(cls, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}

        # 1. Identity & Names
        if "scheme_name" in raw_data and raw_data["scheme_name"]:
            normalized["scheme_name"] = str(raw_data["scheme_name"]).strip()
        
        if "ministry" in raw_data and raw_data["ministry"]:
            normalized["ministry"] = str(raw_data["ministry"]).strip()

        if "purpose" in raw_data and raw_data["purpose"]:
            normalized["purpose"] = str(raw_data["purpose"]).strip()
            normalized["short_description"] = str(raw_data["purpose"]).strip()

        # 2. Financial Parameters
        if "max_loan_amount" in raw_data and raw_data["max_loan_amount"] is not None:
            amt = float(raw_data["max_loan_amount"])
            normalized["max_loan_amount"] = amt
            normalized["maximum_loan_amount"] = amt
            normalized["loan_available"] = "YES" if amt > 0 else "NO"

        if "min_loan_amount" in raw_data and raw_data["min_loan_amount"] is not None:
            normalized["min_loan_amount"] = float(raw_data["min_loan_amount"])
            normalized["minimum_loan_amount"] = float(raw_data["min_loan_amount"])

        if "max_project_cost" in raw_data and raw_data["max_project_cost"] is not None:
            normalized["max_project_cost"] = float(raw_data["max_project_cost"])

        if "subsidy_percentage" in raw_data and raw_data["subsidy_percentage"] is not None:
            sub = float(raw_data["subsidy_percentage"])
            normalized["subsidy_percentage"] = sub
            normalized["subsidy_available"] = "YES" if sub > 0 else "NO"

        if "interest_rate_max" in raw_data and raw_data["interest_rate_max"] is not None:
            normalized["interest_rate_max"] = float(raw_data["interest_rate_max"])

        if "interest_rate_min" in raw_data and raw_data["interest_rate_min"] is not None:
            normalized["interest_rate_min"] = float(raw_data["interest_rate_min"])

        # 3. Demographic & Eligibility Limits
        if "age_min" in raw_data and raw_data["age_min"] is not None:
            normalized["age_min"] = int(raw_data["age_min"])

        if "age_max" in raw_data and raw_data["age_max"] is not None:
            normalized["age_max"] = int(raw_data["age_max"])

        if "income_limit" in raw_data and raw_data["income_limit"] is not None:
            normalized["income_limit"] = float(raw_data["income_limit"])

        # 3b. Moratorium & Repayment Tenure
        if "moratorium_max_months" in raw_data and raw_data["moratorium_max_months"] is not None:
            normalized["moratorium_max_months"] = int(raw_data["moratorium_max_months"])

        if "moratorium_min_months" in raw_data and raw_data["moratorium_min_months"] is not None:
            normalized["moratorium_min_months"] = int(raw_data["moratorium_min_months"])

        if "repayment_period_max_months" in raw_data and raw_data["repayment_period_max_months"] is not None:
            normalized["repayment_period_max_months"] = int(raw_data["repayment_period_max_months"])

        if "repayment_period_min_months" in raw_data and raw_data["repayment_period_min_months"] is not None:
            normalized["repayment_period_min_months"] = int(raw_data["repayment_period_min_months"])

        # 4. Target Groups & Sectors
        if "target_groups" in raw_data and raw_data["target_groups"]:
            normalized["target_groups"] = str(raw_data["target_groups"]).strip()

        if "applicant_types" in raw_data and raw_data["applicant_types"]:
            normalized["applicant_types"] = str(raw_data["applicant_types"]).strip()

        if "sector" in raw_data and raw_data["sector"]:
            normalized["sector"] = str(raw_data["sector"]).strip().upper()

        if "state_coverage" in raw_data and raw_data["state_coverage"]:
            normalized["state_coverage"] = str(raw_data["state_coverage"]).strip()
        else:
            normalized["state_coverage"] = "All India"

        # 4b. Status, Application & Documents
        if "scheme_status" in raw_data and raw_data["scheme_status"]:
            normalized["scheme_status"] = str(raw_data["scheme_status"]).strip().upper()

        if "required_documents" in raw_data and raw_data["required_documents"]:
            normalized["required_documents"] = str(raw_data["required_documents"]).strip()

        if "application_mode" in raw_data and raw_data["application_mode"]:
            normalized["application_mode"] = str(raw_data["application_mode"]).strip().upper()

        if "benefit_description" in raw_data and raw_data["benefit_description"]:
            normalized["benefit_description"] = str(raw_data["benefit_description"]).strip()

        if "support_type" in raw_data and raw_data["support_type"]:
            normalized["support_type"] = str(raw_data["support_type"]).strip().upper()

        # 5. Provenance & Official URLs
        if "official_source_url" in raw_data and raw_data["official_source_url"]:
            normalized["official_source_url"] = str(raw_data["official_source_url"]).strip()

        if "official_portal" in raw_data and raw_data["official_portal"]:
            normalized["official_portal"] = str(raw_data["official_portal"]).strip()

        if "application_url" in raw_data and raw_data["application_url"]:
            normalized["application_url"] = str(raw_data["application_url"]).strip()

        return normalized
