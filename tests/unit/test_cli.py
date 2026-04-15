"""Tests para F7 — CLI con subcomandos."""
from __future__ import annotations
import pytest

from oraculo.cli.main import create_parser, run_cli


class TestCreateParser:
    def test_parser_created(self):
        parser = create_parser()
        assert parser.prog == "oraculo"

    def test_parser_has_subcommands(self):
        parser = create_parser()
        actions = [a for a in parser._subparsers._actions
                   if hasattr(a, '_parser_class')]
        assert len(actions) > 0


class TestCLIQuery:
    def test_query_returns_0(self, capsys):
        rc = run_cli(["query", "buscar algo"])
        assert rc == 0
        out = capsys.readouterr().out
        data = __import__("json").loads(out)
        assert data["command"] == "query"
        assert data["text"] == "buscar algo"

    def test_query_with_limit(self, capsys):
        rc = run_cli(["query", "test", "--limit", "5"])
        assert rc == 0
        out = capsys.readouterr().out
        data = __import__("json").loads(out)
        assert data["limit"] == 5

    def test_query_with_profile(self, capsys):
        rc = run_cli(["--profile", "banking", "query", "test"])
        assert rc == 0
        out = capsys.readouterr().out
        data = __import__("json").loads(out)
        assert data["profile"] == "banking"


class TestCLIIndex:
    def test_index_single_path(self, capsys):
        rc = run_cli(["index", "src/main.py"])
        assert rc == 0
        out = capsys.readouterr().out
        data = __import__("json").loads(out)
        assert data["command"] == "index"
        assert "src/main.py" in data["paths"]

    def test_index_multiple_paths(self, capsys):
        rc = run_cli(["index", "a.py", "b.py", "c.py"])
        assert rc == 0
        out = capsys.readouterr().out
        data = __import__("json").loads(out)
        assert len(data["paths"]) == 3

    def test_index_force(self, capsys):
        rc = run_cli(["index", "x.py", "--force"])
        assert rc == 0
        out = capsys.readouterr().out
        data = __import__("json").loads(out)
        assert data["force"] is True


class TestCLIProfile:
    def test_profile_list(self, capsys):
        rc = run_cli(["profile", "list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "basic" in out
        assert "enterprise" in out
        assert "banking" in out

    def test_profile_show(self, capsys):
        rc = run_cli(["--profile", "banking", "profile", "show"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "banking" in out

    def test_profile_switch_no_name(self, capsys):
        rc = run_cli(["profile", "switch"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "--name requerido" in out

    def test_profile_switch_with_name(self, capsys):
        rc = run_cli(["profile", "switch", "--name", "banking"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "banking" in out


class TestCLIStatus:
    def test_status(self, capsys):
        rc = run_cli(["status"])
        assert rc == 0
        out = capsys.readouterr().out
        data = __import__("json").loads(out)
        assert data["command"] == "status"


class TestCLIServe:
    def test_serve(self, capsys):
        rc = run_cli(["serve"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "127.0.0.1" in out
        assert "9741" in out

    def test_serve_custom_port(self, capsys):
        rc = run_cli(["serve", "--port", "8080"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "8080" in out


class TestCLINoCommand:
    def test_no_command_returns_0(self):
        rc = run_cli([])
        assert rc == 0

    def test_verbose(self, capsys):
        rc = run_cli(["-v", "status"])
        assert rc == 0
