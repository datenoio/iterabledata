import datetime
import logging
from copy import copy
from typing import Any

try:
    from bson.int64 import Int64 as BSONInt64
    from bson.objectid import ObjectId as BSONObjectId
except ImportError:
    BSONInt64 = None
    BSONObjectId = None

from .utils import get_dict_value_deep

OTYPES_MAP = [
    [str, "string"],
    [str, "string"],
    [datetime.datetime, "datetime"],
    [int, "integer"],
    [bool, "boolean"],
    [float, "float"],
    [str, "string"],
    [type([]), "array"],
]

if BSONInt64 is not None and BSONObjectId is not None:
    OTYPES_MAP.extend(
        [
            [BSONInt64, "integer"],
            [BSONObjectId, "string"],
        ]
    )


def _bson_type_name(value: Any) -> str | None:
    if BSONInt64 is not None and isinstance(value, BSONInt64):
        return "integer"
    if BSONObjectId is not None and isinstance(value, BSONObjectId):
        return "string"
    return None


def _is_weak_field_schema(info: dict[str, Any]) -> bool:
    """Return True when ``info`` is a placeholder that later rows may upgrade."""

    field_type = info.get("type")
    if field_type == "string":
        # ``None`` values are recorded as string placeholders.
        return True
    if field_type == "array" and info.get("subtype") != "dict":
        # Empty arrays omit subtype; scalar arrays may later see dict items.
        return True
    if field_type == "array" and info.get("subtype") == "dict" and "schema" not in info:
        return True
    return False


