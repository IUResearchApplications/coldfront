import os
import logging
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def get_maintenance_mode_status():
    file_name = 'maintenance_mode.txt'
    if not os.path.isfile(file_name):
        with open(file_name, 'w') as maintenance_file:
            maintenance_file.write('0')
        
        return False
    
    with open(file_name, 'r') as maintenance_file:
        status = bool(int(maintenance_file.readline()))

    return status


def set_maintenance_mode_status(status):
    if status not in ['on', 'off']:
        logger.error(f'Failed to set maintenance mode status to {status}')

    toggle = False
    if status == 'on':
        toggle = True

    file_name = 'maintenance_mode.txt'
    with open(file_name, 'w') as maintenance_file:
        maintenance_file.write(str(int(toggle)))

    logger.info(f'Maintenance mode has been set to {status}')


def get_maintenance_time_range(schedules):
    if len(schedules) != 2:
        return None
    maintenance_start = schedules[0]
    maintenance_stop = schedules[1]
    if maintenance_start.args != "'on'" or maintenance_stop.args != "'off'":
        return None
    tz = ZoneInfo('America/Indianapolis')
    maintenance_start = maintenance_start.next_run.astimezone(tz)
    if maintenance_start > (datetime.today().astimezone(tz) + timedelta(days=7)):
        return None
    maintenance_start_date = maintenance_start.strftime('%A, %B %d')
    maintenance_start_time = maintenance_start.strftime('%I:%M %p')
    maintenance_stop_time = maintenance_stop.next_run.astimezone(tz).strftime('%I:%M %p')

    return maintenance_start_date, maintenance_start_time, maintenance_stop_time