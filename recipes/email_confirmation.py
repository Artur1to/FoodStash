import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage, InvalidMailer
from django.core.signing import BadSignature, TimestampSigner
from django.template.loader import render_to_string
from django.urls import reverse


logger = logging.getLogger(__name__)
LINK_LIFETIME = timedelta(hours=24)
RESEND_DELAY = timedelta(minutes=1)


def _signer(user):
    return TimestampSigner(salt=f'foodstash.registration:{user.pk}:{user.date_joined.isoformat()}:{user.email}')


def confirmation_matches(user, token):
    try:
        return _signer(user).unsign(token, max_age=LINK_LIFETIME) == str(user.pk)
    except BadSignature:
        return False


def send_confirmation(request, user):
    token = _signer(user).sign(str(user.pk))
    path = reverse('confirm_email', args=[user.pk, token])
    link = settings.FOODSTASH_SITE_URL + path if settings.FOODSTASH_SITE_URL else request.build_absolute_uri(path)
    body = render_to_string('recipes/emails/confirm_email.txt', {'link': link})
    try:
        return EmailMessage('Подтверди почту для FoodStash', body, to=[user.email]).send(using='registration') == 1
    except (OSError, InvalidMailer) as exc:
        logger.warning(
            'Registration email failed: %s (SMTP code: %s)',
            type(exc).__name__,
            getattr(exc, 'smtp_code', 'n/a'),
        )
        return False
