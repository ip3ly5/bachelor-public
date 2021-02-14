# Food4Thought
### Web development bachelor project by Lewis Burtt-Smith and Dan Eskildsen
Based from the webapp Dkdealer by Lewis Burtt-Smith

Required installations:
- Python
- Django
- Docker
- Redis

Local install instructions:
- Set up environment (optional)
- pip install -r requirements.txt
- docker run -p 6379:6379 -d redis:5
- python manage.py makemigrations
- python manage.py migrate
- python manage.py rqworker (for email processes)
- python manage.py runserver (in settings.py dir) (new terminal)

Passwords have been removed from email server for security purposes.
If interested you can use your own gmail username and password, after allowing "less secure 3rd party apps". [read more](https://support.google.com/accounts/answer/6010255?hl=en)

Pre-made logins:

Username|Password

- lewis|root

- admin|root

- dan|root

- test|root
