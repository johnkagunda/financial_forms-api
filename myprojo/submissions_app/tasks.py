from celery import shared_task
from .models import Submission, Notification


@shared_task
def notify_admin(submission_id):
    """
    Async task to notify admin about a new submission.
    Instead of sending an email, store a site notification.
    """
    try:
        submission = Submission.objects.get(id=submission_id)
        message = f"New submission for form: {submission.form.name} by {submission.submitted_by or 'Anonymous'}"

        Notification.objects.create(message=message)

        return f"Notification stored for submission {submission_id}"
    except Submission.DoesNotExist:
        return f"Submission {submission_id} not found"
