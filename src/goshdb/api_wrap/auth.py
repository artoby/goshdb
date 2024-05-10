from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def authenticate(secret_dir: Path) -> Credentials:
    """
    Authenticate with Google Sheets API.
    :param secret_dir: Path to the directory containing credentials.json or token.json.
    :return: credentials object that can be used to access the Google Sheets API.
    """
    assert secret_dir.is_dir(), f'secret_dir does not exist: {secret_dir}'

    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    token_file = secret_dir / 'token.json'

    creds = None
    if token_file.is_file():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_file = secret_dir / 'credentials.json'
            if not credentials_file.is_file:
                raise ValueError(
                    f'secret_dir should contain at least one of: [token.json, credentials.json]. But it does not: {secret_dir}')
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        token_file.write_text(creds.to_json())

    return creds
