from .user.start import router as start_router
from .user.miner import router as miner_router
from .user.boost import router as boost_miner_router
from .user.withdraw import router as withdraw_router
from .user.back import router as back_router

from .admin.admin_panel import router as admin_panel_router
from .admin.admin_stats import router as admin_stats_router
from .admin.tracking_links import router as admin_tracking_links_router
from .admin.user_actions import router as admin_user_actions_router
from .admin.broadcast import router as admin_broadcast_router
from .admin.withdraw_management import router as admin_withdraw_management_router


def setup_routers() -> list:
    return [
        start_router,
        miner_router,
        boost_miner_router,
        withdraw_router,
        back_router,
        admin_panel_router,
        admin_stats_router,
        admin_tracking_links_router,
        admin_user_actions_router,
        admin_broadcast_router,
        admin_withdraw_management_router,
    ]
