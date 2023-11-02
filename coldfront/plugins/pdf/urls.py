from django.urls import path

from coldfront.plugins.pdf.views import UserReportPDFView

urlpatterns = [
    path('user-report/', UserReportPDFView.as_view(), name='user-report')
]