from flask import Flask, g

from utils.api_response import error, ok


def test_ok_includes_timestamp_and_request_id():
    app = Flask(__name__)
    with app.test_request_context("/"):
        g.request_id = "rid_123"
        res = ok({"a": 1})
        payload = res.get_json()
        assert payload["code"] == 200
        assert payload["msg"] == "success"
        assert payload["data"] == {"a": 1}
        assert "timestamp" in payload
        assert payload["request_id"] == "rid_123"


def test_error_includes_timestamp_and_request_id():
    app = Flask(__name__)
    with app.test_request_context("/"):
        g.request_id = "rid_456"
        res = error("bad", code=400)
        payload = res.get_json()
        assert payload["code"] == 400
        assert payload["msg"] == "bad"
        assert "timestamp" in payload
        assert payload["request_id"] == "rid_456"


def test_response_has_required_fields():
    app = Flask(__name__)
    with app.test_request_context("/"):
        for res in [ok({"x": 1}), error("fail", code=422)]:
            payload = res.get_json()
            assert "code" in payload
            assert "msg" in payload
            assert "timestamp" in payload
