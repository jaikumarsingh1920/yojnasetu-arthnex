"""
YojnaSetu Data Quality Audit Report Generator.
Computes before/after statistics for all 56 schemes across soft-fit dimensions,
normalized taxonomy coverage, alias counts, and data completeness.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.scheme import Scheme
from app.engine.normalization import SchemeNormalizedProfileBuilder


class DataQualityAuditReport:
    """
    Generates data quality statistics across all 56 verified schemes.
    """

    @classmethod
    def generate_report(cls, db: Session) -> Dict[str, Any]:
        schemes = db.query(Scheme).all()

        total_schemes = len(schemes)
        before_unknowns = {
            "sector": 0,
            "applicant_types": 0,
            "target_groups": 0,
            "business_stage": 0,
            "activity_type": 0,
            "geography": 0,
            "financial_terms": 0,
        }

        after_populated = {
            "normalized_sectors": 0,
            "normalized_activities": 0,
            "normalized_activity_aliases": 0,
            "normalized_applicant_types": 0,
            "normalized_target_groups": 0,
            "normalized_business_stages": 0,
            "normalized_geographies": 0,
            "normalized_support_types": 0,
            "semantic_tags": 0,
            "related_business_types": 0,
            "financial_requirement_category": 0,
        }

        total_aliases_count = 0
        total_tags_count = 0
        total_sectors_count = 0
        total_activities_count = 0
        total_business_types_count = 0

        scheme_summaries: List[Dict[str, Any]] = []

        for sch in schemes:
            # 1. Before Unknown Statistics
            if not sch.sector or sch.sector.strip().upper() in ["UNKNOWN", "NONE", "NULL", ""]:
                before_unknowns["sector"] += 1
            if not sch.applicant_types or sch.applicant_types.strip().upper() in ["UNKNOWN", "NONE", "NULL", ""]:
                before_unknowns["applicant_types"] += 1
            if not sch.target_groups and not sch.marginalized_group:
                before_unknowns["target_groups"] += 1
            if not sch.business_stage or sch.business_stage.strip().upper() in ["UNKNOWN", "NONE", "NULL", ""]:
                before_unknowns["business_stage"] += 1
            if not sch.activity_type or sch.activity_type.strip().upper() in ["UNKNOWN", "NONE", "NULL", ""]:
                before_unknowns["activity_type"] += 1
            if not sch.state_coverage and not sch.state_restriction:
                before_unknowns["geography"] += 1
            if not sch.max_loan_amount and not sch.max_project_cost:
                before_unknowns["financial_terms"] += 1

            # 2. After Normalized Profile Enrichment
            norm = SchemeNormalizedProfileBuilder.build_profile(sch)

            if norm.normalized_sectors:
                after_populated["normalized_sectors"] += 1
                total_sectors_count += len(norm.normalized_sectors)
            if norm.normalized_activities:
                after_populated["normalized_activities"] += 1
                total_activities_count += len(norm.normalized_activities)
            if norm.normalized_activity_aliases:
                after_populated["normalized_activity_aliases"] += 1
                total_aliases_count += len(norm.normalized_activity_aliases)
            if norm.normalized_applicant_types:
                after_populated["normalized_applicant_types"] += 1
            if norm.normalized_target_groups:
                after_populated["normalized_target_groups"] += 1
            if norm.normalized_business_stages:
                after_populated["normalized_business_stages"] += 1
            if norm.normalized_geographies:
                after_populated["normalized_geographies"] += 1
            if norm.normalized_support_types:
                after_populated["normalized_support_types"] += 1
            if norm.semantic_tags:
                after_populated["semantic_tags"] += 1
                total_tags_count += len(norm.semantic_tags)
            if norm.related_business_types:
                after_populated["related_business_types"] += 1
                total_business_types_count += len(norm.related_business_types)
            if norm.financial_requirement_category:
                after_populated["financial_requirement_category"] += 1

            scheme_summaries.append({
                "scheme_id": sch.scheme_id,
                "scheme_name": sch.scheme_name,
                "normalized_sectors": norm.normalized_sectors,
                "normalized_activities_count": len(norm.normalized_activities),
                "aliases_count": len(norm.normalized_activity_aliases),
                "semantic_tags_count": len(norm.semantic_tags),
                "financial_category": norm.financial_requirement_category or "UNSPECIFIED",
            })

        return {
            "total_schemes_evaluated": total_schemes,
            "before_unknown_counts": before_unknowns,
            "after_populated_counts": after_populated,
            "totals": {
                "total_aliases": total_aliases_count,
                "total_semantic_tags": total_tags_count,
                "total_normalized_sectors": total_sectors_count,
                "total_normalized_activities": total_activities_count,
                "total_related_business_types": total_business_types_count,
            },
            "scheme_summaries": scheme_summaries[:10],
        }
