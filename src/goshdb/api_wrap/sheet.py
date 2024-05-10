from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from openpyxl.utils.cell import column_index_from_string


class Sheet:
    def __init__(self,
                 creds: Credentials,
                 spreadsheet_id: str,
                 sheet_id: int,
                 sheet_name: str):
        # Technically sheet_id=None means use first sheet (i.e. sheet_id=0), though it's an often
        #   root cause of errors when we by mistake pass None instead of sheet_id and modify the first
        #   sheet instead of the target one. If you want to use the first sheet, pass sheet_id=0 explicitly.
        assert sheet_id is not None, 'sheet_id should not be None'

        self.creds = creds
        self.spreadsheet_id = spreadsheet_id
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name

        self.service = build("sheets", "v4", credentials=self.creds)
        self.spreadsheets = self.service.spreadsheets()

    def append_row(self, values: list[str]) -> None:
        body = {
            'values': [values]
        }
        self.spreadsheets.values().append(spreadsheetId=self.spreadsheet_id,
                                          range=f'{self.sheet_name}!A:A',
                                          valueInputOption='RAW',
                                          body=body).execute()

    def set_multiple_values(self, coord: str, values: list) -> None:
        assert '!' not in coord, f'coord should not contain sheet name, i.e. "!": {coord}'
        body = {
            'values': values,
        }
        self.spreadsheets \
            .values() \
            .update(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!{coord}',
                valueInputOption='RAW',
                body=body) \
            .execute()

    def set_value(self, coord: str, value: str) -> None:
        assert ':' not in coord, f'coord should reference only one cell but got: {coord}'
        self.set_multiple_values(coord, [[value]])

    def get_multiple_values(self, coord: str) -> list[list[str]]:
        assert '!' not in coord, f'coord should not contain sheet name, i.e. "!": {coord}'
        result = self.spreadsheets \
            .values() \
            .get(spreadsheetId=self.spreadsheet_id, range=f'{self.sheet_name}!{coord}') \
            .execute()
        values = result.get('values', [])
        return values

    def get_value(self, coord: str) -> str:
        values = self.get_multiple_values(coord)
        if not values:
            return ''
        assert len(values) == 1, f'For {coord} expected only one row, but got {len(values)}'
        assert len(values[0]) == 1, f'For {coord} expected only one column, but got {len(values[0])}'
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

    def delete_columns(self, start_column: str, end_column: str) -> None:
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
                            'sheetId': self.sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': start_column_index,
                            'endIndex': end_column_index + 1  # endIndex is exclusive
                        }
                    }
                }
            ]
        }
        self.spreadsheets.batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
