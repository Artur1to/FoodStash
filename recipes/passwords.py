import logging

from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import password_validators_help_texts
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.core.cache import cache
from django.core.mail import EmailMessage, InvalidMailer
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.crypto import salted_hmac


logger = logging.getLogger(__name__)


class StyledPasswordFields:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'
        self.fields['new_password1'].help_text = ' '.join(password_validators_help_texts())
        self.fields['new_password2'].help_text = ''

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save(update_fields=['password'])
        return user


class AccountPasswordChangeForm(StyledPasswordFields, PasswordChangeForm):
    pass


class AccountSetPasswordForm(StyledPasswordFields, SetPasswordForm):
    pass


class AccountPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Электронная почта',
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'autocomplete': 'email'}),
    )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        subject = ''.join(render_to_string(subject_template_name, context).splitlines())
        body = render_to_string(email_template_name, context)
        try:
            EmailMessage(subject, body, from_email, [to_email]).send(using='registration')
        except (OSError, InvalidMailer) as exc:
            logger.warning(
                'Password reset email failed: %s (SMTP code: %s)',
                type(exc).__name__,
                getattr(exc, 'smtp_code', 'n/a'),
            )


class AccountPasswordResetView(PasswordResetView):
    form_class = AccountPasswordResetForm
    email_template_name = 'recipes/emails/password_reset.txt'
    subject_template_name = 'recipes/emails/password_reset_subject.txt'

    def form_valid(self, form):
        if 'registration' not in settings.MAILERS:
            form.add_error(None, 'Отправка писем пока недоступна. Попробуй позже.')
            return self.form_invalid(form)

        address_hash = salted_hmac('foodstash.password-reset', form.cleaned_data['email'].casefold()).hexdigest()
        if not cache.add(f'password-reset:{address_hash}', True, timeout=60):
            return redirect(self.get_success_url())

        self.extra_email_context = {'site_url': settings.FOODSTASH_SITE_URL}
        return super().form_valid(form)

class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = AccountSetPasswordForm

    def get_user(self, uidb64):
        user = super().get_user(uidb64)
        if user is not None and user.is_active and user.has_usable_password():
            return user
        return None
