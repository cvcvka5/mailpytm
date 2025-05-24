from typing import Dict, List
import requests
import random
import string
from .exceptions import RegistrationFailed, TooManyRequests, TokenError, FetchMessagesFailed, FetchAccountFailed
import time
from abc import ABC, abstractmethod


BASE_URL = "https://api.mail.tm"


class MailTMApi:
    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} is a utility class and cannot be instantiated.")

    
    @staticmethod
    def create_email(username: str = None, password: str = None, domain: str = None, length: int = 15) -> Dict[str, str]:
        """
        Create a new email account.

        Optional parameters:
        - username: desired username; if None, a random one is generated.
        - password: desired password; if None, a random one is generated.
        - domain: email domain; if None, a random available domain is selected.
        - length: length of generated username if not provided.

        Returns a dictionary with 'address' and 'password'.
        """
        username = username if username else MailTMApi._random_string(length)
        domain = domain if domain else MailTMApi.get_domain()["domain"]
        address = f"{username}@{domain}"
        password = password if password else MailTMApi._random_string(20)

        MailTMApi.register_account(address, password)

        return {"address": address, "password": password}

    @staticmethod
    def register_account(address: str, password: str):
        """
        Register a new account with mail.tm.

        Raises:
            TooManyRequests: on HTTP 429 rate limit response.
            RegistrationFailed: on registration failure or duplicate email.
        """
        response = requests.post(f"{BASE_URL}/accounts", json={
            "address": address,
            "password": password
        })

        if response.status_code != 201:
            if response.status_code == 429:
                raise TooManyRequests(f"Registration with mail '{address}' failed.")
            elif response.status_code == 409:
                raise RegistrationFailed(f"Registration with mail '{address}' failed. Mail already exists.")

            raise RegistrationFailed(f"Registration with mail '{address}' failed.")

        return response.json()

    @staticmethod
    def fetch_token(address: str, password: str) -> str:
        """
        Retrieve authentication token for an account.

        Raises:
            TokenError: if token cannot be fetched or response is invalid.
        """
        response = requests.post(f"{BASE_URL}/token", json={
            "address": address,
            "password": password
        })

        if response.status_code != 200:
            raise TokenError(f"Token fetch failed for {address}: {response.text}")

        data = response.json()
        if "token" not in data:
            raise TokenError(f"Token not found in response for {address}")

        return data["token"]

    @staticmethod
    def get_domain() -> Dict:
        """
        Get a random available domain from mail.tm.

        Raises:
            RuntimeError: if no domains are available.
        """
        response = requests.get(f"{BASE_URL}/domains")
        domains = response.json()
        if not domains:
            raise RuntimeError("❌ No domains available from mail.tm")
        return random.choice(domains["hydra:member"])

    @staticmethod
    def get_auth_header(token: str) -> Dict:
        """
        Generate authorization header using the provided token.
        """
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _random_string(length: int) -> str:
        """
        Generate a random string of lowercase letters and digits of given length.
        """
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


