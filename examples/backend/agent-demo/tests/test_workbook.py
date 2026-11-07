"""验证公开练习输入与 HTTP 工具客户端；运行 python -m pytest -q。"""

import asyncio
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from demo.tool_api import app as tool_app
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location(
    "http_tools", ROOT / "scripts/backend/call_http_tools.py"
)
http_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(http_tools)


@pytest.mark.parametrize("name", ["normal", "partial", "deadline"])
def test_tool_inputs(name):
    plan = http_tools.Plan.model_validate_json(
        (ROOT / f"inputs/backend/tools-{name}.json").read_text()
    )
    report = asyncio.run(
        http_tools.run_plan(plan, transport=httpx.ASGITransport(app=tool_app))
    )
    if name == "deadline":
        assert report["status"] == "deadline_exceeded"
    elif name == "partial":
        assert [row["status"] for row in report["results"]] == [
            "ok",
            "timeout",
            "http_error",
        ]
        assert report["results"][2]["http_status"] == 503
    else:
        assert [row["result"] for row in report["results"]] == [
            {"words": 6},
            {"characters": 35},
        ]


def test_tool_plan_does_not_allow_arbitrary_paths_or_duplicate_names():
    raw = json.loads((ROOT / "inputs/backend/tools-normal.json").read_text())
    raw["calls"][0]["path"] = "http://internal.example/admin"
    with pytest.raises(ValidationError):
        http_tools.Plan.model_validate(raw)
    raw = json.loads((ROOT / "inputs/backend/tools-normal.json").read_text())
    raw["calls"][1]["name"] = raw["calls"][0]["name"]
    with pytest.raises(ValidationError):
        http_tools.Plan.model_validate(raw)


def test_network_error_is_an_explicit_result():
    plan = http_tools.Plan.model_validate_json(
        (ROOT / "inputs/backend/tools-normal.json").read_text()
    )

    def offline(request):
        raise httpx.ConnectError("controlled connection failure", request=request)

    report = asyncio.run(
        http_tools.run_plan(plan, transport=httpx.MockTransport(offline))
    )
    assert [row["status"] for row in report["results"]] == [
        "network_error",
        "network_error",
    ]


def test_unexpected_response_error_is_not_silenced():
    plan = http_tools.Plan.model_validate_json(
        (ROOT / "inputs/backend/tools-normal.json").read_text()
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, text="not-json", request=request)
    )
    with pytest.raises(ExceptionGroup):
        asyncio.run(http_tools.run_plan(plan, transport=transport))


def test_public_workbook_cli_and_persisted_evidence(tmp_path):
    output = tmp_path / "lab"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/backend/run_agent_example.py"),
            "--output-dir",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((output / "report.json").read_text())
    assert report["totals"] == {"runs": 6, "messages": 8}
    assert report["cases"]["normal"]["input_characters"] == 140
    assert report["cases"]["normal"]["input_words"] == 14
    assert report["cases"]["normal"]["attachment_bytes"] == 226
    assert report["cases"]["retry"]["attempt"] == 2
    assert report["cases"]["expired_worker"]["late_write"] == "rejected"
    assert report["cases"]["logout"]["next_request_status_code"] == 401
    assert (
        'event: done\ndata: {"status": "succeeded"'
        in (output / "normal-events.sse").read_text()
    )
    assert "access_token" not in (output / "report.json").read_text()
