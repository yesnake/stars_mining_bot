from .user.start import router as start_router
from .user.start_miner import router as start_miner_router

def setup_routers() -> list:
    return [
        start_router,
        start_miner_router,
    ]