from fastapi import APIRouter

router = APIRouter()

@router.get("/routes")
async def list_routes(request):
    """List all registered routes"""
    from main import app
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            })
    return {"routes": routes}
