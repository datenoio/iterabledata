from __future__ import annotations

import typing
from collections import defaultdict
from typing import Any

import lxml.etree as etree

from ..base import BaseCodec, BaseFileIterable
from ..helpers.xmlsec import safe_parse
from ..types import Row


def etree_to_dict(t, prefix_strip=True):
    """Converts tree of XML elements from lxml to python dictionary"""
    tag = t.tag if not prefix_strip else t.tag.rsplit("}", 1)[-1]
    d = {tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                if prefix_strip:
                    k = k.rsplit("}", 1)[-1]
                dd[k].append(v)
        d = {tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[tag].update(("@" + k.rsplit("}", 1)[-1], v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            tag = tag.rsplit("}", 1)[-1]
            if text:
                d[tag]["#text"] = text
        else:
            d[tag] = text
    return d


def extract_gml_coordinates(elem, ns):
    """Extract coordinates from GML geometry elements"""
    coords = None

    # Try different GML coordinate formats
    # GML 3.2 posList
    pos_list = elem.find(".//{http://www.opengis.net/gml/3.2}posList", ns)
    if pos_list is not None and pos_list.text:
        coords_str = pos_list.text.strip()
        parts = coords_str.split()
        coords = []
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                try:
                    lon = float(parts[i])
                    lat = float(parts[i + 1])
                    coords.append([lon, lat])
                except ValueError:
                    continue

    # GML 3.2 pos
    if coords is None:
        pos_elems = elem.findall(".//{http://www.opengis.net/gml/3.2}pos", ns)
        if pos_elems:
            coords = []
            for pos_elem in pos_elems:
                if pos_elem.text:
                    parts = pos_elem.text.strip().split()
                    if len(parts) >= 2:
                        try:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            coords.append([lon, lat])
                        except ValueError:
                            continue

    # GML 2.0 coordinates
    if coords is None:
        coords_elem = elem.find(".//{http://www.opengis.net/gml}coordinates")
        if coords_elem is not None and coords_elem.text:
            coords_str = coords_elem.text.strip()
            # Parse coordinates: "lon,lat lon,lat ..." or "lon,lat,alt lon,lat,alt ..."
            coords = []
            for coord_str in coords_str.split():
                parts = coord_str.split(",")
                if len(parts) >= 2:
                    try:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        alt = float(parts[2]) if len(parts) > 2 else None
                        if alt is not None:
                            coords.append([lon, lat, alt])
                        else:
                            coords.append([lon, lat])
                    except ValueError:
                        continue

    return coords


_GML_GEOMETRY_TAGS = [
    "Point",
    "LineString",
    "Polygon",
    "MultiPoint",
    "MultiLineString",
    "MultiPolygon",
]

_GML_NON_PROPERTY_TAGS = _GML_GEOMETRY_TAGS + ["geometry", "geometryProperty", "boundedBy", "location"]


def _extract_feature_properties(elem):
    """Extract non-geometry child elements as GeoJSON feature properties."""
    properties = {}
    for child in elem:
        child_tag = child.tag.rsplit("}", 1)[-1]
        # Skip geometry elements
        if child_tag in _GML_NON_PROPERTY_TAGS:
            continue
        if child.text:
            properties[child_tag] = child.text.strip()
        elif len(child) > 0:
            # Nested structure
            properties[child_tag] = etree_to_dict(child)
        else:
            properties[child_tag] = None
    return properties


def _find_gml_element(elem, tag, ns):
    """Find a GML element by tag, trying GML 3.2 then GML 2.0 namespaces."""
    found = elem.find(f".//{{http://www.opengis.net/gml/3.2}}{tag}", ns)
    if found is None:
        found = elem.find(f".//{{http://www.opengis.net/gml}}{tag}")
    return found


def _find_gml_elements(elem, tag, ns):
    """Find all GML elements by tag, trying GML 3.2 then GML 2.0 namespaces."""
    found = elem.findall(f".//{{http://www.opengis.net/gml/3.2}}{tag}", ns)
    if not found:
        found = elem.findall(f".//{{http://www.opengis.net/gml}}{tag}")
    return found


def _find_geometry_element(elem, ns):
    """Locate the geometry element of a GML feature, or None."""
    # Try GML 3.2 geometryProperty
    geom_prop = elem.find(".//{http://www.opengis.net/gml/3.2}geometryProperty", ns)
    if geom_prop is None:
        geom_prop = elem.find(".//geometryProperty")

    if geom_prop is not None:
        return geom_prop[0] if len(geom_prop) > 0 else None

    # Try direct geometry elements
    for geom_tag in _GML_GEOMETRY_TAGS:
        geom_elem = _find_gml_element(elem, geom_tag, ns)
        if geom_elem is not None:
            return geom_elem
    return None


def _member_coordinates(geom_elem, member_tag, ns):
    """Collect coordinates of each member geometry (LineString/Polygon) of a multi-geometry."""
    multi_coords = []
    for member in _find_gml_elements(geom_elem, member_tag, ns):
        member_coords = extract_gml_coordinates(member, ns)
        if member_coords:
            multi_coords.append(member_coords)
    return multi_coords


def _build_geojson_geometry(geom_elem, geom_tag, coords, ns):
    """Build a GeoJSON geometry dict for a GML geometry element, or None."""
    if geom_tag == "Point":
        return {"type": "Point", "coordinates": coords[0] if coords else None}
    if geom_tag == "LineString":
        return {"type": "LineString", "coordinates": coords}
    if geom_tag == "Polygon":
        return {"type": "Polygon", "coordinates": [coords]}
    if geom_tag == "MultiPoint":
        return {"type": "MultiPoint", "coordinates": coords}
    if geom_tag == "MultiLineString":
        # GML MultiLineString has multiple LineString elements
        multi_coords = _member_coordinates(geom_elem, "LineString", ns)
        if multi_coords:
            return {"type": "MultiLineString", "coordinates": multi_coords}
    elif geom_tag == "MultiPolygon":
        # GML MultiPolygon has multiple Polygon elements
        multi_coords = _member_coordinates(geom_elem, "Polygon", ns)
        if multi_coords:
            return {"type": "MultiPolygon", "coordinates": [[poly_coords] for poly_coords in multi_coords]}
    return None


def gml_to_geojson(elem, ns):
    """Convert GML feature to GeoJSON-like feature"""
    feature = {"type": "Feature", "properties": _extract_feature_properties(elem), "geometry": None}

    # Extract geometry
    geom_elem = _find_geometry_element(elem, ns)

    if geom_elem is not None:
        geom_tag = geom_elem.tag.rsplit("}", 1)[-1]
        coords = extract_gml_coordinates(geom_elem, ns)

        if coords:
            feature["geometry"] = _build_geojson_geometry(geom_elem, geom_tag, coords, ns)

    return feature


def _pos_text(c):
    """Format a coordinate tuple as a GML pos string."""
    return f"{c[0]} {c[1]}" + (f" {c[2]}" if len(c) > 2 else "")


def _pos_list_text(coords):
    """Format a list of coordinates as a GML posList string."""
    return " ".join(_pos_text(c) for c in coords)


def _add_point_geometry(geom_prop, coords):
    point = etree.SubElement(geom_prop, "{http://www.opengis.net/gml/3.2}Point")
    pos = etree.SubElement(point, "{http://www.opengis.net/gml/3.2}pos")
    pos.text = _pos_text(coords)


def _add_linestring_geometry(geom_prop, coords):
    linestring = etree.SubElement(geom_prop, "{http://www.opengis.net/gml/3.2}LineString")
    pos_list = etree.SubElement(linestring, "{http://www.opengis.net/gml/3.2}posList")
    pos_list.text = _pos_list_text(coords)


def _add_polygon_geometry(geom_prop, coords):
    polygon = etree.SubElement(geom_prop, "{http://www.opengis.net/gml/3.2}Polygon")
    exterior = etree.SubElement(polygon, "{http://www.opengis.net/gml/3.2}exterior")
    linear_ring = etree.SubElement(exterior, "{http://www.opengis.net/gml/3.2}LinearRing")
    pos_list = etree.SubElement(linear_ring, "{http://www.opengis.net/gml/3.2}posList")
    outer_ring = coords[0] if isinstance(coords[0], list) and len(coords) > 0 else coords
    pos_list.text = _pos_list_text(outer_ring)


_GEOMETRY_WRITERS = {
    "Point": _add_point_geometry,
    "LineString": _add_linestring_geometry,
    "Polygon": _add_polygon_geometry,
}


def _add_geometry(feature, geometry):
    """Append a geometryProperty element for a GeoJSON-like geometry dict."""
    if not geometry:
        return
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    geom_prop = etree.SubElement(feature, "{http://www.opengis.net/gml/3.2}geometryProperty")
    writer = _GEOMETRY_WRITERS.get(geom_type)
    if writer is not None and coords:
        writer(geom_prop, coords)


class GMLIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        prefix_strip: bool = True,
        feature_member: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, encoding="utf8", options=options)
        self.prefix_strip = prefix_strip
        self.feature_member = feature_member or "featureMember"
        self.reset()

    def reset(self):
        super().reset()
        self.features = []
        self.pos = 0

        if self.mode == "r":
            # Parse GML document
            try:
                tree = safe_parse(self.fobj)
                root = tree.getroot()

                # Common GML namespaces
                ns = {"gml": "http://www.opengis.net/gml/3.2", "gml2": "http://www.opengis.net/gml"}

                # Find all feature members
                feature_members = root.findall(f".//{{http://www.opengis.net/gml/3.2}}{self.feature_member}", ns)
                if not feature_members:
                    feature_members = root.findall(f".//{{http://www.opengis.net/gml}}{self.feature_member}")
                if not feature_members:
                    # Try without namespace
                    feature_members = root.findall(f".//{self.feature_member}")

                # If no featureMember, try to find feature elements directly
                if not feature_members:
                    # Look for common feature element names
                    for tag_name in ["feature", "Feature", "member"]:
                        feature_members = root.findall(f".//{tag_name}")
                        if feature_members:
                            break

                for member in feature_members:
                    # Get the feature element (first child or the member itself)
                    feature_elem = member[0] if len(member) > 0 else member
                    feature = gml_to_geojson(feature_elem, ns)
                    if feature["geometry"] is not None or feature["properties"]:
                        self.features.append(feature)

                self.iterator = iter(self.features)
            except Exception:
                self.features = []
                self.iterator = iter(self.features)

    @staticmethod
    def id() -> str:
        return "gml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if hasattr(self, "features"):
            return len(self.features)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single GML feature"""
        feature = next(self.iterator)
        self.pos += 1
        return feature

    def write(self, record: Row) -> None:
        """Write single GML feature"""
        # Convert GeoJSON-like feature to GML
        if "type" not in record or record["type"] != "Feature":
            if "geometry" in record:
                record = {"type": "Feature", "properties": record.get("properties", {}), "geometry": record["geometry"]}

        # Create featureMember element
        feature_member = etree.Element("{http://www.opengis.net/gml/3.2}featureMember")
        feature = etree.SubElement(feature_member, "{http://www.opengis.net/gml/3.2}Feature")

        # Add properties
        for key, value in record.get("properties", {}).items():
            prop_elem = etree.SubElement(feature, key)
            if isinstance(value, dict):
                # Nested structure - simplified
                prop_elem.text = str(value)
            else:
                prop_elem.text = str(value) if value is not None else ""

        # Add geometry
        _add_geometry(feature, record.get("geometry", {}))

        # Write to file
        if not hasattr(self, "root_written"):
            # Write GML header
            header = '<?xml version="1.0" encoding="UTF-8"?>\n<gml:FeatureCollection xmlns:gml="http://www.opengis.net/gml/3.2">\n'
            self.fobj.write(header.encode("utf-8") if self.binary else header)
            self.root_written = True

        etree.indent(feature_member, space="  ")
        xml_str = etree.tostring(feature_member, encoding="unicode", pretty_print=True) + "\n"
        self.fobj.write(xml_str.encode("utf-8") if self.binary else xml_str)
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk GML features"""
        for record in records:
            self.write(record)

    def close(self):
        """Close file and write GML footer if writing"""
        if self.mode in ["w", "wr"] and hasattr(self, "root_written"):
            footer = "</gml:FeatureCollection>\n"
            self.fobj.write(footer.encode("utf-8") if self.binary else footer)
        super().close()
