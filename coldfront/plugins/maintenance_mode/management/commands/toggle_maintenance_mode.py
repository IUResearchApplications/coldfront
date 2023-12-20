import logging

from django.core.management.base import BaseCommand, CommandError

from coldfront.plugins.maintenance_mode.utils import set_maintenance_mode_status

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Turns maintenance mode on or off'

    def add_arguments(self, parser):
        parser.add_argument("-s", "--status", help="Turn maintenance mode on/off")

    def handle(self, *args, **options):
        status = options.get('status')
        if status is None:
            raise CommandError('Please provide a status (on/off)')
        
        if status not in ['on', 'off']:
            logger.warning(f'Failed to set maintenance mode status to {status}')
            raise CommandError('Invalid command, status must be set with on/off')

        set_maintenance_mode_status(status)
