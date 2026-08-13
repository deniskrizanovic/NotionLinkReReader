import pytest

from notionlinkrereader.config import DEFAULT_DATABASE_ID, ConfigError, load_config

FULL_ENV = {
    "NOTION_TOKEN": "secret",
    "NOTION_DATABASE_ID": "db123",
    "GMAIL_ADDRESS": "me@gmail.com",
    "GMAIL_APP_PASSWORD": "app-pass",
    "EMAIL_TO": "me@gmail.com",
}


def test_load_config_full():
    config = load_config(FULL_ENV)
    assert config.notion_token == "secret"
    assert config.notion_database_id == "db123"
    assert config.gmail_address == "me@gmail.com"


def test_database_id_defaults_when_absent():
    env = {k: v for k, v in FULL_ENV.items() if k != "NOTION_DATABASE_ID"}
    config = load_config(env)
    assert config.notion_database_id == DEFAULT_DATABASE_ID


@pytest.mark.parametrize(
    "missing", ["NOTION_TOKEN", "GMAIL_ADDRESS", "GMAIL_APP_PASSWORD", "EMAIL_TO"]
)
def test_missing_required_var_raises_naming_it(missing):
    env = {k: v for k, v in FULL_ENV.items() if k != missing}
    with pytest.raises(ConfigError) as excinfo:
        load_config(env)
    assert missing in str(excinfo.value)
