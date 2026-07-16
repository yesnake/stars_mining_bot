from .user.start import router as start_router
from .user.miner import router as miner_router
from .user.boost import router as boost_miner_router
from .user.withdraw import router as withdraw_router
from .user.back import router as back_router


def setup_routers() -> list:
    return [
        start_router,
        miner_router,
        boost_miner_router,
        withdraw_router,
        back_router
    ]
