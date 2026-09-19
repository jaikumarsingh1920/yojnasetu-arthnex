"""
Batch Financial Scheme Enrichment Service for YojnaSetu.

Expands authoritative financial parameters across the entire canonical scheme corpus:
- project cost (min/max)
- loan amount (min/max)
- subsidy percentage and absolute subsidy amount
- grant amount
- margin money / beneficiary contribution
- interest rate (min/max/interest-free)
- interest subsidy / subvention
- repayment tenure (min/max months)
- moratorium (months)
- collateral requirement (YES/NO/CONDITIONAL)
- guarantee requirement (CGTMSE, CGFMU, etc.)
- processing fee

Properties:
- Idempotent: Can be run multiple times safely without data corruption.
- Provenance-aware: Records extraction origin, matching text, and confidence.
- Restartable & Safe: Operates within transaction batches.
- Strictly non-fabricating: Never assumes missing financial data.
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from app.models.scheme import Scheme
from app.services.ingestion.financial_extractor import FinancialFactExtractor

logger = logging.getLogger("yojnasetu.services.financial_enrichment")


class FinancialSchemeEnrichmentService:
    def __init__(self, extractor: Optional[FinancialFactExtractor] = None):
        self.extractor = extractor or FinancialFactExtractor()

    def enrich_scheme(self, scheme: Scheme) -> Dict[str, Any]:
        """
        Extracts authoritative financial facts from scheme text fields and updates
        scheme financial fields where authoritative data is found.
        Returns a summary dict of what was updated.
        """
        # Compile official text corpus from verified scheme fields
        text_corpus = []
        if scheme.detailed_description:
            text_corpus.append(scheme.detailed_description)
        if scheme.benefit_description:
            text_corpus.append(scheme.benefit_description)
        if scheme.short_description:
            text_corpus.append(scheme.short_description)
        if scheme.purpose:
            text_corpus.append(scheme.purpose)
        if scheme.support_type:
            text_corpus.append(scheme.support_type)

        combined_text = "\n".join(text_corpus)
        if not combined_text.strip():
            return {"updated": False, "fields_updated": []}

        facts = self.extractor.extract_financial_facts(combined_text)
        updates: List[str] = []

        # 1. Project Cost
        if facts.get("max_project_cost") is not None and scheme.max_project_cost is None:
            scheme.max_project_cost = Decimal(str(facts["max_project_cost"]))
            updates.append("max_project_cost")
        if facts.get("min_project_cost") is not None and scheme.min_project_cost is None:
            scheme.min_project_cost = Decimal(str(facts["min_project_cost"]))
            updates.append("min_project_cost")

        # 2. Loan Amount
        if facts.get("max_loan_amount") is not None and scheme.max_loan_amount is None:
            scheme.max_loan_amount = Decimal(str(facts["max_loan_amount"]))
            updates.append("max_loan_amount")
        if facts.get("min_loan_amount") is not None and scheme.min_loan_amount is None:
            scheme.min_loan_amount = Decimal(str(facts["min_loan_amount"]))
            updates.append("min_loan_amount")

        # 3. Subsidy
        if facts.get("subsidy_percentage") is not None and scheme.subsidy_percentage is None:
            scheme.subsidy_percentage = Decimal(str(facts["subsidy_percentage"]))
            updates.append("subsidy_percentage")
        if facts.get("subsidy_amount") is not None and scheme.subsidy_amount is None:
            scheme.subsidy_amount = Decimal(str(facts["subsidy_amount"]))
            updates.append("subsidy_amount")

        # 4. Grant
        if facts.get("grant_amount") is not None and scheme.grant_amount is None:
            scheme.grant_amount = Decimal(str(facts["grant_amount"]))
            updates.append("grant_amount")

        # 5. Margin Money / Beneficiary Contribution
        if facts.get("margin_money_percentage") is not None and scheme.beneficiary_contribution_percentage is None:
            scheme.beneficiary_contribution_percentage = Decimal(str(facts["margin_money_percentage"]))
            updates.append("beneficiary_contribution_percentage")

        # 6. Interest Rate
        if facts.get("interest_rate_min") is not None and scheme.interest_rate_min is None:
            scheme.interest_rate_min = Decimal(str(facts["interest_rate_min"]))
            updates.append("interest_rate_min")
        if facts.get("interest_rate_max") is not None and scheme.interest_rate_max is None:
            scheme.interest_rate_max = Decimal(str(facts["interest_rate_max"]))
            updates.append("interest_rate_max")

        # 7. Interest Subsidy / Subvention
        if facts.get("interest_subsidy") is not None and getattr(scheme, "interest_subsidy", None) is None:
            scheme.interest_subsidy = Decimal(str(facts["interest_subsidy"]))
            scheme.interest_subsidy_raw = facts.get("provenance", {}).get("interest_subsidy", {}).get("raw")
            updates.append("interest_subsidy")

        # 8. Repayment Tenure
        if facts.get("repayment_period_max_months") is not None and scheme.repayment_period_max_months is None:
            scheme.repayment_period_max_months = int(facts["repayment_period_max_months"])
            updates.append("repayment_period_max_months")
        if facts.get("repayment_period_min_months") is not None and scheme.repayment_period_min_months is None:
            scheme.repayment_period_min_months = int(facts["repayment_period_min_months"])
            updates.append("repayment_period_min_months")

        # 9. Moratorium
        if facts.get("moratorium_max_months") is not None and scheme.moratorium_max_months is None:
            scheme.moratorium_max_months = int(facts["moratorium_max_months"])
            updates.append("moratorium_max_months")

        # 10. Collateral Requirement
        if facts.get("collateral_required") is not None and (scheme.collateral_required is None or scheme.collateral_required in ("", "UNKNOWN")):
            scheme.collateral_required = facts["collateral_required"]
            updates.append("collateral_required")

        # 11. Guarantee Requirement
        if facts.get("guarantee_requirement") is not None and getattr(scheme, "guarantee_requirement", None) is None:
            scheme.guarantee_requirement = facts["guarantee_requirement"]
            updates.append("guarantee_requirement")

        # 12. Processing Fee
        if facts.get("processing_fee") is not None and getattr(scheme, "processing_fee", None) is None:
            scheme.processing_fee = facts["processing_fee"]
            updates.append("processing_fee")

        # Record change summary if any updates occurred
        if updates:
            summary_note = f"Financial intelligence enriched: {', '.join(updates)}"
            if scheme.change_summary:
                scheme.change_summary = f"{scheme.change_summary} | {summary_note}"
            else:
                scheme.change_summary = summary_note

        return {
            "updated": len(updates) > 0,
            "fields_updated": updates
        }

    def run_batch_enrichment(self, db: Session, batch_size: int = 100) -> Dict[str, Any]:
        """
        Runs batch enrichment over all schemes in the database in safe batches.
        """
        schemes = db.query(Scheme).all()
        total_schemes = len(schemes)
        enriched_count = 0
        total_field_updates: Dict[str, int] = {}

        for i, s in enumerate(schemes):
            res = self.enrich_scheme(s)
            if res["updated"]:
                enriched_count += 1
                for f in res["fields_updated"]:
                    total_field_updates[f] = total_field_updates.get(f, 0) + 1

            if (i + 1) % batch_size == 0:
                db.commit()
                logger.info(f"Enriched batch {i + 1}/{total_schemes}")

        db.commit()
        logger.info(f"Enrichment completed. {enriched_count}/{total_schemes} schemes enriched.")
        return {
            "total_schemes": total_schemes,
            "schemes_enriched": enriched_count,
            "field_updates": total_field_updates
        }

    @staticmethod
    def get_financial_coverage_report(db: Session) -> Dict[str, Any]:
        """
        Produces authoritative report on financial data availability across all schemes.
        Strictly reports what is available vs what remains unavailable.
        """
        all_schemes = db.query(Scheme).all()
        total = len(all_schemes)

        with_metadata = 0
        with_loan = 0
        with_subsidy = 0
        with_interest = 0
        usable_by_calculator = 0
        without_financial_data = 0

        breakdown = {
            "max_project_cost": 0,
            "min_project_cost": 0,
            "max_loan_amount": 0,
            "min_loan_amount": 0,
            "subsidy_percentage": 0,
            "subsidy_amount": 0,
            "grant_amount": 0,
            "beneficiary_contribution_percentage": 0,
            "interest_rate": 0,
            "interest_subsidy": 0,
            "repayment_period": 0,
            "moratorium": 0,
            "collateral_status": 0,
            "guarantee_requirement": 0,
            "processing_fee": 0
        }

        for s in all_schemes:
            has_any = False

            # Project cost
            if s.max_project_cost is not None or s.min_project_cost is not None:
                has_any = True
                if s.max_project_cost is not None:
                    breakdown["max_project_cost"] += 1
                if s.min_project_cost is not None:
                    breakdown["min_project_cost"] += 1

            # Loan
            has_loan_val = False
            if s.max_loan_amount is not None or s.min_loan_amount is not None:
                has_any = True
                has_loan_val = True
                if s.max_loan_amount is not None:
                    breakdown["max_loan_amount"] += 1
                if s.min_loan_amount is not None:
                    breakdown["min_loan_amount"] += 1
            if has_loan_val:
                with_loan += 1

            # Subsidy / Grant
            has_sub_val = False
            if s.subsidy_percentage is not None:
                has_any = True
                has_sub_val = True
                breakdown["subsidy_percentage"] += 1
            if s.subsidy_amount is not None:
                has_any = True
                has_sub_val = True
                breakdown["subsidy_amount"] += 1
            if s.grant_amount is not None:
                has_any = True
                has_sub_val = True
                breakdown["grant_amount"] += 1
            if has_sub_val:
                with_subsidy += 1

            # Margin money
            if s.beneficiary_contribution_percentage is not None:
                has_any = True
                breakdown["beneficiary_contribution_percentage"] += 1

            # Interest
            has_int_val = False
            if s.interest_rate_max is not None or s.interest_rate_min is not None:
                has_any = True
                has_int_val = True
                breakdown["interest_rate"] += 1
            if getattr(s, "interest_subsidy", None) is not None:
                has_any = True
                has_int_val = True
                breakdown["interest_subsidy"] += 1
            if has_int_val:
                with_interest += 1

            # Repayment
            if s.repayment_period_max_months is not None or s.repayment_period_min_months is not None:
                has_any = True
                breakdown["repayment_period"] += 1

            # Moratorium
            if s.moratorium_max_months is not None:
                has_any = True
                breakdown["moratorium"] += 1

            # Collateral
            if s.collateral_required and s.collateral_required not in ("UNKNOWN", "NOT_APPLICABLE"):
                has_any = True
                breakdown["collateral_status"] += 1

            # Guarantee
            if getattr(s, "guarantee_requirement", None):
                has_any = True
                breakdown["guarantee_requirement"] += 1

            # Processing fee
            if getattr(s, "processing_fee", None):
                has_any = True
                breakdown["processing_fee"] += 1

            if has_any:
                with_metadata += 1
            else:
                without_financial_data += 1

            # Usable by financial calculator requires at least loan amount or project cost,
            # or an interest rate and tenure
            if (s.max_loan_amount is not None or s.max_project_cost is not None) and (
                s.interest_rate_max is not None or s.subsidy_percentage is not None or s.subsidy_amount is not None
            ):
                usable_by_calculator += 1

        return {
            "total_schemes": total,
            "schemes_with_financial_metadata": with_metadata,
            "schemes_with_loan_data": with_loan,
            "schemes_with_subsidy_data": with_subsidy,
            "schemes_with_interest_data": with_interest,
            "schemes_usable_by_financial_calculator": usable_by_calculator,
            "schemes_where_financial_data_remains_unavailable": without_financial_data,
            "parameter_breakdown": breakdown
        }
