from django.core.mail import send_mail


def email_message(message_dict):
    print(message_dict)

    contents = f"""
    Hi, thank you for trying to reset your password.
    Your token is: {message_dict['token']}
    """
    send_mail(
        'Password Reset Token',
        contents,
        'food4thought@gmail.com',
        [message_dict['email']],
        fail_silently=False
    )
