"""Tests for run manifest generation and serialisation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.manifests import RunManifest, load_manifest
from app.core.exceptions import ManifestError


class TestRunManifest:
    def test_creation(self) -> None:
        m = RunManifest(run_id="test-run-001")
        assert m.run_id == "test-run-001"
        assert m.status == "running"
        assert m.started_at is not None

    def test_finish(self) -> None:
        m = RunManifest(run_id="test-run")
        m.finish("success")
        assert m.status == "success"
        assert m.finished_at is not None

    def test_record_input(self, tmp_path: Path) -> None:
        m = RunManifest(run_id="r1")
        p = tmp_path / "data.h5ad"
        p.touch()
        m.record_input(p, file_hash="abc123")
        assert any(e["path"] == str(p) for e in m.input_files)
        assert m.input_files[0]["sha256"] == "abc123"

    def test_record_output(self, tmp_path: Path) -> None:
        m = RunManifest(run_id="r1")
        p = tmp_path / "results.h5ad"
        m.record_output(p, description="Main results")
        assert m.output_files[0]["description"] == "Main results"

    def test_set_parameters(self) -> None:
        m = RunManifest(run_id="r1")
        m.set_parameters({"device": "cpu", "epochs": 100})
        assert m.parameters["device"] == "cpu"

    def test_to_dict(self) -> None:
        m = RunManifest(run_id="r1", config={"key": "value"})
        d = m.to_dict()
        assert d["run_id"] == "r1"
        assert d["config"] == {"key": "value"}
        assert "environment" in d

    def test_environment_contains_python_version(self) -> None:
        m = RunManifest(run_id="r1")
        assert "python_version" in m.environment

    def test_save_and_load(self, tmp_path: Path) -> None:
        m = RunManifest(run_id="persist-test")
        m.finish("success")
        m.set_parameters({"batch_size": 2500})
        path = m.save(tmp_path)
        assert path.exists()

        loaded = load_manifest(path)
        assert loaded["run_id"] == "persist-test"
        assert loaded["status"] == "success"
        assert loaded["parameters"]["batch_size"] == 2500

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        m = RunManifest(run_id="r2")
        nested = tmp_path / "deep" / "nested" / "dir"
        path = m.save(nested)
        assert path.exists()

    def test_json_content_is_valid(self, tmp_path: Path) -> None:
        m = RunManifest(run_id="json-test")
        path = m.save(tmp_path)
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)


class TestLoadManifest:
    def test_load_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ManifestError):
            load_manifest(tmp_path / "does_not_exist.json")

    def test_load_valid(self, tmp_path: Path) -> None:
        data = {"run_id": "x", "status": "success"}
        p = tmp_path / "manifest.json"
        with open(p, "w") as f:
            json.dump(data, f)
        loaded = load_manifest(p)
        assert loaded["run_id"] == "x"
