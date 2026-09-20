from fastapi import APIRouter
from app.api.v1.endpoints import auth, profile, schemes, recommendations, applications, partner, calculator, ai, admin, notifications, saved_schemes, health, ingestion, financial_health, blogs

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health & Readiness"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Access Control"])
api_router.include_router(profile.router, prefix="/profile", tags=["Citizen Profile & Smart Matching"])
api_router.include_router(schemes.router, prefix="/schemes", tags=["Scheme Discovery"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Scheme Recommendations"])
api_router.include_router(applications.router, prefix="/applications", tags=["Beneficiary Applications"])
api_router.include_router(saved_schemes.router, prefix="/saved-schemes", tags=["Saved Schemes"])
api_router.include_router(partner.router, prefix="/partner", tags=["Partner & Authority Review"])
api_router.include_router(partner.router, prefix="/partners", tags=["Partner & Authority Review"])
api_router.include_router(admin.router, prefix="/admin", tags=["System Admin & Management"])
api_router.include_router(calculator.router, prefix="/calculator", tags=["Financial Calculator"])
api_router.include_router(financial_health.router, prefix="/financial-health", tags=["Financial Health & Suitability"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI & NLP Intelligence Layer"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications & Alerts"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Dynamic Scheme Data Ingestion Pipeline"])
api_router.include_router(blogs.router, prefix="/blogs", tags=["Financial Blogs"])
api_router.include_router(blogs.admin_router, prefix="/admin/blogs", tags=["System Admin & Management"])

