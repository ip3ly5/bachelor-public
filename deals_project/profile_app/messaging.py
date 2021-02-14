from django.core.mail import send_mail
from django.template.loader import render_to_string

def email_message(message_dict):

    msg_plain = render_to_string('profile_app/email.txt', {'posts': message_dict['posts']})
    msg_html = render_to_string('profile_app/email.html', {'posts': message_dict['posts']})

    send_mail(
        'Your Subscription List',
        msg_plain,
        'ip3ly5@gmail.com',
        [message_dict['email']],
        fail_silently=False,
        html_message=msg_html,
    )