def _should_upgrade_field_schema(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Upgrade only null/empty placeholders into structured dict/array shapes."""

    if not _is_weak_field_schema(left):
        return False
    right_type = right.get("type")
    if right_type == "dict" and isinstance(right.get("schema"), dict):
        return True
    if right_type == "array" and (right.get("subtype") == "dict" or isinstance(right.get("schema"), dict)):
        return True
    if left.get("type") == "array" and left.get("subtype") is None and right_type == "array" and right.get("subtype"):
        return True
    return False


def merge_schemes(alist, novalue=True):
    """Merges schemes of list of objects and generates final data schema"""
    if len(alist) == 0:
        return None
    obj = alist[0]
    okeys = obj.keys()
    for item in alist[1:]:
        for k in item.keys():
            #            print(obj[k]['type'])
            if k not in okeys:
                obj[k] = item[k]
                continue

            left = obj[k]
            right = item[k]
            if not isinstance(left, dict) or not isinstance(right, dict):
                continue

            # Null placeholders and empty arrays start weak; upgrade when a later
            # row observes a richer dict / array-of-dict shape.
            if _should_upgrade_field_schema(left, right):
                upgraded = copy(right)
                if (
                    left.get("type") == "array"
                    and upgraded.get("type") == "array"
                    and isinstance(left.get("schema"), dict)
                    and isinstance(upgraded.get("schema"), dict)
                ):
                    upgraded["schema"] = merge_schemes([left["schema"], upgraded["schema"]])
                elif (
                    left.get("type") == "dict"
                    and upgraded.get("type") == "dict"
                    and isinstance(left.get("schema"), dict)
                    and isinstance(upgraded.get("schema"), dict)
                ):
                    upgraded["schema"] = merge_schemes([left["schema"], upgraded["schema"]])
                if not novalue and "value" in left and "value" in upgraded:
                    upgraded["value"] = left["value"] + right.get("value", 0)
                obj[k] = upgraded
                continue

            if left["type"] in ["integer", "float", "string", "datetime"]:
                if not novalue:
                    left["value"] += right["value"]
            elif left["type"] == "dict":
                if not novalue:
                    left["value"] += right["value"]
                if "schema" in right and "schema" in left:
                    left["schema"] = merge_schemes([left["schema"], right["schema"]])
                elif "schema" in right and "schema" not in left:
                    left["schema"] = right["schema"]
            elif left["type"] == "array":
                if not novalue:
                    left["value"] += right["value"]
                if right.get("subtype") == "dict" and "schema" in right:
                    if left.get("subtype") != "dict" or "schema" not in left:
                        left["subtype"] = "dict"
                        left["schema"] = right["schema"]
                    else:
                        left["schema"] = merge_schemes([left["schema"], right["schema"]])
                elif left.get("subtype") == "dict" and "schema" in left and "schema" in right:
                    left["schema"] = merge_schemes([left["schema"], right["schema"]])
    return obj


def get_schemes(alist):
    """Generates schemas for each object"""
    results = []
    for o in alist:
        results.append(get_schema(o))
    return results


def get_schema(obj: dict, novalue=True):
    """Generates schema from object"""
    result = {}
    for k in obj.keys():
        if obj[k] is None:
            result[k] = {"type": "string", "value": 1}
        elif isinstance(obj[k], str):
            result[k] = {"type": "string", "value": 1}
        elif isinstance(obj[k], datetime.datetime):
            result[k] = {"type": "datetime", "value": 1}
        elif isinstance(obj[k], bool):
            result[k] = {"type": "boolean", "value": 1}
        elif isinstance(obj[k], float):
            result[k] = {"type": "float", "value": 1}
        elif isinstance(obj[k], int):
            result[k] = {"type": "integer", "value": 1}
        elif (bson_type := _bson_type_name(obj[k])) is not None:
            result[k] = {"type": bson_type, "value": 1}
        elif isinstance(obj[k], dict):
            result[k] = {"type": "dict", "value": 1, "schema": get_schema(obj[k])}
        elif isinstance(obj[k], list):
            result[k] = {"type": "array", "value": 1}
            if len(obj[k]) == 0:
                # Leave subtype unset so later non-empty rows can upgrade the
                # array to array-of-dict (or a concrete scalar subtype).
                pass
            else:
                found = False
                for otype, oname in OTYPES_MAP:
                    if isinstance(obj[k][0], otype):
                        result[k]["subtype"] = oname
                        found = True
                if not found:
                    if isinstance(obj[k][0], dict):
                        result[k]["subtype"] = "dict"
                        result[k]["schema"] = merge_schemes(get_schemes(obj[k]))
                    else:
                        logging.info(f"Unknown object {k} type {str(type(obj[k][0]))}")
        else:
            logging.info(f"Unknown object {k} type {str(type(obj[k]))}")
            result[k] = {"type": "string", "value": 1}
        if novalue:
            del result[k]["value"]
    return result


def extract_keys_from_dict(obj: dict, parent: str = None, text: str = None, level: int = 1):
    """Extracts keys from object"""
    if text is None:
        text = ""
    if not parent:
        text = "'schema': {\n"
    for k in obj.keys():
        if isinstance(obj[k], dict):
            text += "\t" * level + f"'{k}' : {{'type' : 'dict', 'schema' : {{\n"
            text += extract_keys_from_dict(obj[k], k, text, level + 1)
            text += "\t" * level + "}},\n"
        elif isinstance(obj[k], list):
            text += "\t" * level + f"'{k}' : {{'type' : 'list', 'schema' : {{ 'type' : 'dict', 'schema' : {{\n"
            if len(obj[k]) > 0:
                item = obj[k][0]
                if isinstance(item, dict):
                    text += extract_keys_from_dict(item, k, text, level + 1)
                else:
                    text += "\t" * level + f"'{k}' : {{'type' : 'string'}},\n"
            text += "\t" * level + "}}},\n"
        else:
            logging.info(str(type(obj[k])))
            text += "\t" * level + f"'{k}' : {{'type' : 'string'}},\n"
    if not parent:
        text += "}"
    return text


def schema_from_list_of_dicts(data: list[dict]):
    """Generates schema from python dictionary"""
    scheme = None
    for r in data:
        if scheme is None:
            scheme = get_schema(r)
        else:
            scheme = merge_schemes([scheme, get_schema(r)])
    return scheme


def schema2fieldslist(schema: dict, prefix: str = None, predefined: dict = None, sample: dict = None):
    """Converts data schema to the fields list"""
    fieldslist = []
    for k in schema.keys():
        if prefix is None:
            name = k
        else:
            name = ".".join([".".join(prefix.split(".")), k])
        try:
            sampledata = get_dict_value_deep(sample, name) if sample else ""
        except Exception:
            sampledata = ""
        if "schema" not in schema[k].keys():
            if schema[k]["type"] != "array":
                field = {"name": name, "type": schema[k]["type"], "description": "", "sample": sampledata, "class": ""}
            else:
                subtype = schema[k].get("subtype", "any")
                field = {
                    "name": name,
                    "type": f"list of [{subtype}]",
                    "description": "",
                    "sample": sampledata,
                    "class": "",
                }
            if predefined:
                if name in predefined.keys():
                    field["description"] = predefined[name]["text"]
                    if predefined[name]["class"]:
                        field["class"] = predefined[name]["class"]
                elif k in predefined.keys():
                    field["description"] = predefined[k]["text"]
                    if predefined[k]["class"]:
                        field["class"] = predefined[k]["class"]
            if field["type"] == "datetime":
                field["class"] = "datetime"
            fieldslist.append(field)
        else:
            if prefix is not None:
                subprefix = copy(prefix) + "." + k
            #                subprefix.append(k)
            else:
                subprefix = k
            if schema[k]["type"] == "dict":
                field = {"name": name, "type": schema[k]["type"], "description": "", "sample": "", "class": ""}
                if predefined:
                    if name in predefined.keys():
                        field["description"] = predefined[name]["text"]
                        if predefined[name]["class"]:
                            field["class"] = predefined[name]["class"]
                    elif k in predefined.keys():
                        field["description"] = predefined[k]["text"]
                        if predefined[k]["class"]:
                            field["class"] = predefined[k]["class"]
                fieldslist.append(field)
                fieldslist.extend(
                    schema2fieldslist(schema[k]["schema"], prefix=subprefix, predefined=predefined, sample=sample)
                )
            elif schema[k]["type"] == "array":
                subtype = schema[k].get("subtype", "any")
                field = {"name": name, "type": f"list of [{subtype}]", "description": "", "sample": "", "class": ""}
                if predefined:
                    if name in predefined.keys():
                        field["description"] = predefined[name]["text"]
                        if predefined[name]["class"]:
                            field["class"] = predefined[name]["class"]
                    elif k in predefined.keys():
                        field["description"] = predefined[k]["text"]
                        if predefined[k]["class"]:
                            field["class"] = predefined[k]["class"]
                fieldslist.append(field)
                fieldslist.extend(schema2fieldslist(schema[k]["schema"], prefix=subprefix, sample=sample))
    return fieldslist
