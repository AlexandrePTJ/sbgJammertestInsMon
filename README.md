# SBG Systems - INS Monitoring system

Quick'n'Dirty Dashboard created fo follow INS data during Jammertest 2025

## Install

Ensure to have python installed and available in path.

```sh
# Create virtual env
python -m venv venv

# Enter virtual env
(windows) .\venv\Scripts\activate
(linux)   source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```


## Configure

Create `config.json` from `config_template.json`
Ensure each `id` field is unique upon all configured INS.

`config.json` expects an array of INS configuration objects. Available fields are :

- `id` **mandatory** Unique ID for the system
- `name` **mandatory** Display name
- `connection_type` **mandatory**
    - `ethernet` Connect to INS through INS Rest API
    - `fake` Use local file at `<project source>/app/monitoring/collectors/fake_data.json` to send data
- `ip_address` **madatory** if `connection_type` is set to `ethernet`
- `color` Color as hex code (for map display)


## Run

```sh
# Enter virtual env (if not already in)
(windows) .\venv\Scripts\activate
(linux)   source venv/bin/activate

# Install dependencies
python app.py
```

Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
