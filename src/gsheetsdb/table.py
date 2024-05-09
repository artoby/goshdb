from pathlib import Path
from typing import Optional
import json

from gsheetsdb.sheet import GSheetsSheet


class GSheetsTable:
    def __init__(self, secret_dir: Path, spreadsheet_id: str, sheet_name: str):
        """
        Class that represents a table. See README.md for more details.

        :param secret_dir: Path to the directory containing credentials.json or token.json.
        :param spreadsheet_id: ID of the target spreadsheet.
        :param sheet_name: Name of the sheet that will be used as a table.
        """
        self.sheet = GSheetsSheet(secret_dir=secret_dir,
                                  spreadsheet_id=spreadsheet_id,
                                  sheet_name=sheet_name,
                                  header=['key', 'value'])

    def has_key(self, key: str) -> bool:
        row_number = self.__try_get_key_row_number(key)
        return row_number is not None

    def get_string(self, key: str, raise_on_missing: bool = True) -> Optional[str]:
        row_number = self.__try_get_key_row_number(key)
        if row_number is None:
            if raise_on_missing:
                raise ValueError(f'Key {key} not found')
            return None
        return self.sheet.get_value(f'B{row_number}')

    def set_string(self, key: str, value: str) -> None:
        assert key != '', f'Key should not be empty as Google Sheets cannot distinguish between empty string and empty cell value'
        assert type(
            value) == str, f'value should be of type str, but got: {type(value)}. Use `set_oject` for other types'
        assert type(key) == str, f'key should be of type str, but got: {type(key)}'
        row_number = self.__try_get_key_row_number(key)

        # Try to fill vacant rows first
        if row_number is None:
            row_number = self.__try_get_vacant_row_number()
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
        # We use rows emptying instead of deletion so that concurrent clients wont get in collision
        #   when Alice reads the row number corresponding to key, then Bob deletes above row, and then
        #   Alice reads wrong cell by previously read row number
        self.sheet.set_multiple_values(f'A{row_number}:B{row_number}', [['', '']])

    def get_all_keys(self) -> list[str]:
        values = self.sheet.get_multiple_values('A2:A')
        return [v[0] for v in values if len(v) > 0]

    def get_object(self, key: str) -> object:
        value = self.get_string(key)
        result = json.loads(value)
        return result

    def set_object(self, key: str, obj: object) -> None:
        value = json.dumps(obj)
        self.set_string(key, value)

    @staticmethod
    def __key_index_to_row_number(key_index: int) -> int:
        # We add +1 because first row is the header, and +1 more because indices start from 0 while rows start from 1
        return key_index + 2

    def __try_get_key_row_number(self, key: str) -> Optional[int]:
        values = self.sheet.get_multiple_values('A2:A')
        indices = [i for i, v in enumerate(values) if len(v) > 0 and v[0] == key]
        if len(indices) == 0:
            return None
        elif len(indices) == 1:
            return self.__key_index_to_row_number(indices[0])
        else:
            raise ValueError(f'Found multiple occurances of key {key}, indices: {indices}')

    def __try_get_vacant_row_number(self) -> Optional[int]:
        values = self.sheet.get_multiple_values('A2:A')
        indices = [i for i, v in enumerate(values) if len(v) == 0]
        if len(indices) == 0:
            return None
        else:
            return self.__key_index_to_row_number(indices[0])
