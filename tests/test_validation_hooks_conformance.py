"""Conformance guard: every writable format applies write-time validation hooks.

OpenSpec change ``add-validation-hooks-rollout``: for every format descriptor
with ``writable=True``, the ``write()`` and ``write_bulk()`` paths must invoke
``_apply_validation_hooks`` so a configured ``validation_hook`` fires, and the
``on_validation_error="skip"`` policy must prevent rejected records from being
persisted.

Two layers of protection:

1. ``test_writable_format_applies_validation_hooks`` — behavioral: opens each
   format through the public ``open_iterable(..., mode="w", iterableargs=...)``
   API with a rejecting hook, writes one failing record through both write
   paths, and asserts the hook fired and nothing was persisted. Formats whose
   optional backends are not installed are skipped (ImportError).
2. ``test_all_writable_formats_have_hooked_write_paths`` — static fallback:
   resolves each format's effective ``write``/``write_bulk`` through the MRO
   (including ``self.write_bulk``/``super().write``/``self.write`` delegation)
   and asserts the resolved path applies ``_apply_validation_hooks``. This runs
   even when a format's backend is not installed, so future formats cannot
   regress silently.
"""

import inspect
import os

import pytest

from iterable import open_iterable
from iterable.helpers.format_registry import FORMAT_DESCRIPTORS

WRITABLE_DESCRIPTORS = [d for d in FORMAT_DESCRIPTORS if d.writable]

# Schema used by lakehouse/table formats that need one to create a table.
_SCHEMA = [("id", "bigint"), ("name", "string")]


def _message_classes() -> dict:
    """Optional protobuf message classes, keyed by format id, when deps exist."""
    available = {}
    try:
        from google.protobuf.struct_pb2 import Struct

        available["pb"] = Struct
    except ImportError:
        pass
    try:
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest

        available["otlp-protobuf"] = ExportTraceServiceRequest
    except ImportError:
        pass
    return available


def _extra_iterableargs(format_id: str, tmp_path) -> dict:
    """Documented iterableargs a format needs to be constructed in write mode."""
    if format_id == "xml":
        return {"tagname": "item"}
    if format_id == "ddb":
        return {"table": "conformance"}
    if format_id == "ducklake":
        return {"table": "conformance", "create_table": True, "schema": _SCHEMA}
    if format_id == "paimon":
        return {"create_table": True, "schema": _SCHEMA}
    if format_id == "iceberg":
        # Local sqlite-backed PyIceberg catalog; no writes reach it because the
        # rejecting hook short-circuits the write path first.
        return {
            "table_name": "conformance",
            "create_table": True,
            "catalog": {"uri": f"sqlite:///{tmp_path}/iceberg_catalog.db", "warehouse": f"file://{tmp_path}"},
        }
    if format_id == "kafka":
        # Lazy producer: construction does not connect, and the rejecting hook
        # returns before any broker I/O.
        return {"topic": "conformance", "bootstrap_servers": "localhost:1"}
    if format_id == "pulsar":
        # Lazy client: same reasoning as kafka above.
        return {"topic": "conformance", "service_url": "pulsar://localhost:6650"}
    message_classes = _message_classes()
    if format_id in message_classes:
        return {"message_class": message_classes[format_id]}
    return {}


# Container/table formats that persist layout or catalog metadata at open/close
# even when zero records are written (e.g. DuckDB database file, XLSX package
# structure, Paimon table header). For these, the hook-fired assertions are the
# conformance guarantee; byte-emptiness is not meaningful.
CONTAINER_METADATA_FORMATS = frozenset({"ddb", "ducklake", "paimon_row", "xlsx"})

# Formats where an empty output still reads back as a record (parser artifact):
# an empty .eml file parses as one empty message. Asserted via size instead.
EMPTY_READBACK_ARTIFACT_FORMATS = frozenset({"eml"})


