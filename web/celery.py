from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

app = Celery('web')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()



app.conf.beat_schedule = {
    'create-renewal-orders-daily': {
        'task': 'apps.order.tasks.create_renewal_orders_for_expiring_restaurants',
        'schedule': 10.0,  # هر ۲۴ ساعت
    },
    'check-expired-restaurants-daily': {
        'task': 'apps.order.tasks.check_and_deactivate_expired_restaurants',
        'schedule': 10.0,  # هر ۲۴ ساعت
    },
    'send-renewal-reminders-daily': {
        'task': 'apps.order.tasks.send_renewal_reminders',
        'schedule': 10.0,  # هر ۲۴ ساعت
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
