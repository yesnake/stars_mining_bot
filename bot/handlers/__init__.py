from .user.start import router as start_router

def setup_routers() -> list:
    return [
        start_router,
    ]