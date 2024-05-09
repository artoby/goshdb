from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from openpyxl.utils.cell import column_index_from_string


class Sheet:
    def __init__(self, secret_dir: Path, spreadsheet_id: str, sheet_name: str, header: list[str]):
        self.secret_dir = secret_dir
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.header = header

        self.creds = self.__authenticate(self.secret_dir)
        self.service = build("sheets", "v4", credentials=self.creds)
        self.spreadsheets = self.service.spreadsheets()
        self.sheet_id = self.__ensure_sheet_exist_and_get_id()
        self.__check_sheet_header()

    @staticmethod
    def __authenticate(secret_dir: Path) -> Credentials:
        assert secret_dir.is_dir(), f'secret_dir does not exist: {secret_dir}'

        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        token_file = secret_dir / 'token.json'

        creds = None
        if token_file.is_file():
            creds = Credentials.from_authorized_user_file(token_file, scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                credentials_file = secret_dir / 'credentials.json'
                if not credentials_file.is_file:
                    raise ValueError(
                        f'secret_dir should contain at least one of: [token.json, credentials.json]. But it does not: {secret_dir}')
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            token_file.write_text(creds.to_json())

        return creds

    def __try_get_sheet_id(self) -> Optional[int]:
        ss = self.spreadsheets.get(spreadsheetId=self.spreadsheet_id).execute()
        sheets = ss.get('sheets', [])
        target_sheet_array = [sheet for sheet in sheets if sheet['properties']['title'] == self.sheet_name]
        if len(target_sheet_array) == 1:
            return target_sheet_array[0]['properties']['sheetId']
        elif len(target_sheet_array) > 1:
            raise ValueError(f'Unexpectedly found multiple sheets with name {self.sheet_name}: {sheets}')
        else:
            return None

    def __ensure_sheet_exist_and_get_id(self) -> id:
        sheet_id = self.__try_get_sheet_id()
        if sheet_id is not None:
            return sheet_id

        # Create the sheet
        body = {
            'requests': {
                'addSheet': {
                    'properties': {
                        'title': self.sheet_name
                    }
                }
            }
        }
        self.spreadsheets.batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
        # Set the header
        self.append_row(self.header)
        # Now it'll find the new sheet and return its id
        sheet_id = self.__try_get_sheet_id()
        assert sheet_id is not None, f'Failed to create sheet {self.sheet_name}'

        self.delete_columns('C', 'Z', sheet_id=sheet_id)

    def __check_sheet_header(self):
        actual_header_raw = self.get_multiple_values('A1:Z1')
        # We allow extra columns after required header columns
        actual_header = actual_header_raw[0][:len(self.header)]
        assert actual_header == self.header, f'Expected header to be {self.header}, but got: {actual_header}'

    def append_row(self, values: list[str]) -> None:
        body = {
            'values': [values]
        }
        self.spreadsheets.values().append(spreadsheetId=self.spreadsheet_id,
                                          range=f'{self.sheet_name}!A:A',
                                          valueInputOption='RAW',
                                          body=body).execute()

    def set_multiple_values(self, range: str, values: list) -> None:
        assert '!' not in range, f'range should not contain sheet name, i.e. "!": {range}'
        body = {
            'values': values,
        }
        self.spreadsheets \
            .values() \
            .update(
            spreadsheetId=self.spreadsheet_id,
            range=f'{self.sheet_name}!{range}',
            valueInputOption='RAW',
            body=body) \
            .execute()

    def set_value(self, range: str, value: str) -> None:
        assert ':' not in range, f'range should reference only one cell but got: {range}'
        self.set_multiple_values(range, [[value]])

    def get_multiple_values(self, range: str) -> list[list[str]]:
        assert '!' not in range, f'range should not contain sheet name, i.e. "!": {range}'
        result = self.spreadsheets \
            .values() \
            .get(spreadsheetId=self.spreadsheet_id, range=f'{self.sheet_name}!{range}') \
            .execute()
        values = result.get('values', [])
        return values

    def get_value(self, range: str) -> str:
        values = self.get_multiple_values(range)
        if not values:
            return ''
        assert len(values) == 1, f'For {range} expected only one row, but got {len(values)}'
        assert len(values[0]) == 1, f'For {range} expected only one column, but got {len(values[0])}'
        return values[0][0]

    def delete_row(self, row_number: int) -> None:
        """
        :param row_number: starting from 1
        """
        body = {
            'requests': [
                {
                    'deleteDimension': {
                        'range': {
                            'sheetId': self.sheet_id,
                            'dimension': 'ROWS',
                            'startIndex': row_number - 1,
                            'endIndex': row_number
                        }
                    }
                }
            ]
        }
        self.spreadsheets.batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()

    def delete_columns(self, start_column: str, end_column: str, sheet_id: int) -> None:
        """
        start_column and end_column are letter-based, e.g. 'A', 'B', 'AA', etc.
        """
        start_column_index = column_index_from_string(start_column) - 1
        end_column_index = column_index_from_string(end_column) - 1
        body = {
            'requests': [
                {
                    'deleteDimension': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': start_column_index,
                            'endIndex': end_column_index + 1  # endIndex is exclusive
                        }
                    }
                }
            ]
        }
        self.spreadsheets.batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
