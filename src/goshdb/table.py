from typing import Optional
import json
from google.oauth2.credentials import Credentials

from goshdb.api_wrap.sheet import Sheet
from goshdb.api_wrap.spreadsheet import Spreadsheet


class Table:
    def __init__(self, creds: Credentials, spreadsheet_id: str, table_name: str, create_if_missing: bool = True):
        """
        Class that represents a table. Table is one sheet in the spreadsheet.
        See README.md for more details.

        :param creds: Authenticated credentials object that will be used to access the Google Sheets API.
        :param spreadsheet_id: ID of the target spreadsheet.
        :param table_name: Name of the sheet that will be used as a table.
        """
        self.keys_cache: list = []
        self.sheet = self.__prepare_sheet(creds=creds,
                                          spreadsheet_id=spreadsheet_id,
                                          sheet_name=table_name,
                                          create_if_missing=create_if_missing)

    def has_key(self, key: str) -> bool:
        row_number = self.__try_get_key_row_number(key)
        return row_number is not None

    def get_string(self, key: str, raise_on_missing: bool = True) -> Optional[str]:
        # Try read using cached keys first -- it reduces the number of requests to Google Sheets
        #   and speeds up the read in case of long keys list
        row_number = self.__try_get_key_row_number(key, refresh_cache=False)
        if row_number is not None:
            # Check if key is still there, as it might have been deleted
            kv_array = self.sheet.get_multiple_values(f'A{row_number}:B{row_number}')
            # If `kv_array` is empty -- key was deleted, we will refresh cache and try again
            if len(kv_array) > 0:
                assert len(kv_array) == 1, f'Expected 1 row, but got {len(kv_array)}'
                assert len(kv_array[0]) == 2, f'Expected 2 columns, but got {len(kv_array[0])}'
                actual_key = kv_array[0][0]
                if actual_key == key:
                    return kv_array[0][1]

        # If key was not found in cache, or it was found but then deleted, we refresh cache and try again
        row_number = self.__try_get_key_row_number(key)
        if row_number is None:
            if raise_on_missing:
                raise ValueError(f'Key {key} not found')
            return None
        return self.sheet.get_value(f'B{row_number}')

    def set_string(self, key: str, value: str) -> None:
        assert key != '', f'Key should not be empty as Google Sheets cannot distinguish between empty ' \
                          f'string and empty cell value'
        assert type(value) == str, f'value should be of type str, but got: {type(value)}. ' \
                                   f'Use `set_object` for other types'
        assert type(key) == str, f'key should be of type str, but got: {type(key)}'
        row_number = self.__try_get_key_row_number(key)

        # Try to fill vacant rows first
        if row_number is None:
            # We don't refresh cache as it was already refreshed in __try_get_key_row_number
            row_number = self.__try_get_vacant_row_number(refresh_cache=False)
            if row_number is not None:
                self.sheet.set_value(f'A{row_number}', key)

        if row_number is None:
            # Add the new row
            self.sheet.append_row([key, value])
        else:
            self.sheet.set_value(f'B{row_number}', value)

    def delete_key(self, key: str, raise_on_missing: bool = True) -> None:
        row_number = self.__try_get_key_row_number(key)
        if row_number is None:
            if raise_on_missing:
                raise ValueError(f'Key {key} not found')
            return
        # We use rows emptying instead of deletion so that concurrent clients won't get in collision
        #   when Alice reads the row number corresponding to key, then Bob deletes above row, and then
        #   Alice reads wrong cell by previously read row number
        self.sheet.set_multiple_values(f'A{row_number}:B{row_number}', [['', '']])

    def get_all_keys(self) -> list[str]:
        self.__refresh_keys_cache()
        return [k for k in self.keys_cache if k is not None]

    def get_object(self, key: str) -> object:
        value = self.get_string(key)
        result = json.loads(value)
        return result

    def set_object(self, key: str, obj: object) -> None:
        value = json.dumps(obj)
        self.set_string(key, value)

    @staticmethod
    def __prepare_sheet(creds: Credentials,
                        spreadsheet_id: str,
                        sheet_name: str,
                        create_if_missing: bool) -> Sheet:
        spreadsheet = Spreadsheet(creds=creds, spreadsheet_id=spreadsheet_id)
        is_new_sheet = not spreadsheet.has_sheet(sheet_name)
        if is_new_sheet and (not create_if_missing):
            raise ValueError(f'Sheet {sheet_name} does not exist')

        sheet_id = spreadsheet.create_sheet(sheet_name, exist_ok=True)
        sheet = Sheet(creds=creds,
                      spreadsheet_id=spreadsheet_id,
                      sheet_id=sheet_id,
                      sheet_name=sheet_name)

        header = ['key', 'value']
        if is_new_sheet:
            # Set the header
            sheet.delete_columns('C', 'Z')
            sheet.append_row(header)
        else:
            actual_header_raw = sheet.get_multiple_values('A1:Z1')
            # We allow extra columns after required header columns
            actual_header = actual_header_raw[0][:len(header)]
            assert actual_header == header, f'Expected header to be {header}, but got: {actual_header}'
        return sheet

    @staticmethod
    def __key_index_to_row_number(key_index: int) -> int:
        # We add +1 because first row is the header, and +1 more because indices start from 0 while rows start from 1
        return key_index + 2

    def __refresh_keys_cache(self) -> None:
        keys_raw = self.sheet.get_multiple_values('A2:A')
        self.keys_cache = [kr[0] if len(kr) > 0 else None for kr in keys_raw]

    def __try_get_key_row_number(self, key: str, refresh_cache: bool = True) -> Optional[int]:
        if refresh_cache:
            self.__refresh_keys_cache()
        matched_key_indices = [i for i, k in enumerate(self.keys_cache) if (k is not None) and k == key]
        if len(matched_key_indices) == 0:
            return None
        elif len(matched_key_indices) == 1:
            return self.__key_index_to_row_number(matched_key_indices[0])
        else:
            raise ValueError(f'Found multiple occurrences of key {key}, indices: {matched_key_indices}')

    def __try_get_vacant_row_number(self, refresh_cache: bool = True) -> Optional[int]:
        if refresh_cache:
            self.__refresh_keys_cache()
        vacant_indices = [i for i, k in enumerate(self.keys_cache) if k is None]
        if len(vacant_indices) == 0:
            return None
        else:
            return self.__key_index_to_row_number(vacant_indices[0])