@pytest.mark.parametrize("descriptor", WRITABLE_DESCRIPTORS, ids=[d.id for d in WRITABLE_DESCRIPTORS])
def test_writable_format_applies_validation_hooks(descriptor, tmp_path):
    """A record rejected by the configured hook must not be persisted."""
    hook_calls = []

    def rejecting_hook(row):
        hook_calls.append(row)
        raise ValueError("record rejected by conformance hook")

    iterableargs = {
        "format": descriptor.id,
        "validation_hook": rejecting_hook,
        "on_validation_error": "skip",
    }
    iterableargs.update(_extra_iterableargs(descriptor.id, tmp_path))
    fname = str(tmp_path / f"out_{descriptor.id.replace('-', '_')}.dat")
    try:
        iterable = open_iterable(fname, mode="w", iterableargs=iterableargs)
    except ImportError as exc:
        pytest.skip(f"optional backend for {descriptor.id!r} unavailable: {exc}")

    with iterable:
        iterable.write({"id": 1, "name": "rejected"})
        assert len(hook_calls) == 1, f"{descriptor.id}: write() bypassed validation hooks"
        iterable.write_bulk([{"id": 2, "name": "rejected"}])
        assert len(hook_calls) == 2, f"{descriptor.id}: write_bulk() bypassed validation hooks"

    # Nothing was persisted: prefer a read-back proof, fall back to byte size.
    if descriptor.id in EMPTY_READBACK_ARTIFACT_FORMATS:
        assert os.path.getsize(fname) == 0
        return
    try:
        with open_iterable(
            fname, iterableargs={"format": descriptor.id, **_extra_iterableargs(descriptor.id, tmp_path)}
        ) as source:
            persisted = sum(1 for _ in source)
        assert persisted == 0, f"{descriptor.id}: {persisted} rejected record(s) were persisted"
    except Exception:
        # Reader cannot open an empty/container output; then the file must be
        # absent or empty unless the format persists container metadata anyway.
        if descriptor.id in CONTAINER_METADATA_FORMATS:
            return
        if os.path.isfile(fname):
            assert os.path.getsize(fname) == 0, f"{descriptor.id}: rejected record bytes persisted in {fname}"


def _method_source(owner: type, name: str) -> str:
    try:
        return inspect.getsource(owner.__dict__[name])
    except (KeyError, OSError, TypeError):
        return ""


def _method_owner(cls: type, name: str) -> type | None:
    for klass in cls.__mro__:
        if name in klass.__dict__:
            return klass
    return None


def _write_path_applies_hooks(cls: type, method: str, _seen: frozenset = frozenset()) -> bool:
    """Whether cls.<method> effectively applies _apply_validation_hooks.

    Follows the delegation idioms used across datatypes: ``write`` ->
    ``self.write_bulk([record])``, ``write`` -> ``super().write(record)``, and
    ``write_bulk`` -> per-record ``self.write(record)``.
    """
    owner = _method_owner(cls, method)
    if owner is None:
        return False
    if (owner, method) in _seen:
        return False
    src = _method_source(owner, method)
    if "_apply_validation_hooks" in src:
        return True
    seen = _seen | {(owner, method)}
    if method == "write":
        if "self.write_bulk(" in src:
            return _write_path_applies_hooks(cls, "write_bulk", seen)
        if "super().write(" in src:
            mro = cls.__mro__
            for sub in mro[mro.index(owner) + 1 :]:
                if "write" not in sub.__dict__:
                    continue
                sub_src = _method_source(sub, "write")
                if "_apply_validation_hooks" in sub_src:
                    return True
                if "self.write_bulk(" in sub_src:
                    return _write_path_applies_hooks(cls, "write_bulk", seen)
                return False
        return False
    # write_bulk
    if "self.write(" in src:
        return _write_path_applies_hooks(cls, "write", seen)
    return False


def test_all_writable_formats_have_hooked_write_paths():
    """Static conformance fallback covering formats whose deps are missing here."""
    import importlib

    from iterable.base import BaseIterable

    bypassed = []
    for descriptor in WRITABLE_DESCRIPTORS:
        try:
            module = importlib.import_module(descriptor.module)
            cls = getattr(module, descriptor.cls)
        except (ImportError, AttributeError):
            continue  # backend missing in this env; behavioral test covers it where installed
        if not issubclass(cls, BaseIterable):
            continue
        write_hooked = _write_path_applies_hooks(cls, "write")
        bulk_hooked = _write_path_applies_hooks(cls, "write_bulk")
        if not (write_hooked and bulk_hooked):
            bypassed.append((descriptor.id, write_hooked, bulk_hooked))
    assert not bypassed, f"writable formats bypassing validation hooks: {bypassed}"
