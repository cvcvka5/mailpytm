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
from mailpytm import MailTMApi, MailTMAccount
from mailpytm.exceptions import TooManyRequests, RegistrationFailed

# Create a new temporary email account
account_info = MailTMApi.create_email()
print("Email Address:", account_info["address"])
print("Password:", account_info["password"])

# Use the account with MailTMAccount
with MailTMAccount(account_info["address"], account_info["password"]) as account:
    print(account.messages)  # List messages

    # Wait for an email with a subject containing 'Verification'
    try:
        message = account.wait_for_message(subject_contains="Verification", timeout=120)
        print("Found message:", message)
    except TimeoutError:
        print("No verification email received in time.")
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.