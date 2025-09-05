from typing import Dict, List
import requests
import random
import string
import secrets
from .exceptions import (
    RegistrationFailed,
    TooManyRequests,
    TokenError,
    FetchMessagesFailed,
    FetchAccountFailed
)
import time

BASE_URL = "https://api.mail.tm"


class MailTMApi:
    """
    Utility class for interacting with the mail.tm API.

    Provides static methods to:
    - Create email addresses
    - Register accounts
    - Fetch auth tokens
    - Retrieve available domains
    """

    def __new__(cls, *args, **kwargs):
        """
        Prevent instantiation of this utility class.
        """
        raise TypeError(f"{cls.__name__} is a utility class and cannot be instantiated.")

    @staticmethod
    def create_email(username: str = None, password: str = None, domain: str = None, length: int = 15) -> "MailTMAccount":
        """
        Create a new email account on mail.tm.

        Args:
            username (str, optional): Desired username. If None, a random one is generated.
            password (str, optional): Desired password. If None, a random one is generated.
            domain (str, optional): Domain to use. If None, a random domain is chosen.
            length (int): Length of generated username if not provided.

        Returns:
            MailTMAccount: Initialized account object.
        """
        username = username if username else MailTMApi._random_string(length, secure=True)
        domain = domain if domain else MailTMApi.get_domain()["domain"]
        address = f"{username}@{domain}"
        password = password if password else MailTMApi._random_string(20, secure=True)

        # Register account on mail.tm
        MailTMApi.register_account(address, password)
        return MailTMAccount(address=address, password=password)

    @staticmethod
    def register_account(address: str, password: str):
        """
        Register a new account on mail.tm.

        Raises:
            TooManyRequests: If rate-limited.
            RegistrationFailed: If registration fails or email exists.
        """
        response = requests.post(f"{BASE_URL}/accounts", json={"address": address, "password": password})

        if response.status_code != 201:
            if response.status_code == 429:
                raise TooManyRequests(f"Registration with mail '{address}' failed due to rate limiting.")
            elif response.status_code == 409:
                raise RegistrationFailed(f"Registration with mail '{address}' failed. Mail already exists.")
            raise RegistrationFailed(f"Registration with mail '{address}' failed.")

        return response.json()

    @staticmethod
    def fetch_token(address: str, password: str) -> str:
        """
        Fetch authentication token for an account.

        Raises:
            TokenError: If token cannot be fetched or response invalid.
        """
        response = requests.post(f"{BASE_URL}/token", json={"address": address, "password": password})
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
            RuntimeError: If no domains are available.
        """
        response = requests.get(f"{BASE_URL}/domains")
        members = response.json().get("hydra:member", [])
        if not members:
            raise RuntimeError("❌ No domains available from mail.tm")
        return random.choice(members)

    @staticmethod
    def get_auth_header(token: str) -> Dict:
        """
        Generate an authorization header for a given token.
        """
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _random_string(length: int, secure: bool = False) -> str:
        """
        Generate a random string of lowercase letters and digits.

        Args:
            length (int): Length of string.
            secure (bool): Use secrets.choice for cryptographically secure string.

        Returns:
            str: Randomly generated string.
        """
        chars = string.ascii_lowercase + string.digits
        if secure:
            return ''.join(secrets.choice(chars) for _ in range(length))
        return ''.join(random.choices(chars, k=length))


class MailTMAccount:
    """
    Represents a mail.tm account with email and password.

    Provides methods to:
    - Fetch and refresh tokens
    - Retrieve messages
    - Mark messages as read
    - Delete messages or account
    - Wait for new messages
    """

    def __init__(self, address: str, password: str):
        """
        Initialize account with email and password.
        Automatically fetches a token.

        Args:
            address (str): Email address
            password (str): Account password
        """
        self._address = address
        self._password = password
        self._token_info = {"token": None, "time": time.time()}
        self.refresh_token()

    @property
    def address(self):
        """Return email address."""
        return self._address

    @property
    def password(self):
        """Return account password."""
        return self._password

    def refresh_token(self) -> str:
        """
        Fetch and refresh auth token for this account.

        Returns:
            str: New token
        """
        token = MailTMApi.fetch_token(self.address, self.password)
        self._token_info["token"] = token
        self._token_info["time"] = time.time()
        return token

    @property
    def token(self) -> str:
        """
        Return current valid token (~10 minutes), else refresh.
        """
        if time.time() - self._token_info["time"] < 590:  # ~10 minutes
            return self._token_info["token"]
        return self.refresh_token()

    @property
    def account_info(self) -> Dict:
        """
        Retrieve account information.

        Raises:
            FetchAccountFailed: If fetching account info fails.
        """
        resp = requests.get(f"{BASE_URL}/me", headers=MailTMApi.get_auth_header(self.token))
        if resp.status_code != 200:
            raise FetchAccountFailed(f"Couldn't get data for this account. {resp.text}")
        return resp.json()

    @property
    def id(self) -> str:
        """Return unique account ID."""
        return self.account_info.get("id")

    @property
    def messages(self) -> List[Dict]:
        """
        Retrieve all messages for this account.

        Raises:
            FetchMessagesFailed: If fetching messages fails.
        """
        resp = requests.get(f"{BASE_URL}/messages", headers=MailTMApi.get_auth_header(self.token))
        if resp.status_code != 200:
            raise FetchMessagesFailed(f"Failed to get messages: {resp.text}")
        return resp.json().get("hydra:member", [])

    def get_message_by_id(self, message_id: str) -> Dict:
        """
        Fetch a specific message by ID.

        Raises:
            FetchMessagesFailed: If fetching message fails.
        """
        resp = requests.get(f"{BASE_URL}/messages/{message_id}", headers=MailTMApi.get_auth_header(self.token))
        if resp.status_code != 200:
            raise FetchMessagesFailed(f"Failed to fetch message by ID: {resp.text}")
        return resp.json()

    def get_message_source(self, source_id: str) -> Dict:
        """
        Fetch the raw source of a message.

        Raises:
            FetchMessagesFailed: If fetching source fails.
        """
        resp = requests.get(f"{BASE_URL}/sources/{source_id}", headers=MailTMApi.get_auth_header(self.token))
        if resp.status_code != 200:
            raise FetchMessagesFailed(f"Failed to get message source: {resp.text}")
        return resp.json()

    def mark_message_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read.

        Returns:
            bool: True if message marked as read.
        """
        headers = MailTMApi.get_auth_header(self.token)
        headers["Content-Type"] = "application/merge-patch+json"
        resp = requests.patch(f"{BASE_URL}/messages/{message_id}", headers=headers, json={"seen": True})
        if resp.status_code != 200:
            raise FetchMessagesFailed(f"Failed to mark message {message_id} as read: {resp.text}")
        return resp.json().get("seen", False)

    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message by ID.

        Returns:
            bool: True if deletion succeeded.
        """
        resp = requests.delete(f"{BASE_URL}/messages/{message_id}", headers=MailTMApi.get_auth_header(self.token))
        return resp.status_code == 204

    def wait_for_new_message(self, subject_contains: str = None, timeout: int = 60, interval: int = 5) -> Dict:
        """
        Wait for a new message, optionally filtering by subject.
        Ignores messages that were already present when called.

        Args:
            subject_contains (str, optional): Text to match in subject. Defaults to None (any new message).
            timeout (int): Max seconds to wait.
            interval (int): Polling interval in seconds.

        Returns:
            dict: First new message matching filter.

        Raises:
            TimeoutError: If no message found within timeout.
        """
        existing_ids = {msg.get("id") for msg in self.messages}

        end_time = time.time() + timeout
        while time.time() < end_time:
            for msg in self.messages:
                msg_id = msg.get("id")
                if msg_id not in existing_ids:
                    if subject_contains is None or subject_contains.lower() in msg.get("subject", "").lower():
                        return msg
            time.sleep(interval)

        raise TimeoutError(f"No new message received matching '{subject_contains}' within {timeout}s")

    def delete_account(self) -> bool:
        """
        Delete this mail.tm account.

        Returns:
            bool: True if deletion succeeded.
        """
        resp = requests.delete(f"{BASE_URL}/accounts/{self.id}", headers=MailTMApi.get_auth_header(self.token))
        return resp.status_code == 204

    def __repr__(self):
        """String representation of the account."""
        return f"Email('{self._address}')"

    def __enter__(self):
        """Support for context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Deletes account when exiting context."""
        self.delete_account()
