# django-calendly
## About
A Calendar Slot Booking service, similar to that of Calendly, which allows people to define their available slots on a day and other people to book them.
The server of this application is built on the Python framework Django.

## Setup
Run the following commands to setup the application on your machine:
```bash
./server-setup.sh
source pyenv/bin/activate
python manage.py migrate
```
## Start the server
1. Activate the virtual environment by running the command:
    ```bash
    source pyenv/bin/activate
    ```
2. Start the Django Server by running the command:
    ```bash
    python manage.py runserver
    ```
    The application starts listening on http://127.0.0.1:8000/.

## Author
Akash Agrawal