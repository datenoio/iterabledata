"""Shared helpers for related datatype implementations.

Holds conversion logic reused by several format modules (graph formats
backed by NetworkX, RDF formats backed by rdflib) so it is defined once
instead of being duplicated per module. This module must stay free of
optional third-party imports: callers pass already-parsed objects in.
"""

from __future__ import annotations

from ..types import Row


def graph_to_records(graph) -> list[Row]:
    """Convert a NetworkX graph to a list of node/edge records (nodes first, then edges).

    Each node yields {"_type": "node", "id": ...} plus node attributes;
    each edge yields {"_type": "edge", "source": ..., "target": ...} plus edge attributes.
    """
    records: list[Row] = []
    for n in graph.nodes():
        d = {"_type": "node", "id": str(n)}
        d.update(graph.nodes[n])
        records.append(d)
    for u, v, data in graph.edges(data=True):
        d = {"_type": "edge", "source": str(u), "target": str(v)}
        d.update(data)
        records.append(d)
    return records


def rdf_term_to_str(term) -> str:
    """Convert an rdflib term (URIRef, Literal, BNode) to its string form."""
    return str(term)
