# gseetsdb
Python client to key-value database based on Google Sheets

Sheet works as a table and has the following structure:
```
| key | value |
|-----|-------|
|     |       |
|     |       |
|     |       |
```

# Installation
```bash
pip install gseetsdb
```

# Configuration

#### Step 1. Select a Google account that will be used to access the spreadsheet

<details>
<summary>Details</summary>

* Though `GSheetsTable` uses only provided spreadsheet, credentials technically 
allow to read/write all the spreadsheets in the account.
* So it's recommended to use `GSheetsTable` with a special service (non-personal)
account that doesn't have critical/secret spreadsheets that might be compromised.

</details>

#### Step 2. Obtain credentials.json file with this the [instruction](https://developers.google.com/sheets/api/quickstart/python)

<details>
<summary>Details</summary>

* If you do this for the first time - take `credentials.json` and put it in `secret_dir`.
* On a first attempt to create `GSheetsTable` it'll open a browser window, ask you to sign in 
the target test account.
* Then the `token.json` file will be generated automatically and put in `secret_dir`.
* The `token.json` file will be used automatically for further access to the
target spreadsheet.
* You can use `token.json` to access the spreadsheet from another machine without completing the 
steps above

</details>

#### Step 3. Create a spreadsheet in your Google Sheets account.

<details>
<summary>Details</summary>

* You should share the spreadsheet and provide write access to the account that will be used to 
access it (see Step 1).

</details>


# Usage
```python
from gseetsdb import GSheetsTable
from pathlib import Path

# Take spreadsheet ID from your spreadsheet URL:
# https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit#gid=0
SPREADSHEET_ID = '...'
# Provide a sheet name. It should be either new sheet or existing one that follows the required structure.
SHEET_NAME = '...'  


# Create a GSheetsTable object. If you do this for the first time - it'll open a browser window (see Step 2 details)
table = GSheetsTable(
    secret_dir=Path('path/to/secret_dir'),
    spreadsheet_id=SPREADSHEET_ID,
    sheet_name=SHEET_NAME
)

# Write a key-value pair
table.set_string('city', 'London')
print(table.get_string('city'))  # London
table.set_object('person_1', {'name': 'John', 'age': 30})
print(table.get_object('person_1'))  # {'name': 'John', 'age': 30}
```
