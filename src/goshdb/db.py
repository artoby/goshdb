from google.oauth2.credentials import Credentials

from goshdb.api_wrap.spreadsheet import Spreadsheet
from goshdb.table import Table


class Db:
    def __init__(self, creds: Credentials, spreadsheet_id: str):
        """
        Class that represents a database. Database is one spreadsheet.
        See README.md for more details.

        :param creds: Authenticated credentials object that will be used to access the Google Sheets API.
        :param spreadsheet_id: ID of the target spreadsheet.
        """
        self.spreadsheet = Spreadsheet(creds=creds, spreadsheet_id=spreadsheet_id)

    def get_table(self, table_name: str, create_if_missing: bool = False) -> Table:
        return Table(creds=self.spreadsheet.creds,
                     spreadsheet_id=self.spreadsheet.spreadsheet_id,
                     table_name=table_name,
                     create_if_missing=create_if_missing)

    def has_table(self, table_name: str) -> bool:
        return self.spreadsheet.has_sheet(sheet_name=table_name)

    def create_table(self, table_name: str, exist_ok: bool = False) -> Table:
        if (not exist_ok) and self.has_table(table_name):
            raise ValueError(f'Sheet {table_name} already exists')
        return self.get_table(table_name, create_if_missing=True)

    def delete_table(self, table_name: str) -> None:
        sheet_id = self.spreadsheet.try_get_sheet_id(sheet_name=table_name)
        if sheet_id is None:
            raise ValueError(f'Sheet {table_name} does not exist')
        self.spreadsheet.delete_sheet(sheet_id)
