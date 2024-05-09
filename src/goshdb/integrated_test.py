from pathlib import Path
from goshdb.table import Table


def test_gosh_db_integration(secret_dir: Path, spreadsheet_id: str, sheet_name: str):
    """
    The test is put here but not in test folder because it requires a real Google Sheets account.
    :param sheet_name: Name of a sheet that either don't exist or exist thou contains header only
    """
    table = Table(secret_dir=secret_dir, spreadsheet_id=spreadsheet_id, sheet_name=sheet_name)

    table.set_string('key1', 'value1')
    assert table.get_string('key1') == 'value1'
    assert table.get_all_keys() == ['key1']
    table.delete_key('key1', raise_on_missing=True)
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

    print('test_gosh_db_integration passed')
