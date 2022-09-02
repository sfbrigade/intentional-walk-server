# Import API views
from .api.appuser import AppUserCreateView, AppUserDeleteView
from .api.dailywalk import DailyWalkCreateView, DailyWalkListView
from .api.intentionalwalk import IntentionalWalkView, IntentionalWalkListView
from .api.contest import ContestCurrentView
from .api.intentionalwalk import IntentionalWalkListView, IntentionalWalkView
from .web.data import (
    daily_walks_csv_view,
    intentional_walks_csv_view,
    user_agg_csv_view,
    users_csv_view,
)

# Import web views
from .web.home import HomeView
from .web.intentionalwalk import IntentionalWalkWebView
from .web.user import UserListView
