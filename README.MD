# mailpytm

A Python client library for the [mail.tm](https://mail.tm) temporary email service API.

This package allows you to easily create disposable email accounts, fetch messages, manage tokens, and interact with the mail.tm API seamlessly.

## Features

- Create and register temporary email accounts
- Fetch and read emails
- Poll and wait for specific messages
- Mark emails as read and delete them
- Manage authentication tokens automatically

## Installation

```bash
pip install mailpytm
```

## Usage

```python
from mailpytm import MailTMApi

def usage_example():
    print("=== MailTMApi Usage Example ===")

    # Create a new email account
    account = MailTMApi.create_email()
    print(f"Created account: {account.address}")
    
    # Get account token
    print(f"Token: {account.token[:10]}...")  # truncated

    # Get account info
    info = account.account_info
    print(f"Account ID: {account.id}")
    print(f"Account email: {info.get('address')}")

    # Fetch current messages
    print(f"Current messages: {len(account.messages)}")

    # Wait for new message (subject filter optional)
    try:
        print("Waiting for new messages (timeout 30s)...")
        new_msg = account.wait_for_new_message(subject_contains=None, timeout=30)
        print(f"New message received: {new_msg.get('id')}, subject: {new_msg.get('subject')}")
    except TimeoutError:
        print("No new messages arrived during the timeout.")

    # Mark first message as read if available
    if account.messages:
        msg_id = account.messages[0]["id"]
        seen = account.mark_message_as_read(msg_id)
        print(f"Message {msg_id} marked as read: {seen}")

    # Delete first message if available
    if account.messages:
        msg_id = account.messages[0]["id"]
        deleted = account.delete_message(msg_id)
        print(f"Message {msg_id} deleted: {deleted}")

    # Use context manager for temporary accounts
    with MailTMApi.create_email() as temp_account:
        print(f"Temporary account created: {temp_account.address}")
        print(f"Token: {temp_account.token[:10]}...")

    # Delete original account
    deleted = account.delete_account()
    print(f"Original account deleted: {deleted}")

    print("=== Usage example finished ===")

if __name__ == "__main__":
    usage_example()
```

## Exceptions

Exceptions are available under `mailpytm.exceptions` for fine-grained error handling:

- `TooManyRequests`
- `RegistrationFailed`
- `TokenError`
- `FetchMessagesFailed`
- `FetchAccountFailed`

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/cvcvka5/mailpytm/issues).

## License

This project is licensed under the MIT License.
