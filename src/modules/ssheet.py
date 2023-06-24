from pathlib import Path
import gspread
from gspread.exceptions import APIError
import json
from typing import List, Union, Dict
from time import sleep
from datetime import datetime
from modules import naming
from config import log
import csv, os


class GSheet:
    def __init__(self, creds_file: str, sheet_key: str,
                 ws_content_id: int, ws_telemetry_id: int,
                 ws_users_id: int, ws_admins_id: int,
                 cooldown: int = 5, backup_dir: Path | None = None):
        self.backup_dir: Path | None = backup_dir
        # Create creds pseudo-file in memory with IO
        gc = gspread.service_account(filename=creds_file)
        self.sh = gc.open_by_key(sheet_key)
        self.cooldown = cooldown
        self.ws_content = self.sh.get_worksheet_by_id(ws_content_id)
        self.ws_telemetry = self.sh.get_worksheet_by_id(ws_telemetry_id)
        self.ws_users = self.sh.get_worksheet_by_id(ws_users_id)
        self.ws_admins = self.sh.get_worksheet_by_id(ws_admins_id)
        self.raw_data = self.ws_content.get_all_values()[1:]
        self.columns = {}
        self.buttons = []
        self.users = {}
        self.admins = {}
        self.fetch_columns()
        self.fetch_users()
        self.fetch_admins()
        self.make_btns()
        self.telemetry_entries: List[dict] = []

    def fetch_columns(self) -> None:
        # cols structure: {'0': {'text': 'abc', 'is_reply': 'y'}, '1': {'text': 'abc', 'is_reply': ''}, ...}
        # Get all columns from the second row, default blank is ''
        # Return to self
        try:
            cols = self.ws_content.get_all_values()[1:]
        except APIError:
            print(f"APIError occurred while fetching columns; retrying after {self.cooldown} seconds...")
            sleep(self.cooldown)
            self.fetch_columns()
        # Convert to dict
        cols = {str(col[0]): col[1:] for col in cols}
        for key, value in cols.items():
            if value[0] == '':
                continue
            dic = {}
            # Text mutation
            dic.update({'text': value[0]})
            # Description mutation
            if value[1] == '':
                dic.update({'is_reply': False})
            else:
                dic.update({'is_reply': value[1].lower() == 'y'})
            # Update value
            cols[key] = dic

        json_cols = {}
        for key, value in cols.items():
            if not isinstance(value, dict):
                continue
            if value['text'] == '' and not value.get('is_reply', False):
                continue
            # splitting key to create nested dictionary
            key_list = list(map(str, key.split('.')))
            temp_dict = json_cols
            for k in key_list[:-1]:
                temp_dict = temp_dict.setdefault(k, {})
            temp_dict[key_list[-1]] = value
        self.columns = json_cols

    def fetch_users(self, return_users: bool = False) -> dict | None:
        # self.ws_users table content: timestamp, user_id, platform, first_name, last_name, username
        # Create the table hat if it doesn't exist
        if not self.ws_users.get_all_values():
            self.ws_users.append_row(['Timestamp', 'User ID', 'Platform', 'Username', 'First name', 'Last name',
                                      'City', 'Phone number', 'Email'])
        # Get all users
        users = self.ws_users.get_all_values()[1:]
        # Convert to dict
        # Timestamp format: 05.05.2023 10:49:47
        users = {f"{naming.platform_short[user[2]]}_{user[1]}": {'platform': naming.platform_short[user[2]],
                                                                 'user_id': user[1],
                                                                 'username': user[3], 'first_name': user[4],
                                                                 'last_name': user[5],
                                                                 'city': user[6], 'phone_number': user[7],
                                                                 'email': user[8],
                                                                 'timestamp': datetime.strptime(user[0],
                                                                                                '%d.%m.%Y %H:%M:%S')}
                 for user in users}
        print(f"DEBUG: users: {users}")
        if return_users:
            return users
        self.users = users

    def fetch_admins(self):
        # self.ws_admins table content: user_id, platform, timestamp
        # Create the table hat if it doesn't exist
        if not self.ws_admins.get_all_values():
            self.ws_admins.append_row(['User ID', 'Platform', 'Timestamp'])
        # Get all admins
        admins = self.ws_admins.get_all_values()[1:]
        # Convert to dict
        # Timestamp format: 05.05.2023 10:49:47
        admins = {f"{naming.platform_short[admin[1]]}_{admin[0]}": {'platform': naming.platform_short[admin[1]],
                                                                    'user_id': admin[0],
                                                                    'timestamp': datetime.strptime(admin[2],
                                                                                                   '%d.%m.%Y %H:%M:%S')}
                  for admin in admins}
        print(f"DEBUG: admins: {admins}")
        self.admins = admins

    def make_btns(self, data=None, main_func: bool = True):
        if not data:
            data = self.columns
        buttons = []
        if isinstance(data, dict):
            if 'text' in data and not data['is_reply']:
                button = {
                    'path': '',
                    'text': data['text'],
                    'is_reply': data['is_reply']
                }
                buttons.append(button)
            for key in data:
                if isinstance(data[key], dict):
                    sub_buttons = self.make_btns(data[key], main_func=False)
                    if sub_buttons is not None:
                        for sub_button in sub_buttons:
                            sub_button_path = key + '.' + sub_button['path']
                            if sub_button_path.endswith('.'):
                                sub_button_path = sub_button_path[:-1]
                            sub_button['path'] = sub_button_path
                        buttons.extend(sub_buttons)
        if main_func:
            self.buttons = buttons
        else:
            return buttons

    def get_path_data(self, btn_id: Union[int, str]):
        if isinstance(btn_id, int):
            btn_id = str(btn_id)
        data = self.columns
        # Recursively search through the data
        for i in btn_id.split('.'):
            data = data[i]
        # Return any buttons (format: { { 'path': 'full path like 1.0.1', 'text': 'text of button', 'is_reply': 'y/n' } })
        buttons = []
        if isinstance(data, dict):
            if 'text' in data:
                button = {
                    'path': btn_id,
                    'text': data['text'],
                    'is_reply': data['is_reply']
                }
                buttons.append(button)
            for key in data:
                if isinstance(data[key], dict) and 'text' in data[key]:
                    button = {
                        'path': btn_id + '.' + key,
                        'text': data[key]['text'],
                        'is_reply': data[key]['is_reply']
                    }
                    buttons.append(button)
        return buttons

    def get_btns(self, path: str):
        print(f"DEBUG: get_btns({path}): {[button for button in self.get_path_data(path) if not button['is_reply'] and button['path'] != path]},\nget_path_data({path}): {self.get_path_data(path)}")
        return [button for button in self.get_path_data(path) if not button['is_reply'] and button['path'] != path]

    def get_replies(self, path: str):
        print(f"DEBUG: get_replies({path}): {[reply for reply in self.get_path_data(path) if reply['is_reply']]},\nget_path_data({path}): {self.get_path_data(path)}")
        return [reply for reply in self.get_path_data(path) if reply['is_reply']]

    def get_btn_name(self, path: str) -> str | None:
        data = self.get_path_data(path)
        if not data:
            return None
        # Filter out replies
        data = [button for button in data if not button['is_reply']]
        if not data:
            return None
        return data[0]['text']

    def upload_telemetry(self):
        """Upload telemetry to the second Google Sheet (append)"""
        # If the worksheet is empty, add the top column
        try:
            if not self.ws_telemetry.get_all_values():
                self.ws_telemetry.append_row(['Timestamp', 'Platform', 'User ID', 'Button ID', 'Button Name'])
        except APIError:
            print("APIError occurred while uploading telemetry")
            self.create_backup()
            return
        for entry in self.telemetry_entries:
            platform = "Unknown"
            if entry['platform'] == 'tg':
                platform = "Telegram"
            elif entry['platform'] == 'vk':
                platform = "VKontakte"
            print(f"Appending row to telemetry: {datetime.fromtimestamp(entry['timestamp']).strftime('%d.%m.%Y %H:%M:%S')} {platform} {entry['user_id']} {entry['button_id']}")
            button_name = self.get_btn_name(entry['button_id'])
            if button_name is None:
                print("The telemetry entry is not a button, skipping")
                continue
            self.ws_telemetry.append_row([datetime.fromtimestamp(entry['timestamp']).strftime('%d.%m.%Y %H:%M:%S'),
                                          platform,
                                          entry['user_id'],
                                          entry['button_id'],
                                          button_name])
        self.telemetry_entries = []

    def add_telemetry_entries(self, entries: List[dict]):
        self.telemetry_entries.extend(entries)

    # region User management
    def get_admins(self, platform: str) -> List[int]:
        """Get a list of admins from the Google Sheet."""
        admins: List[int] = []
        for admin in self.admins:
            if self.admins[admin]['platform'] == platform:
                admins.append(self.admins[admin]['user_id'])
        return admins

    def add_admin(self, user_id: int, platform: str) -> bool:
        """Add an admin to the Google Sheet."""
        # Check if the admin is already in the table
        if f"{platform}_{user_id}" in self.admins:
            return False
        # Add admin to the table
        try:
            self.ws_admins.append_row([user_id, naming.platform_long[platform],
                                       datetime.now().strftime('%d.%m.%Y %H:%M:%S')])
        except APIError:
            log.error("APIError occurred while adding admin to the Google Sheet")
            self.create_backup()
            return False
        # Add admin to the admins dict
        self.admins[f"{platform}_{user_id}"] = {'user_id': user_id,
                                                'platform': platform,
                                                'timestamp': datetime.now()}
        return True

    def delete_admin(self, user_id: int, platform: str) -> bool:
        """Remove an admin from the Google Sheet."""
        # Check if the admin is in the table
        if f"{platform}_{user_id}" not in self.admins:
            return False
        # Remove admin from the table
        try:
            for row in self.ws_admins.get_all_values():
                if row[0] == str(user_id) and row[1] == platform:
                    self.ws_admins.delete_row(self.ws_admins.find(row[0]).row)
                    break
        except APIError:
            log.error("APIError occurred while removing admin from the Google Sheet")
            self.create_backup()
            return False
        # Remove admin from the admins dict
        del self.admins[f"{platform}_{user_id}"]
        return True

    def add_user(self, data) -> bool:
        """Add user to Google Sheets.

        If the user is already in the table, do nothing and return False."""
        # Check if the user is already in the table
        if f"{data['platform']}_{data['user_id']}" in self.users:
            return False
        # Add user to the table
        try:
            self.ws_users.append_row([datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                                      data['user_id'],
                                      naming.platform_long[data['platform']],
                                      data['username'] if 'username' in data else None,
                                      data['first_name'] if 'first_name' in data else None,
                                      data['last_name'] if 'last_name' in data else None,
                                      data['city'] if 'city' in data else None,
                                      data['phone_number'] if 'phone_number' in data else None,
                                      data['email'] if 'email' in data else None])
        except APIError:
            log.error("APIError occurred while adding user to the Google Sheet")
            self.create_backup()
            return False
        # Add user to the users dict
        self.users[f"{data['platform']}_{data['user_id']}"] = data
        return True

    def update_user(self, data: dict, panic_on_not_found: bool = False) -> bool:
        """Update user in Google Sheets."""
        found = False
        # Check if the user is in the table
        if f"{data['platform']}_{data['user_id']}" in self.users:
            # Update user in the table
            try:
                for row in self.ws_users.get_all_values():
                    if row[1] == str(data['user_id']) and row[2] == naming.platform_long[data['platform']]:
                        # Update the whole row with the new data
                        self.ws_users.update(f"B{self.ws_users.find(row[0]).row}:I{self.ws_users.find(row[0]).row}",
                                             [[data['user_id'],
                                               naming.platform_long[data['platform']],
                                               data['username'] if 'username' in data else None,
                                               data['first_name'] if 'first_name' in data else None,
                                               data['last_name'] if 'last_name' in data else None,
                                               data['city'] if 'city' in data else None,
                                               data['phone_number'] if 'phone_number' in data else None,
                                               data['email'] if 'email' in data else None]])
                        found = True
                        break
            except APIError:
                log.error("APIError occurred while updating user in the Google Sheet")
                self.create_backup()
                return False
        if not found:
            if panic_on_not_found:
                raise ValueError(f"User {data['user_id']} not found in the Google Sheet")
            found = self.add_user(data)
        # Update user in the users dict
        self.users[f"{data['platform']}_{data['user_id']}"] = data
        return found

    def update_user_partial(self, data: dict) -> bool:
        """Update provided user columns in Google Sheets."""
        # Merge new data into the existing user data
        user = (self.users[f"{data['platform']}_{data['user_id']}"]
                if f"{data['platform']}_{data['user_id']}" in self.users else {})
        user.update(data)
        return self.update_user(user)

    def get_user(self, platform: str, user_id: int):
        """Get user from Google Sheets."""
        if f"{platform}_{user_id}" not in self.users:
            return None
        return self.users[f"{platform}_{user_id}"]

    def get_users_by_platform(self, platform: str) -> Dict[int, dict]:
        """Get all users of the platform from Google Sheets."""
        return {int(user_id.split('_')[1]): user for user_id, user in self.users.items()
                if user['platform'] == platform}

    def get_users_ids_by_platform(self, platform: str) -> List[int]:
        """Get all users IDs of the platform from Google Sheets."""
        return [int(user['user_id']) for user in self.users.values() if user['platform'] == platform]

    def is_user(self, platform: str, user_id: int) -> bool:
        """Check if the user is in the table."""
        return f"{platform}_{user_id}" in self.users

    def delete_user(self, platform: str, user_id: int) -> bool:
        """Delete user from Google Sheets.

        If the user is not in the table, do nothing and return False."""
        if f"{platform}_{user_id}" not in self.users:
            return False
        del self.users[f"{platform}_{user_id}"]
        # Remove user from the table
        try:
            for i, row in enumerate(self.ws_users.get_all_values()):
                print(f'evaluating row {i + 1}: {row}: [{row[2]}]{row[2] == naming.platform_long[platform]} [{row[1]}]{row[1] == str(user_id)}')
                if row[2] == naming.platform_long[platform] and row[1] == str(user_id):
                    self.ws_users.delete_rows(i + 1)
                    break
        except APIError:
            log.error("APIError occurred while deleting user from the Google Sheet")
            self.create_backup()
            return False
        return True
    # endregion

    # region Integrity checks
    # This region is dedicated to checking the data integrity of Google Sheet data
    def remote_users_absent(self) -> bool:
        """
        Check user data integrity in Google Sheets.

        :return:

        Check whether all users are present in the Google Sheet (ws_users page).
        """
        gs_users_keys: list = list(self.fetch_users(return_users=True).keys())
        absent_user_ids: list = list()
        for user_id in self.users.keys():
            if user_id not in gs_users_keys:
                absent_user_ids.append(user_id)
        if not absent_user_ids:
            log.debug("All users are present in the Google Sheet")
            return False
        log.warning(f"{len(absent_user_ids)} users are not present in the Google Sheet")

    def create_backup(self):
        """Create a backup CSV file with all users in `self.backup_dir` if it's not none."""
        if not self.backup_dir:
            log.warning("Backup event triggered, but backup_dir is not set")
            return
        log.info("Backup event triggered; Creating a backup CSV file")
        backup_file_ts: str = datetime.now().strftime('%Y.%m.%d-%H.%M.%S')
        # Create a backup with csv module
        with open(f"{self.backup_dir}/users_{backup_file_ts}.csv", 'w', newline='') as backup_file:
            writer = csv.writer(backup_file)
            writer.writerow(['timestamp', 'user_id', 'platform', 'username', 'first_name', 'last_name', 'city',
                             'phone_number', 'email'])
            for user_id, user in self.users.items():
                writer.writerow([user['timestamp'], user['user_id'], user['platform'], user['username'],
                                 user['first_name'], user['last_name'], user['city'], user['phone_number'],
                                 user['email']])
        log.info(f"Backup file created: {backup_file_ts}.csv")

    def restore_backup(self):
        """Restore the latest backup file."""
        if not self.backup_dir:
            log.warning("Restore event triggered, but backup_dir is not set")
            return
        log.info("Restore event triggered; Restoring the latest backup file")
        # Get the latest backup file
        backup_files: list = list()
        for file in os.listdir(self.backup_dir):
            if file.endswith('.csv'):
                backup_files.append(file.split('.')[0].split('_')[1])
        if not backup_files:
            log.warning("No backup files found")
            return
        # Get the latest backup file using datetime module
        latest_backup_file: str = max(backup_files, key=lambda x: datetime.strptime(x, '%Y.%m.%d-%H.%M.%S'))
        # Restore the latest backup file with csv module
        with open(f"{self.backup_dir}/users_{latest_backup_file}.csv", 'r', newline='') as backup_file:
            reader = csv.reader(backup_file)
            next(reader)
            for row in reader:
                self.update_user({
                    'timestamp': row[0],
                    'user_id': row[1],
                    'platform': row[2],
                    'username': row[3],
                    'first_name': row[4],
                    'last_name': row[5],
                    'city': row[6],
                    'phone_number': row[7],
                    'email': row[8]
                })
        log.info(f"Backup file restored: users_{latest_backup_file}.csv")

    def ensure_data_integrity(self):
        if self.remote_users_absent():
            self.create_backup()
        # if not self.is_sheet_up_to_date():  # Should check the timestamp on a separate sheet
        #     self.restore_backup()
    # endregion
