import notionlinkrereader.__main__ as main
from notionlinkrereader.notion import LinkRecord


def test_run_reads_environment_and_drives_pipeline(monkeypatch):
    # load_config defaults to os.environ; supply every required var there.
    monkeypatch.setenv("NOTION_TOKEN", "tok")
    monkeypatch.setenv("NOTION_DATABASE_ID", "db123")
    monkeypatch.setenv("GMAIL_ADDRESS", "me@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "pw")
    monkeypatch.setenv("EMAIL_TO", "you@gmail.com")

    query_args = {}

    def fake_query(token, database_id):
        query_args["token"] = token
        query_args["database_id"] = database_id
        return [{"id": "1"}]

    sent = {}

    def fake_send(message, *, gmail_address, gmail_app_password):
        sent["to"] = message["To"]
        sent["gmail_address"] = gmail_address
        sent["gmail_app_password"] = gmail_app_password

    monkeypatch.setattr(main, "query_database", fake_query)
    monkeypatch.setattr(
        main, "select_links", lambda records: [LinkRecord(name="A")]
    )
    monkeypatch.setattr(main, "send_message", fake_send)

    main.run()

    # Config sourced from the environment, passed through to the job.
    assert query_args == {"token": "tok", "database_id": "db123"}
    assert sent["to"] == "you@gmail.com"
    assert sent["gmail_address"] == "me@gmail.com"
    assert sent["gmail_app_password"] == "pw"
