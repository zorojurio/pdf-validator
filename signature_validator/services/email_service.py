import socket

from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse_lazy

from validator.logger import module_logger
from django.core.handlers.wsgi import WSGIRequest


logger = module_logger(__name__)


class EmailService:
    """Send email using EmailMessage."""
    FROM_EMAIL = settings.EMAIL_HOST_USER

    @staticmethod
    def send_invite_email(emails: list, path: str, request: WSGIRequest) -> None:
        """Send email using EmailMessage."""
        try:
            subject = "Invitation to PDf Validator"
            message = f"""
Hello,

We hope this message finds you well.

You have recently digitally signed a document, and we would like to invite you to PDf Validator to 
confirm your identity and access the platform securely. And the document you signed is attached to 
this email as well. To complete the sign-up process, please click on the following link:
{request.build_absolute_uri(reverse_lazy('accounts:signup'))}

PDf Validator is a platform designed to ensure the integrity and authenticity of PDF documents, 
providing a secure environment for document validation and verification.

We look forward to welcoming you to PDf Validator and assisting you with your document needs.

If you have any questions or require assistance during the sign-up process, please feel free to 
contact us at {EmailService.FROM_EMAIL}.

Best regards,

Maven Patel,
Marketing Manager
PDf Validator Team """

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=EmailService.FROM_EMAIL,
                to=emails,
                bcc=emails
            )
            with open(path, 'rb') as file:
                email.attach(file.name, file.read(), 'application/pdf')
            email.send()
        except Exception as e:
            logger.error(f"Error creating EmailMessage {e}")