class MailTMAccount:
    def __init__(self, address: str, password: str):
        """
        Initialize MailTMAccount with email address and password.
        """
        self._address = address
        self._password = password
        self._token_info = {"token": None, "time": time.time()}
        self.refresh_token()

    @property
    def address(self):
        """
        Get the email address.
        """
        return self._address

    @property
    def password(self):
        """
        Get the account password.
        """
        return self._password

    def refresh_token(self) -> str:
        """
        Fetch and update the authentication token.

        Returns the new token.
        """
        token = MailTMApi.fetch_token(self.address, self.password)
        self._token_info["token"] = token
        self._token_info["time"] = time.time()
        return token

    @property
    def token(self) -> str:
        """
        Return the current token if valid (~10 minutes old),
        otherwise refresh and return a new token.
        """
        if time.time() - self._token_info["time"] < 590:
            return self._token_info["token"]
        return self.refresh_token()

    @property
    def account_info(self):
        """
        Retrieve account information.

        Raises:
            FetchAccountFailed: if the account info cannot be retrieved.
        """
        resp = requests.get(f"{BASE_URL}/me", headers=MailTMApi.get_auth_header(self.token))
        if resp.status_code != 200:
            raise FetchAccountFailed(f"Couldn't get data for this account. {resp.text}")
        return resp.json()

    @property
    def id(self):
        """
        Get the unique ID of the account.
        """
        return self.account_info["id"]

    @property
    def messages(self) -> List[Dict]:
        """
        Retrieve list of messages for this account.

        Raises:
            FetchMessagesFailed: if messages cannot be fetched.
        """
        resp = requests.get(f"{BASE_URL}/messages", headers=MailTMApi.get_auth_header(self.token))
        if resp.status_code != 200:
            raise FetchMessagesFailed(f"Failed to get messages: {resp.text}")
        return resp.json().get("hydra:member", [])

    def get_unread_messages(self) -> List[Dict]:
        """
        Get a list of unread messages.
        """
        return [msg for msg in self.messages if not msg.get("seen", False)]

    def get_message_by_id(self, message_id: str) -> Dict:
        """
        Fetch a message by its ID.

        Raises:
            FetchMessagesFailed: if the message cannot be fetched.
        """
        resp = requests.get(f"{BASE_URL}/messages/{message_id}", headers=MailTMApi.get_auth_header(self.token))
        if resp.status_code != 200:
            raise FetchMessagesFailed(f"Failed to fetch message by ID: {resp.text}")
        return resp.json()

    def get_message_source(self, source_id: str) -> Dict:
        """
        Fetch raw source data of a message by its source ID.

        Raises:
            FetchMessagesFailed: if the source cannot be fetched.
        """
        resp = requests.get(f"{BASE_URL}/sources/{source_id}", headers=MailTMApi.get_auth_header(self.token))
        if resp.status_code != 200:
            raise FetchMessagesFailed(f"Failed to get message source: {resp.text}")
        return resp.json()

    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read by ID.

        Raises:
            FetchMessagesFailed: if marking as read fails.
        """
        headers = MailTMApi.get_auth_header(self.token)
        headers["Content-Type"] = "application/merge-patch+json"

        resp = requests.patch(f"{BASE_URL}/messages/{message_id}", headers=headers, json={})

        if resp.status_code != 200:
            raise FetchMessagesFailed(f"Failed to mark message {message_id} as read: {resp.text}")
        return resp.json().get("seen", False)

    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message by its ID.

        Returns True if deletion succeeded.
        """
        resp = requests.delete(f"{BASE_URL}/messages/{message_id}", headers=MailTMApi.get_auth_header(self.token))
        return resp.status_code == 204

    def wait_for_message(self, subject_contains: str, timeout: int = 60, interval: int = 5) -> Dict:
        """
        Poll for a message containing `subject_contains` in the subject line.

        Polls every `interval` seconds, up to `timeout` seconds total.

        Raises:
            TimeoutError: if no matching message is found within the timeout.
        """
        end = time.time() + timeout
        while time.time() < end:
            for msg in self.messages:
                if subject_contains.lower() in msg["subject"].lower():
                    return msg
            time.sleep(interval)
        raise TimeoutError(f"Mail with subject containing '{subject_contains}' not received in {timeout} seconds.")

    def delete_account(self) -> bool:
        """
        Delete this mail.tm account.

        Returns True if deletion succeeded.
        """
        resp = requests.delete(f"{BASE_URL}/accounts/{self.id}", headers=MailTMApi.get_auth_header(self.token))
        return resp.status_code == 204

    def __repr__(self):
        return f"Email('{self._address}')"

    def __enter__(self):
        """
        Enable usage as a context manager.

        Returns self.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Deletes the account when exiting the context manager.
        """
        self.delete_account()