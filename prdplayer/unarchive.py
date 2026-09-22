"""Turns an NSKeyedArchiver plist into plain Python dicts, lists and scalars.

Principle documents (.prd) are Apple binary property lists written by
NSKeyedArchiver: a flat object table plus UID references between entries.
This module walks those references and rebuilds the real object tree.
"""
import plistlib
from plistlib import UID

# Foundation container classes get unwrapped into native Python equivalents.
_ARRAYS = {"NSMutableArray", "NSArray", "NSSet", "NSMutableSet"}
_DICTS = {"NSDictionary", "NSMutableDictionary"}
_DATA = {"NSMutableData", "NSData"}
_STRINGS = {"NSString", "NSMutableString"}


def load(path):
    """Read a .prd file and return its root object as plain Python data."""
    with open(path, "rb") as fh:
        plist = plistlib.load(fh)
    objects = plist["$objects"]
    resolved = {}

    def classname(entry):
        return objects[entry["$class"].data].get("$classname")

    def resolve(ref):
        # Anything that isn't a reference is already a plain value.
        if not isinstance(ref, UID):
            return ref
        index = ref.data
        if index in resolved:
            return resolved[index]
        entry = objects[index]
        if entry == "$null":
            return None
        if not isinstance(entry, dict):
            return entry
        name = classname(entry) if "$class" in entry else None

        if name in _ARRAYS:
            out = []
            resolved[index] = out
            out.extend(resolve(x) for x in entry.get("NS.objects", []))
            return out
        if name in _DICTS:
            out = {}
            resolved[index] = out
            keys = [resolve(k) for k in entry.get("NS.keys", [])]
            vals = [resolve(v) for v in entry.get("NS.objects", [])]
            out.update({str(k): v for k, v in zip(keys, vals)})
            return out
        if name in _DATA:
            resolved[index] = entry.get("NS.data", b"")
            return resolved[index]
        if name in _STRINGS:
            resolved[index] = entry.get("NS.string", "")
            return resolved[index]
        if name == "NSUUID":
            resolved[index] = entry.get("NS.uuidbytes", b"").hex()
            return resolved[index]

        # Everything else keeps its class name so the model layer can dispatch.
        out = {"__class__": name}
        resolved[index] = out
        for key, value in entry.items():
            if key == "$class":
                continue
            out[key] = resolve(value)
        return out

    return resolve(plist["$top"]["root"])
