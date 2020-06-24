# Import API views
from .api.appuser import AppUserCreateView
from .api.dailywalk import DailyWalkCreateView, DailyWalkListView
from .api.intentionalwalk import IntentionalWalkView, IntentionalWalkListView
from .api.contest import ContestCurrentView

# Import web views
from .web.home import HomeView
from .web.intentionalwalk import IntentionalWalkWebView
from .web.user import UserListView
