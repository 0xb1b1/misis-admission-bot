from os import getenv
from pathlib import Path
import asyncio
from time import mktime
# import json
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from typing import Union
# import gspread
from dotenv import load_dotenv

from modules.ssheet import GSheet
from modules.checks import Checks
# from modules.db import DBManager
# from modules.models import Platform

load_dotenv()


# Create a new file and write getenv('GOOGLE_API_TOKEN') to it
with open(Path.cwd() / "google_api_creds.json", "w") as f:
    f.write(getenv('GOOGLE_API_TOKEN', ""))

sheet = GSheet('google_api_creds.json', 'misis_admission_spreadsheet',
               int(getenv("WS_CONTENT_ID", "0")),
               int(getenv("WS_TELEMETRY_ID", "")),
               int(getenv("WS_USERS_ID", "")),
               int(getenv("WS_ADMINS_ID", ""))
              )

# db = DBManager(None)
checks = Checks(getenv("ADMIN_TOKEN", "SuperSecretToken12345"))


async def gsheet_ops():
    while True:
        await asyncio.sleep(90)
        sheet.fetch_columns()
        sheet.upload_telemetry()

loop = asyncio.get_event_loop()
loop.create_task(gsheet_ops())
app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=250)


@app.get('/')
async def get_root():
    return "Hello World!"


@app.get('/ping')
async def ping():
    return {"status": "pong"}


@app.get('/reload')
async def reload():
    res = await reload_replies()
    if res['status'] != 0:
        return res
    res = await reload_users()
    if res['status'] != 0:
        return res
    return {"status": 0}


@app.get('/reload/repls')
async def reload_replies():
    try:
        sheet.fetch_columns()
    except Exception as e:
        return {"status": 1, "error": str(e)}
    return {"status": 0}


@app.get('/reload/users')
async def reload_users():
    try:
        sheet.fetch_users()
    except Exception as e:
        return {"status": 1, "error": str(e)}
    try:
        sheet.fetch_admins()
    except Exception as e:
        return {"status": 2, "error": str(e)}
    return {"status": 0}


@app.get('/all')
async def get_all():
    return sheet.columns


@app.get('/all/btns')
async def get_all_btns():
    return sheet.buttons


@app.get('/all/repls')
async def get_all_repls(data=None):
    if not data:
        data = sheet.columns
    buttons = []
    if isinstance(data, dict):
        if 'text' in data and data['is_reply']:
            button = {
                'path': '',
                'text': data['text'],
                'is_reply': data['is_reply']
            }
            buttons.append(button)
        for key in data:
            if isinstance(data[key], dict):
                sub_buttons = await get_all_repls(data[key])
                for sub_button in sub_buttons:
                    sub_button_path = key + '.' + sub_button['path']
                    if sub_button_path.endswith('.'):
                        sub_button_path = sub_button_path[:-1]
                    sub_button['path'] = sub_button_path
                buttons.extend(sub_buttons)
    return buttons


# format: /btns/1 /btns/2.0.0 /btns/3.0.1
@app.get('/btns/{path}')
async def get_btns(path: str):
    return sheet.get_btns(path)


@app.get('/repls/{path}')
async def get_replies(path: str):
    return sheet.get_replies(path)


@app.get('/count/all/btns')
async def get_count_all_btns():
    data = await get_all_btns()
    return len(data)


@app.get('/count/all/repls')
async def get_count_all_repls():
    data = await get_all_repls()
    return len(data)


@app.get('/raw')
async def get_raw_data():
    return sheet.raw_data


@app.post('/telemetry')
async def upload_telemetry(data: dict):
    sheet.add_telemetry_entries(data['events'])
    return {'status': 0}


# region User data checking
@app.get('/check/email')
async def check_email(email: str):
    is_valid = checks.email(email)
    return {'status': 0, 'is_valid': is_valid}


@app.get('/check/phone_number')
async def check_phone(phone: str):
    is_valid = checks.phone_number(phone)
    return {'status': 0, 'is_valid': is_valid}


@app.get('/check/city')
async def check_city(city: str):
    is_valid = checks.city(city)
    return {'status': 0, 'is_valid': is_valid}
# endregion


# region User management
@app.get('/users')
async def get_users():
    return sheet.users


@app.get('/users/all/{platform}')
async def get_users_by_platform(platform: str):
    return sheet.get_users_by_platform(platform)


@app.get('/users/ids/{platform}')
async def get_user_ids_by_platform(platform: str):
    return sheet.get_users_ids_by_platform(platform)


@app.post('/user/register')
async def register_user(data: dict):
    if not checks.user_data_partial(data):  # As per request: some data fields can be omitted
        return {'status': 2}
    is_added = sheet.add_user(data)
    return {'status': 0 if is_added else 1}


@app.put('/user/update')
async def update_user(data: dict):
    if not checks.user_data(data):
        return {'status': 2}
    is_updated = sheet.update_user(data)
    return {'status': 0 if is_updated else 1}


@app.put('/user/update/partial')
async def update_user_partial(data: dict):
    """Update user data partially (per provided fields)."""
    if not checks.user_data_partial(data):
        return {'status': 2}
    is_updated = sheet.update_user_partial(data)
    return {'status': 0 if is_updated else 1}


@app.get('/user/exists/{platform}/{user_id}')
async def user_exists(platform: str, user_id: int):
    is_user = sheet.is_user(platform, user_id)
    return {'status': 0, 'exists': is_user}


@app.delete('/user/{platform}/{user_id}')
async def delete_user(platform: str, user_id: int):
    is_deleted = sheet.delete_user(platform, user_id)
    if is_deleted:
        status = 0
    else:
        status = 1
    return {'status': status}


@app.get('/user/{platform}/{user_id}')
async def get_user(platform: str, user_id: int):
    user = sheet.get_user(platform, user_id)
    if user:
        return user
    return {'status': 1}
# endregion


# region Admin management
@app.get('/admins/{platform}')
async def get_admins(platform: str):
    return sheet.get_admins(platform)


@app.post('/admin/enroll')
async def enroll_admin(data: dict):
    """Enroll admin to the system."""
    if not checks.admin_token(data['token']):
        return {'status': 1}
    is_enrolled = sheet.add_admin(data['user_id'], data['platform'])
    if is_enrolled:
        return {'status': 0}
    return {'status': 2}


@app.delete('/admin/{platform}/{user_id}')
async def delete_admin(platform: str, user_id: int):
    """Delete admin from the system."""
    is_deleted = sheet.delete_admin(user_id, platform)
    if is_deleted:
        return {'status': 0}
    return {'status': 1}
# endregion


# @app.get('/telemetry')
# async def get_telemetry():
#     entries = db.get_all_telemetry_entries()
#     res = []
#     for entry in entries:  # timestamp in unix time
#         if entry.platform == Platform.TELEGRAM:
#             platform = 'tg'
#         elif entry.platform == Platform.VK:
#             platform = 'vk'
#         else:
#             platform = 'unknown'
#         res.append({"id": entry.id, "button_id": entry.button_id, "platform": platform, "user_id": entry.user_id,
#                     "timestamp": mktime(entry.timestamp.timetuple())})
#     return {"entries": res}


# @app.delete('/telemetry')
# async def delete_telemetry():
#     db.delete_all_telemetry_entries()
#     return {"status": 0}
