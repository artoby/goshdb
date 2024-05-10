from pathlib import Path


def get_test_data_dir(test_module_file: str) -> Path:
    cur_dir = Path(test_module_file).parent
    submodule_name = Path(test_module_file).name.split('.')[0]

    return cur_dir / 'data' / submodule_name
