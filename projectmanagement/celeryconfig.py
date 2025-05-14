from celery.schedules import crontab

# Define periodic tasks
beat_schedule = {
    'check-approaching-deadlines': {
        'task': 'notifications.tasks.check_approaching_deadlines',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
    'check-missed-deadlines': {
        'task': 'notifications.tasks.check_missed_deadlines',
        'schedule': crontab(minute=0, hour='*/3'),  # Every 3 hours
    },
    'update-project-metrics': {
        'task': 'analytics.tasks.update_project_metrics',
        'schedule': crontab(minute=0, hour=0),  # At midnight
    },
}

# Task settings
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Task execution settings
worker_max_tasks_per_child = 1000
broker_transport_options = {'visibility_timeout': 3600}  # 1 hour 