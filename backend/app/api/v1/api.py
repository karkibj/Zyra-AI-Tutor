from app.api.v1.practice import router as practice_router

# In the include_routers section, add:
api_router.include_router(practice_router)