from flask import session, redirect, url_for

import app_project as app
from testing import USER_MESSAGES_FILE


def save_user_data(user_data):
    with open(app.USER_DATA_FILE, 'w') as file:
        for username, password in user_data.items():
            file.write(f'{username} {password}\n')


def edit_user_data(user_data):
    with open(app.USER_DATA_FILE, 'w') as file:
        for username, password in user_data.items():
            file.write(f'{password}\n')


def load_user_data():
    try:
        with open(app.USER_DATA_FILE, 'r') as file:
            data = file.readlines()
        return {line.split()[0]: line.split()[1] for line in data}
    except FileNotFoundError:
        return {}


def load_instructor_data():
    try:
        with open(app.INSTRUCTOR_DATA_FILE, 'r') as file:
            data = file.readlines()
        return {line.split()[0]: line.split()[1] for line in data}
    except FileNotFoundError:
        return {}


def save_instructor_data(instructor_data):
    with open(app.INSTRUCTOR_DATA_FILE, 'w') as file:
        for instructor_id, password in instructor_data.items():
            file.write(f'{instructor_id} {password}\n')



