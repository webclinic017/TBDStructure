from django.urls import path

from core.views import (
    UserViewList,
    LoginView,
    MonitorStockList,
    MonitorStockDetails,
    PortHistoryList,
    PortHistoryDetails,
)

from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path('user/', UserViewList.as_view()),
    path('login/', LoginView.as_view()),
    path('monitorstock/', MonitorStockList.as_view()),
    path('monitorstock/<int:pk>/', MonitorStockDetails.as_view()),
    path('porthistory/', PortHistoryList.as_view()),
    path('porthistory/<int:pk>/', PortHistoryDetails.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)