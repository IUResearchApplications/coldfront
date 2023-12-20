from datetime import tzinfo
from zoneinfo import ZoneInfo

from django.shortcuts import render
from django.utils.cache import add_never_cache_headers
from django.contrib import messages
from django_q.tasks import  Schedule

from coldfront.plugins.maintenance_mode.utils import get_maintenance_mode_status, get_maintenance_time_range


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if not get_maintenance_mode_status():
            if path in ['/', '/center-summary']:
                maintenance_schedules = Schedule.objects.filter(
                    name='Maintenance'
                ).order_by('next_run')
                times = get_maintenance_time_range(maintenance_schedules)
                if times is not None:
                    start_date, start_time, stop_time = times
                    messages.warning(
                        request,
                        f'This site will be undergoing maintenance and inaccessable on '
                        f'{start_date}, from {start_time} to {stop_time} EST'
                    )
                else:
                    monthly_maintenance_schedules = Schedule.objects.filter(
                        name='Monthly Maintenance'
                    ).order_by('next_run')
                    times = get_maintenance_time_range(monthly_maintenance_schedules)
                    if times is not None:
                        start_date, start_time, stop_time = times
                        messages.warning(
                            request,
                            f'This site will be undergoing maintenance and inaccessable on '
                            f'{start_date}, from {start_time} to {stop_time} EST'
                        )

            return self.get_response(request)

        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)

        if '/admin' in path:
            return self.get_response(request)

        # This allows the cas login to complete
        if '/user/login' in path:
            return self.get_response(request)

        response = render(
            request,
            'maintenance_mode/503.html',
            status=503
        )
        add_never_cache_headers(response)

        return response
