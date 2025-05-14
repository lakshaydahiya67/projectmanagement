from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')

# Create the Celery app
app = Celery('projectmanagement')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load celery config file
app.config_from_object('projectmanagement.celeryconfig')

# Auto-discover tasks from all registered Django app configs
app.autodiscover_tasks()

# Register periodic tasks
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Check for approaching deadlines every hour
    sender.add_periodic_task(
        crontab(minute=0, hour='*/1'),  # Every hour
        sender.import_task('notifications.tasks.check_approaching_deadlines').s(),
    )
    
    # Check for missed deadlines every 3 hours
    sender.add_periodic_task(
        crontab(minute=0, hour='*/3'),  # Every 3 hours
        sender.import_task('notifications.tasks.check_missed_deadlines').s(),
    )
    
    # Update project metrics once a day (at midnight)
    sender.add_periodic_task(
        crontab(minute=0, hour=0),  # At midnight
        sender.import_task('analytics.tasks.update_project_metrics').s(),
    )

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
