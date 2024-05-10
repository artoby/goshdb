# goshdb
GOogle SHeets DataBase - Python client to key-value database based on Google Sheets

Sheet works as a table and has the following look & structure:

<img src="https://github.com/artoby/goshdb/assets/6637041/cf3ba5d4-e1df-42ff-8487-3f18a27190fd" width="300">


# Use cases
- Store configuration with ability to change it on the fly
- Store data that should be shared between multiple users / machines
- Write status of a long-running process and observe it in real-time in Google Sheets
- Review data modification history in Google Sheets UI (File -> Version history -> See version history)

Features
- Simple key-value interface (get/set string/object)

Advantages
- Free storage (Google Sheets API has free quota)
- Concurrent read (Supports parallel read from multiple clients)
- No need to create a server
- User-friendly Google Sheets UI for data review & modification
- No need to install any software on the client side (only Python)
- Simple get/set methods instead of SQL queries
- No need to create a database schema (just create a new sheet)
- Data backup, synchronization, availability, and security are managed by Google Sheets

Limitations
- Not suitable for high-frequency read/write operations (Google Sheets API has read/write quota: 
300/minute per project, 60/minute per user per project)
- Not suitable for concurrent write (Google Sheets API has no locking mechanism)
- Not suitable for very large data (Google Sheets has a limit of 10 million cells per spreadsheet, 
i.e. 5 million key-value pairs
- Not suitable for high-speed data access (Google Sheets API has a delay, takes ~0.3-1 second per 
get/set operation)
- Not suitable for complex queries, types, data structures, relations, validation and indexing 
(only key-value interface)
- Not suitable for sensitive & high-security data (Google Sheets API has access to all 
spreadsheets in the account)

# Installation

```bash
pip install goshdb
```

# Configuration

See [this video](https://youtu.be/_J6Hy6KFgx4) for step-by-step instruction & demo

#### Step 1. Select a Google account that will be used to access the spreadsheet

<details>
<summary>Details</summary>

* Though `Table` uses only provided spreadsheet, credentials technically 
allow to read/write all the spreadsheets in the account.
* So it's recommended to use `Table` with a special service (non-personal)
account that doesn't have critical/secret spreadsheets that might be compromised.

</details>

#### Step 2. Create a spreadsheet in your Google Sheets account.

<details>
<summary>Details</summary>

* You should share the spreadsheet and provide write access to the account that will be used to 
access it (see Step 1).

</details>

#### Step 3. Obtain credentials.json file with this the [instruction](https://developers.google.com/sheets/api/quickstart/python)

<details>
<summary>Details</summary>

* If you do this for the first time - take `credentials.json` and put it in `secret_dir`.
* On a first attempt to create `Table` it'll open a browser window, ask you to sign in 
the target test account.
* Then the `token.json` file will be generated automatically and put in `secret_dir`.
* The `token.json` file will be used automatically for further access to the
target spreadsheet.
* You can use `token.json` to access the spreadsheet from another machine without completing the 
steps above

</details>


# Usage
```python
from goshdb import authenticate, Table
from pathlib import Path

# Take spreadsheet ID from your spreadsheet URL:
# https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit#gid=0
SPREADSHEET_ID = '...'
# Provide a sheet name. It should be either new sheet or existing one that follows the required structure.
SHEET_NAME = '...'  

# Authenticate
creds = authenticate(Path('path/to/secret_dir'))
# Create a Table object. If you do this for the first time - it'll open a browser window (see Step 3 details)
table = Table(
    creds=creds,
    spreadsheet_id=SPREADSHEET_ID,
    table_name=SHEET_NAME
)

# Write a key-value pair
table.set_string('city', 'London')
print(table.get_string('city'))  # London
table.set_object('person_1', {'name': 'John', 'age': 30})
print(table.get_object('person_1'))  # {'name': 'John', 'age': 30}
```
