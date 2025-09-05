import time
from mailpytm import MailTMApi, MailTMAccount  # replace 'your_module' with your package name

def main():
    print("=== Testing MailTMApi & MailTMAccount ===")

    # 1️⃣ Create a new email account
    print("Creating new account...")
    account = MailTMApi.create_email()
    print(f"Account created: {account.address}, password: {account.password}")

    # 2️⃣ Verify token retrieval
    print("Fetching auth token...")
    token = account.token
    print(f"Token: {token[:10]}... (truncated)")

    # 3️⃣ Fetch account info
    print("Fetching account info...")
    info = account.account_info
    print(f"Account ID: {account.id}")
    print(f"Account info keys: {list(info.keys())}")

    # 4️⃣ Fetch current messages (should be empty)
    print("Fetching current messages...")
    messages = account.messages
    print(f"Current messages count: {len(messages)}")

    # 5️⃣ Wait for a new message (simulate a message arriving)
    # NOTE: To test this properly, send an email to account.address manually.
    print("Waiting for new message (timeout 60s)...")
    try:
        new_msg = account.wait_for_new_message(timeout=60)
        print(f"New message received: {new_msg['id']}, subject: {new_msg.get('subject')}")
    except TimeoutError:
        print("No new messages arrived during test timeout.")

    # 6️⃣ Mark a message as read if available
    if messages:
        msg_id = messages[0]["id"]
        print(f"Marking message {msg_id} as read...")
        seen = account.mark_message_as_read(msg_id)
        print(f"Message marked as read: {seen}")

    # 7️⃣ Delete a message if available
    if messages:
        msg_id = messages[0]["id"]
        print(f"Deleting message {msg_id}...")
        deleted = account.delete_message(msg_id)
        print(f"Message deleted: {deleted}")

    # 8️⃣ Test __enter__ and __exit__ context manager
    print("Testing context manager for automatic deletion...")
    with MailTMApi.create_email() as temp_account:
        print(f"Temp account created: {temp_account.address}")
        print(f"Temp account token: {temp_account.token[:10]}...")

    # 9️⃣ Delete original account manually
    print("Deleting original account...")
    deleted = account.delete_account()
    print(f"Original account deleted: {deleted}")

    print("=== All tests completed ===")


if __name__ == "__main__":
    main()
