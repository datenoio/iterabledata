"""Hardened XML parsing helpers (XXE protection).

All lxml parsing in the library goes through these helpers so that untrusted
XML input cannot exploit external entity resolution (XXE), load remote DTDs,
or trigger network access during parsing. lxml is imported lazily because XML
support is an optional dependency.
"""

from __future__ import annotations

from typing import Any


def hardened_xml_parser(recover: bool = True) -> Any:
    """Return an lxml ``XMLParser`` with entity/DTD/network resolution disabled."""
    from lxml import etree

    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
        recover=recover,
    )


def safe_parse(source: Any, recover: bool = True) -> Any:
    """Parse an XML document with XXE protections enabled."""
    from lxml import etree

    return etree.parse(source, parser=hardened_xml_parser(recover=recover))


def safe_iterparse(source: Any, events: tuple[str, ...] | None = None, recover: bool = True) -> Any:
    """Incrementally parse an XML document with XXE protections enabled."""
    from lxml import etree

    kwargs: dict[str, Any] = {
        "resolve_entities": False,
        "no_network": True,
        "load_dtd": False,
        "dtd_validation": False,
        "recover": recover,
    }
    if events is not None:
        kwargs["events"] = events
    return etree.iterparse(source, **kwargs)
