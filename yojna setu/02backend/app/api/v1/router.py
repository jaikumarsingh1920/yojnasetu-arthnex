from fastapi import APIRouter
from app.api.v1.endpoints import auth, schemes, recommendations, applications, partner, calculator, ai, admin, notifications, saved_schemes, health

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health & Readiness"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Access Control"])
api_router.include_router(schemes.router, prefix="/schemes", tags=["Scheme Discovery"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["Scheme Recommendations"])
api_router.include_router(applications.router, prefix="/applications", tags=["Beneficiary Applications"])
api_router.include_router(saved_schemes.router, prefix="/saved-schemes", tags=["Saved Schemes"])
api_router.include_router(partner.router, prefix="/partner", tags=["Partner & Authority Review"])
api_router.include_router(admin.router, prefix="/admin", tags=["System Admin & Management"])
api_router.include_router(calculator.router, prefix="/calculator", tags=["Financial Calculator"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI & NLP Intelligence Layer"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications & Alerts"])
