"""End-to-end test for the reference plugin (OpenSpec add-reference-plugin).

Installs `examples/plugins/iterabledata-example` into a throwaway directory
the way pip would (package + dist-info with entry_points.txt) and verifies,
in a subprocess with that directory on sys.path, that the plugin is
discovered and usable through the public open_iterable() API with no core
library changes. Fully offline: no pip build step required.
"""

import json
import os
import shutil
import subprocess
import sys
import textwrap

import pytest

PLUGIN_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "plugins", "iterabledata-example"
)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _simulate_install(site_dir):
    """Copy the plugin package and emit pip-style dist-info metadata."""
    pkg_src = os.path.join(PLUGIN_ROOT, "src", "iterabledata_example")
    shutil.copytree(pkg_src, os.path.join(site_dir, "iterabledata_example"))
    dist_info = os.path.join(site_dir, "iterabledata_example-0.1.0.dist-info")
    os.makedirs(dist_info)
    with open(os.path.join(dist_info, "METADATA"), "w") as f:
        f.write("Metadata-Version: 2.1\nName: iterabledata-example\nVersion: 0.1.0\n")
    with open(os.path.join(dist_info, "entry_points.txt"), "w") as f:
        f.write("[iterabledata.formats]\njournal = iterabledata_example.journal:JournalIterable\n")
    with open(os.path.join(dist_info, "RECORD"), "w") as f:
        f.write("")


def _run_child(site_dir, workdir):
    script = textwrap.dedent(
        """
        import json, os, sys
        workdir = sys.argv[1]
        from iterable import open_iterable

        path = os.path.join(workdir, "app.journal")
        with open_iterable(path, mode="w", iterableargs={"format": "journal"}) as target:
            target.write({"level": "info", "msg": "started"})
            target.write_bulk([{"level": "warn", "msg": "slow", "elapsed_ms": 812}])

        with open(path, encoding="utf-8") as f:
            raw = f.read()

        with open_iterable(path, iterableargs={"format": "journal"}) as source:
            rows = list(source)
        print(json.dumps({"raw": raw, "rows": rows}))
        """
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([site_dir, REPO_ROOT])
    result = subprocess.run(
        [sys.executable, "-c", script, workdir],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    return result


@pytest.mark.skipif(not os.path.isdir(PLUGIN_ROOT), reason="reference plugin not present")
class TestReferencePlugin:
    def test_discover_and_roundtrip(self, tmp_path):
        site_dir = tmp_path / "site"
        site_dir.mkdir()
        _simulate_install(str(site_dir))
        result = _run_child(str(site_dir), str(tmp_path))
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["raw"] == "level=info;msg=started\nlevel=warn;msg=slow;elapsed_ms=812\n"
        assert payload["rows"] == [
            {"level": "info", "msg": "started"},
            {"level": "warn", "msg": "slow", "elapsed_ms": "812"},
        ]

    def test_plugin_metadata_visible(self, tmp_path):
        site_dir = tmp_path / "site"
        site_dir.mkdir()
        _simulate_install(str(site_dir))
        script = (
            "from iterable.plugins import get_plugin_registry, discover_plugins\n"
            "discover_plugins()\n"
            "registry = get_plugin_registry()\n"
            "assert 'journal' in registry._formats, registry._formats\n"
            "print('journal registered')\n"
        )
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(site_dir), REPO_ROOT])
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, timeout=60)
        assert result.returncode == 0, result.stderr
        assert "journal registered" in result.stdout
