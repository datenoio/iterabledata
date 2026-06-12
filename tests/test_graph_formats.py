"""Tests for GraphML, GEXF, DOT formats (NetworkX)."""

import os
import tempfile

import pytest

try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from iterable.datatypes.dot import DOTIterable
from iterable.datatypes.gexf import GEXFIterable
from iterable.datatypes.graphml import GraphMLIterable
from iterable.helpers.detect import open_iterable


@pytest.mark.skipif(not HAS_NETWORKX, reason="networkx not installed")
class TestGraphML:
    def test_graphml_id(self):
        assert GraphMLIterable.id() == "graphml"

    def test_graphml_read(self):
        G = nx.path_graph(2)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".graphml", delete=False, encoding="utf-8") as f:
            path = f.name
        try:
            nx.write_graphml(G, path)
            it = GraphMLIterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) >= 1
            types = {r.get("_type") for r in rows}
            assert "node" in types or "edge" in types
        finally:
            os.unlink(path)

    def test_graphml_open_iterable_detection(self):
        G = nx.path_graph(2)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".graphml", delete=False, encoding="utf-8") as f:
            path = f.name
        try:
            nx.write_graphml(G, path)
            with open_iterable(path) as src:
                rows = list(src)
            assert len(rows) >= 1
        finally:
            os.unlink(path)


@pytest.mark.skipif(not HAS_NETWORKX, reason="networkx not installed")
class TestGEXF:
    def test_gexf_id(self):
        assert GEXFIterable.id() == "gexf"

    def test_gexf_read(self):
        G = nx.path_graph(2)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gexf", delete=False, encoding="utf-8") as f:
            path = f.name
        try:
            nx.write_gexf(G, path)
            it = GEXFIterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) >= 1
        finally:
            os.unlink(path)

    def test_gexf_open_iterable_detection(self):
        G = nx.path_graph(2)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gexf", delete=False, encoding="utf-8") as f:
            path = f.name
        try:
            nx.write_gexf(G, path)
            with open_iterable(path) as src:
                rows = list(src)
            assert len(rows) >= 1
        finally:
            os.unlink(path)


@pytest.mark.skipif(not HAS_NETWORKX, reason="networkx not installed")
class TestDOT:
    def test_dot_id(self):
        assert DOTIterable.id() == "dot"

    def test_dot_read(self):
        G = nx.path_graph(2)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dot", delete=False, encoding="utf-8") as f:
            path = f.name
        try:
            nx.nx_pydot.write_dot(G, path)
            it = DOTIterable(path, mode="r")
            rows = list(it)
            it.close()
            assert len(rows) >= 1
        except (ImportError, AttributeError):
            pytest.skip("pydot or graphviz not available for read_dot")
        finally:
            if os.path.exists(path):
                os.unlink(path)


@pytest.mark.skipif(HAS_NETWORKX, reason="only run when networkx is not installed")
def test_graphml_import_error_without_networkx():
    """Without networkx, GraphMLIterable raises ImportError with install hint."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".graphml", delete=False) as f:
        path = f.name
    try:
        with pytest.raises(ImportError) as exc_info:
            GraphMLIterable(path, mode="r")
        assert "iterabledata[graph]" in str(exc_info.value) or "networkx" in str(exc_info.value).lower()
    finally:
        os.unlink(path)
