from goshdb import Table, Db, authenticate
import pytest

from goshdb.test_utils.test_utils import get_test_data_dir

def test_gosh_db_integration():
    test_data_dir = get_test_data_dir(__file__)

    secret_dir = test_data_dir / 'secret'
    token_file = secret_dir / 'token.json'
    if not token_file.is_file():
        pytest.skip(f'token.json does not exist in {secret_dir}')

    spreadsheet_id = '1bofFXyy7Lz-slQ1m0-mJcNGgJKuO9MVrSuisTxgHLDA'
    sheet_name = 'integrated_test'

    creds = authenticate(secret_dir=secret_dir)

    db = Db(creds=creds, spreadsheet_id=spreadsheet_id)
    if db.has_table(sheet_name):
        db.delete_table(sheet_name)

    table = db.get_table(sheet_name, create_if_missing=True)

    table.set_string('key1', 'value1')
    assert table.get_string('key1') == 'value1'
    assert table.get_all_keys() == ['key1']
    table.delete_key('key1', raise_on_missing=True)

    table = Table(creds=creds, spreadsheet_id=spreadsheet_id, table_name=sheet_name, create_if_missing=False)

    assert table.get_all_keys() == []
    assert table.get_string('key1', raise_on_missing=False) is None
    assert table.has_key('key1') == False
    table.set_string('key1', 'value2')
    assert table.get_string('key1') == 'value2'
    table.set_string('key1', 'value3')
    assert table.get_string('key1') == 'value3'
    table.set_string('key2', 'value4')
    assert table.get_all_keys() == ['key1', 'key2']
    table.delete_key('key1')
    assert table.get_all_keys() == ['key2']
    table.set_string('key3', 'value5')
    assert table.get_all_keys() == ['key3', 'key2']  # 'key3' filled the empty row left by 'key1'
    table.delete_key('key2')
    table.delete_key('key3')
    assert table.get_all_keys() == []
    assert table.has_key('key1') is False
    table.set_string('key1', 'value5')
    table.set_string('key1', 'value6')
    assert table.get_string('key1') == 'value6'

    table.set_object('key3', {'a': 1, 'b': 2})
    assert table.get_object('key3') == {'a': 1, 'b': 2}
    table.set_object('key3', [100, 'b', [1, 2, {'a': 1}]])
    assert table.get_object('key3') == [100, 'b', [1, 2, {'a': 1}]]
    table.delete_key('key3')
    assert table.get_all_keys() == ['key1']
    table.delete_key('key1')
