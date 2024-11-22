import os
from atproto import Client

SESSION_FILE = "session.txt"


def get_session() -> str:
    """Retrieve session string from file."""
    try:
        with open(SESSION_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None


def save_session(session_string: str) -> None:
    """Save session string to file."""
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        f.write(session_string)


def init_client() -> Client:
    """Initialize the standard ATProto Client with session management."""
    client = Client()

    session_string = get_session()
    if session_string:
        client.login(session_string=session_string)
    else:
        username = os.getenv("USERNAME")
        password = os.getenv("PASSWORD")
        print("Logging in with username and password...")
        client.login(username, password)

    return client