from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openpyxl.utils.cell import column_index_from_string


class Spreadsheet:
    def __init__(self, creds: Credentials, spreadsheet_id: str):
        self.creds = creds
        self.spreadsheet_id = spreadsheet_id

        self.service = build("sheets", "v4", credentials=self.creds)
        self.spreadsheets = self.service.spreadsheets()

    def try_get_sheet_id(self, sheet_name: str) -> Optional[int]:
        ss = self.spreadsheets.get(spreadsheetId=self.spreadsheet_id).execute()
        sheets = ss.get('sheets', [])
        target_sheet_array = [sheet for sheet in sheets if sheet['properties']['title'] == sheet_name]
        if len(target_sheet_array) == 1:
            return target_sheet_array[0]['properties']['sheetId']
        elif len(target_sheet_array) > 1:
            raise ValueError(f'Unexpectedly found multiple sheets with name {sheet_name}: {sheets}')
        else:
            return None

    def has_sheet(self, sheet_name: str) -> bool:
        return self.try_get_sheet_id(sheet_name) is not None

    def create_sheet(self, sheet_name: str, exist_ok: bool = False) -> int:
        sheet_id = self.try_get_sheet_id(sheet_name)
        if sheet_id is not None:
            if not exist_ok:
                raise ValueError(f'Sheet {sheet_name} already exists')
            return sheet_id

        # Create the sheet
        body = {
            'requests': {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }
        }

        res = self.spreadsheets.batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
        sheet_id = res['replies'][0]['addSheet']['properties']['sheetId']
        return sheet_id

    def delete_sheet(self, sheet_id: int) -> None:
        body = {
            'requests': {
                'deleteSheet': {
                    'sheetId': sheet_id
                }
            }
        }
        self.spreadsheets.batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()