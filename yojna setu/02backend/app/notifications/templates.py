import json
from typing import Dict, Any, Tuple


def build_notification_content(
    notification_type: str,
    application_id: str,
    scheme_name: str = "",
    extra_context: Dict[str, Any] = None
) -> Tuple[str, str, str, str]:
    """
    Builds (title, message, priority, metadata_json) for a given notification type.
    Includes deep-link paths (e.g. /applications/:id or /partner/applications/:id).
    """
    ctx = extra_context or {}
    scheme_str = scheme_name if scheme_name else f"Application {application_id}"

    title = "YojnaSetu Notification"
    message = f"Update regarding application {application_id}."
    priority = "NORMAL"
    deep_link = f"/applications/{application_id}"

    if notification_type == "APPLICATION_CREATED":
        title = "Application Draft Created"
        message = f"Your application draft for '{scheme_str}' has been initialized."
        priority = "LOW"
        deep_link = f"/applications/{application_id}"

    elif notification_type == "APPLICATION_SUBMITTED":
        target_role = ctx.get("target_role", "BENEFICIARY")
        if target_role == "BENEFICIARY":
            title = "Application Submitted Successfully"
            message = f"Your application for '{scheme_str}' has been submitted and sent for partner agency review."
            priority = "NORMAL"
            deep_link = f"/applications/{application_id}"
        else:
            title = "New Application Submitted for Review"
            message = f"A new application ({application_id}) for '{scheme_str}' has been submitted to your organization queue."
            priority = "HIGH"
            deep_link = f"/partner/applications/{application_id}"

    elif notification_type == "APPLICATION_ASSIGNED":
        title = "Application Assigned for Review"
        message = f"Application {application_id} for '{scheme_str}' has been assigned to you for verification."
        priority = "NORMAL"
        deep_link = f"/partner/applications/{application_id}"

    elif notification_type == "APPLICATION_UNDER_REVIEW":
        title = "Review Underway"
        message = f"Your application for '{scheme_str}' is now under active review by the channelizing authority."
        priority = "NORMAL"
        deep_link = f"/applications/{application_id}"

    elif notification_type == "DOCUMENT_VERIFIED":
        doc_name = ctx.get("document_name", "Document")
        title = "Document Verified"
        message = f"Your submitted '{doc_name}' for '{scheme_str}' has been successfully verified."
        priority = "NORMAL"
        deep_link = f"/applications/{application_id}"

    elif notification_type == "DOCUMENT_REJECTED":
        doc_name = ctx.get("document_name", "Document")
        reason = ctx.get("reason", "Please check verification guidelines.")
        title = "Document Requires Revision"
        message = f"Your document '{doc_name}' was rejected: {reason}"
        priority = "HIGH"
        deep_link = f"/applications/{application_id}"

    elif notification_type == "CORRECTION_REQUIRED":
        reason = ctx.get("reason", "Corrections required before approval.")
        title = "Action Required: Application Correction Needed"
        message = f"Action required: corrections are needed for your application. Reason: {reason}"
        priority = "URGENT"
        deep_link = f"/applications/{application_id}"

    elif notification_type == "APPLICATION_RESUBMITTED":
        title = "Corrected Application Resubmitted"
        message = f"Beneficiary has resubmitted corrected documents for application {application_id}."
        priority = "HIGH"
        deep_link = f"/partner/applications/{application_id}"

    elif notification_type == "APPLICATION_APPROVED":
        title = "Good News! Application Approved"
        message = f"Congratulations! Your application for '{scheme_str}' has been approved by the channelizing authority."
        priority = "URGENT"
        deep_link = f"/applications/{application_id}"

    elif notification_type == "APPLICATION_REJECTED":
        reason = ctx.get("reason", "Ineligible based on scheme criteria.")
        title = "Application Status Update"
        message = f"Your application for '{scheme_str}' has been rejected. Reason: {reason}"
        priority = "HIGH"
        deep_link = f"/applications/{application_id}"

    elif notification_type == "SYSTEM_INFO":
        title = ctx.get("title", "System Update")
        message = ctx.get("message", "Welcome to YojnaSetu platform.")
        priority = "LOW"
        deep_link = "/notifications"

    elif notification_type == "SYSTEM_WARNING":
        title = ctx.get("title", "System Advisory")
        message = ctx.get("message", "Please check your account details.")
        priority = "HIGH"
        deep_link = "/notifications"

    metadata = {
        "application_id": application_id,
        "deep_link": deep_link,
        "notification_type": notification_type,
        "extra": ctx
    }

    return title, message, priority, json.dumps(metadata)
