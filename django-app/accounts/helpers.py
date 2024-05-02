from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .models import PostTickets


@receiver(post_save, sender=PostTickets)
def send_approval_email(sender, instance, created, **kwargs):
    if instance.approve and not instance.email_sent:
        subject = "Your ticket has been approved"
        message = "Congratulations! Your ticket has been approved."
        recipient_email = instance.user.email
        print(recipient_email, "hellol")

        context = {}
        html_message = render_to_string("ticket_approval_email.html", context)

        send_html_email(subject, [recipient_email], html_message=html_message)

        instance.email_sent = True
        instance.save()


def send_html_email(subject, recipient_list, html_message):
    # Create the Mail object
    message = Mail(
        from_email="admin@django-tickets.com",
        to_emails=recipient_list,
        subject=subject,
        html_content=html_message,
    )

    try:
        # Initialize the SendGrid client
        sg = SendGridAPIClient(
            "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"
        )
        # Send the email
        response = sg.send(message)
        return True
    except Exception as e:
        print(e)
        return False


def forget_password_mail(domain, email, token):
    subject = "Your Forget password Link"

    # Get the current domain
    # domain = current_site
    print(domain)
    context = {
        "token": token,
        "domain": domain,  # Pass the domain to the template
    }
    html_message = render_to_string("forget_password_mail.html", context)

    recipient_list = [email]
    send_html_email(subject, recipient_list, html_message)
    return True


def exchange_request_mail(domain, recipient_email, ticket_id):
    subject = "You received an exchange request"
    context = {
        "ticket_id": ticket_id,
        "domain": domain,
    }
    html_message = render_to_string("exchange_request_email.html", context)
    recipient_list = [recipient_email]

    send_html_email(subject, recipient_list, html_message)
    return True


def payment_reciept_mail(domain, recipient_email):
    subject = "Sucessfully Subscribed!"
    context = {"domain": domain}
    html_message = render_to_string("payment_reciept.html", context)
    recipient_list = [recipient_email]

    send_html_email(subject, recipient_list, html_message)
    return True


# def exchange_request_mail(recipient_email, ticket_id):
#     subject = "You received an exchange request"
#     message = f"Hi, click on the link to check the request for ticket ID {ticket_id}"
#     email_from = settings.EMAIL_HOST_USER
#     recipient_list = [recipient_email]


#     send_mail(subject, message, email_from, recipient_list)
#     return True
def exchange_request_approve_mail(domain, recipient_email, ticket_id):
    subject = "Congratulations! Your exchange request has been approved"
    context = {
        "ticket_id": ticket_id,
        "domain": domain,
    }
    html_message = render_to_string("exchange_approval_email.html", context)
    recipient_list = [recipient_email]

    send_html_email(subject, recipient_list, html_message)
    return True


def exchange_request_decline_mail(domain, recipient_email, ticket_id):
    subject = "Your exchange request has been declined"
    context = {"ticket_id": ticket_id, "domain": domain}
    html_message = render_to_string("exchange_decline_email.html", context)
    recipient_list = [recipient_email]

    send_html_email(subject, recipient_list, html_message)
    return True
