from pathlib import Path
from gsheetsdb.db import GSheetsDB


def test_gsheets_db_integration(secret_dir: Path, spreadsheet_id: str, sheet_name: str):
    """
    The test is put here but not in test folder because it requires a real Google Sheets account.
    :param sheet_name: Name of a sheet that either don't exist or exist thou contains header only
    """
    db = GSheetsDB(secret_dir=secret_dir, spreadsheet_id=spreadsheet_id, sheet_name=sheet_name)

    db.set_string('key1', 'value1')
    assert db.get_string('key1') == 'value1'
    assert db.get_all_keys() == ['key1']
    db.delete_key('key1', raise_on_missing=True)
    assert db.get_all_keys() == []
    assert db.get_string('key1', raise_on_missing=False) is None
    assert db.has_key('key1') == False
    db.set_string('key1', 'value2')
    assert db.get_string('key1') == 'value2'
    db.set_string('key1', 'value3')
    assert db.get_string('key1') == 'value3'
    db.set_string('key2', 'value4')
    assert db.get_all_keys() == ['key1', 'key2']
    db.delete_key('key1')
    assert db.get_all_keys() == ['key2']
    db.set_string('key3', 'value5')
    assert db.get_all_keys() == ['key3', 'key2']  # 'key3' filled the empty row left by 'key1'
    db.delete_key('key2')
    db.delete_key('key3')
    assert db.get_all_keys() == []
    assert db.has_key('key1') == False
    db.set_string('key1', 'value5')
    db.set_string('key1', 'value6')
    assert db.get_string('key1') == 'value6'

    db.set_object('key3', {'a': 1, 'b': 2})
    assert db.get_object('key3') == {'a': 1, 'b': 2}
    db.set_object('key3', [100, 'b', [1, 2, {'a': 1}]])
    assert db.get_object('key3') == [100, 'b', [1, 2, {'a': 1}]]
    db.delete_key('key3')
    assert db.get_all_keys() == ['key1']
    db.delete_key('key1')

    print('test_gsheets_db_integration passed')
