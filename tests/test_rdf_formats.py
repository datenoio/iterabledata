"""Tests for TriG, N3, TriX RDF formats (rdflib)."""

import os
import tempfile

import pytest

try:
    from rdflib import ConjunctiveGraph, Graph  # noqa: F401

    HAS_RDFLIB = True
except ImportError:
    HAS_RDFLIB = False

from iterable.datatypes.n3 import N3Iterable
from iterable.datatypes.trig import TriGIterable
from iterable.datatypes.trix import TriXIterable
from iterable.helpers.detect import open_iterable


@pytest.mark.skipif(not HAS_RDFLIB, reason="rdflib not installed")
class TestTriG:
    def test_trig_id(self):
        assert TriGIterable.id() == "trig"

    def test_trig_flatonly(self):
        assert TriGIterable.is_flatonly()

    def test_trig_read_quads(self):
        content = """@prefix ex: <http://example.org/> .
        { ex:a ex:p ex:b . }"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".trig", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = TriGIterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) >= 1
            r = rows[0]
            assert "subject" in r and "predicate" in r and "object" in r and "graph" in r
        finally:
            os.unlink(path)

    def test_trig_open_iterable_detection(self):
        content = """@prefix ex: <http://example.org/> . { ex:a ex:p ex:b . }"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".trig", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            with open_iterable(path) as src:
                rows = list(src)
            assert len(rows) >= 1
        finally:
            os.unlink(path)


@pytest.mark.skipif(not HAS_RDFLIB, reason="rdflib not installed")
class TestN3:
    def test_n3_id(self):
        assert N3Iterable.id() == "n3"

    def test_n3_read_triples(self):
        content = """@prefix ex: <http://example.org/> .
        ex:a ex:p ex:b ."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".n3", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = N3Iterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) >= 1
            r = rows[0]
            assert "subject" in r and "predicate" in r and "object" in r
        finally:
            os.unlink(path)

    def test_n3_open_iterable_detection(self):
        content = """@prefix ex: <http://example.org/> . ex:a ex:p ex:b ."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".n3", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            with open_iterable(path) as src:
                rows = list(src)
            assert len(rows) >= 1
        finally:
            os.unlink(path)


@pytest.mark.skipif(not HAS_RDFLIB, reason="rdflib not installed")
class TestTriX:
    def test_trix_id(self):
        assert TriXIterable.id() == "trix"

    def test_trix_read_triples(self):
        content = """<?xml version="1.0"?>
        <TriX xmlns="http://www.w3.org/2004/03/trix/trix-1/">
        <graph><uri>http://example.org/g</uri>
        <triple><uri>http://example.org/a</uri><uri>http://example.org/p</uri><uri>http://example.org/b</uri></triple>
        </graph></TriX>"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".trix", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            it = TriXIterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) >= 1
            r = rows[0]
            assert "subject" in r and "predicate" in r and "object" in r
        finally:
            if os.path.exists(path):
                os.unlink(path)


@pytest.mark.skipif(HAS_RDFLIB, reason="only run when rdflib is not installed")
def test_trig_import_error_without_rdflib():
    """Without rdflib, TriGIterable raises ImportError with install hint."""
    with tempfile.NamedTemporaryFile(suffix=".trig", delete=False) as f:
        path = f.name
    try:
        TriGIterable(path, mode="r")
    except ImportError as e:
        assert "iterabledata[rdf]" in str(e) or "rdflib" in str(e).lower()
    finally:
        os.unlink(path)
