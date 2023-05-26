#!/usr/bin/env python3

"""Checks for input data."""

import re


class Checks:
    def __init__(self, admin_token: str):
        self.admin_token_store = admin_token

    def admin_token(self, token: str) -> bool:
        return token == self.admin_token_store

    def user_data(self, data: dict) -> bool:
        """Check if user data is valid."""
        if 'user_id' not in data:
            return False
        if isinstance(data['user_id'], str):
            try:
                data['user_id'] = int(data['user_id'])
            except ValueError:
                return False
        if not data['user_id'] > 0:
            return False
        if not self.phone_number(data['phone_number']):
            return False
        if not self.email(data['email']):
            return False
        if not self.city(data['city']):
            return False
        if not data['platform'] in ['tg', 'vk']:
            return False
        return True

    def user_data_partial(self, data: dict) -> bool:
        """Check if user data is valid for provided fields only."""
        if 'user_id' not in data:
            return False
        if isinstance(data['user_id'], str):
            try:
                data['user_id'] = int(data['user_id'])
            except ValueError:
                return False
        if not data['user_id'] > 0:
            return False
        if ('phone_number' not in data
                and 'email' not in data
                and 'city' not in data
                and 'platform' not in data
                and 'user_id' not in data):
            return False
        if 'phone_number' in data:
            if not self.phone_number(data['phone_number']):
                return False
        if 'email' in data:
            if not self.email(data['email']):
                return False
        if 'city' in data:
            if not self.city(data['city']):
                return False
        if 'platform' not in data:
            return False
        if not data['platform'] in ['tg', 'vk']:
            return False
        return True

    @staticmethod
    def phone_number(phone: str) -> bool:
        """Check if a phone number is valid.

        A valid phone number should look like 79991234455.
        """
        return bool(re.match(r'^7\d{10}$', phone)) if phone else True

    def email(self, email: str) -> bool:
        """Check if an email is valid.

        Provided domain names are verified against a pre-defined list.
        """
        if email is None:
            return True
        return (bool(re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email))
                and self.email_domain(email.split('@')[1]))

    @staticmethod
    def email_domain(domain: str):
        """Check if a domain is valid against a list of known email domains."""
        domains = [
            'gmail.com',
            'yahoo.com',
            'hotmail.com',
            'aol.com',
            'msn.com',
            'live.com',
            'outlook.com',
            'icloud.com',
            'privaterelay.appleid.com',
            'mail.ru',
            'inbox.ru',
            'list.ru',
            'bk.ru',
            'rambler.ru',
            'edu.misis.ru',
            # Yandex domains
            'yandex.ru',
            'ya.ru',
            'yandex.ua',
            'yandex.by',
            'yandex.kz',
            'yandex.com',
            'yandex.com.tr',
            'yandex.fr',
            'yandex.it',
            'yandex.de',
            'yandex.co.il',
            'yandex.co.jp',
            'yandex.co.uk',
            'yandex.es',
            'yandex.lv',
            'yandex.lt'
        ]
        return domain in domains

    @staticmethod
    def city(city: str) -> bool:
        """Check if a city is valid.

        A valid city should look like <at least 2 letters, first one is capital,
        dashes are allowed but not mandatory, letters after dashes can be capital or not,
        but trailing dashes are forbidden>. City names can be in Russian or English.
        Provided city names are verified against a pre-defined list.
        """
        return bool(re.match(r'^[A-ZА-Я][a-zа-я]+(-[A-ZА-Яa-zа-я]+)*$', city)) if city else True
