"""Turns a Principle object tree into a flat model the web player can run.

Principle is a state machine: screens are states, and a layer that appears on
more than one screen animates between the values it holds on each. Layers are
matched across screens by their name path, so that is the identity used here.
"""
import base64
import re

# Principle addresses animatable properties by index. These were established by
# matching driver keyframe outputs against the values stored on their layers.
PROPERTY_BY_INDEX = {
    1: "x",
    2: "y",
    3: "angle",
    4: "scale",
    7: "opacity",
    10: "scrollX",
    11: "scrollY",
}

# horizontalBehavior / verticalBehavior use 2 to mean "this axis scrolls".
SCROLL_BEHAVIOR = 2

# PREvent.type — 0 is a tap on a layer, 7 fires on entering a screen.
EVENT_TAP = 0
EVENT_AUTO = 7


def _colour(layer, prefix):
    """Read a Principle RGBA colour into a CSS rgba() string."""
    if f"{prefix}.0" not in layer:
        return None
    channels = [layer.get(f"{prefix}.{i}", 0.0) for i in range(4)]
    r, g, b = (round(c * 255) for c in channels[:3])
    return f"rgba({r},{g},{b},{round(channels[3], 4)})"


def _font_weight(family):
    """Principle names fonts by PostScript name; the trailing number is weight."""
    if not family:
        return None
    match = re.search(r"(\d{3})$", family)
    return int(match.group(1)) if match else None


def _image_data_uri(image):
    """Principle stores bitmaps inline; emit them as data URIs."""
    if not image:
        return None
    raw = image.get("jpegData") or b""
    if not raw:
        return None
    kind = "png" if raw[:4] == b"\x89PNG" else "jpeg"
    return f"data:image/{kind};base64," + base64.b64encode(raw).decode("ascii")


class Builder:
    def __init__(self, prototype):
        self.prototype = prototype
        self.nodes = {}          # key -> static description of a layer
        self.order = []          # keys in the order they were first seen
        self.children = {}       # key -> list of child keys
        self.roots = []
        self.images = {}         # data URI -> short id, so repeats are stored once
        self.symbol_specs = {}
        self.layer_screen = {}   # id(layer object) -> screen it sits on
        self.current_screen = None

    # -- static layer description -------------------------------------------

    def _image_id(self, layer):
        uri = _image_data_uri(layer.get("image"))
        if not uri:
            return None
        if uri not in self.images:
            self.images[uri] = f"i{len(self.images)}"
        return self.images[uri]

    def _static(self, layer):
        """The parts of a layer that never change between screens."""
        text = layer.get("text")
        text = text if isinstance(text, str) else None
        # On a text layer Principle stores the type colour in backgroundColor.
        colour = _colour(layer, "backgroundColor") if text else None
        return {
            "name": layer.get("name") or "",
            "color": colour,
            "weight": _font_weight(layer.get("fontFamily")),
            "image": self._image_id(layer),
            "text": text,
            "fontFamily": layer.get("fontFamily"),
            "fontSize": layer.get("fontSize"),
            "textAlign": layer.get("textAlignment"),
            "scrollX": layer.get("horizontalBehavior") == SCROLL_BEHAVIOR,
            "scrollY": layer.get("verticalBehavior") == SCROLL_BEHAVIOR,
            "clip": bool(layer.get("maskToBounds")),
            "border": _colour(layer, "borderColor"),
            "borderWidth": layer.get("borderWidth") or 0,
            "shadowColor": _colour(layer, "shadowColor"),
            "shadowRadius": layer.get("shadowRadius") or 0,
            "shadowX": layer.get("shadowOffset.width") or 0,
            "shadowY": layer.get("shadowOffset.height") or 0,
        }

    # -- per-screen state ----------------------------------------------------

    def _state(self, layer):
        """The values a layer holds on one particular screen."""
        symbol = layer.get("prototypeLayer")
        width = layer.get("size.width")
        height = layer.get("size.height")
        # Symbol instances take their size from the symbol screen they show.
        if width is None and symbol:
            width = symbol.get("size.width")
            height = symbol.get("size.height")
        info = layer.get("animationInfo") or {}
        timing = {}
        for index, entry in info.items():
            if not isinstance(entry, dict) or index == "__class__":
                continue
            prop = PROPERTY_BY_INDEX.get(int(index))
            if not prop:
                continue
            curve = entry.get("customCurve") or {}
            timing[prop] = {
                "duration": entry.get("duration", 0.3),
                "delay": entry.get("delay", 0.0),
                "curve": [
                    curve.get("c1x", 0.42), curve.get("c1y", 0.0),
                    curve.get("c2x", 0.58), curve.get("c2y", 1.0),
                ],
            }
        return {
            "x": layer.get("position.x", 0.0),
            "y": layer.get("position.y", 0.0),
            "w": width if width is not None else 0.0,
            "h": height if height is not None else 0.0,
            "opacity": 1.0 if layer.get("opacity") is None else layer["opacity"],
            "angle": layer.get("angle") or 0.0,
            "scale": 1.0 if layer.get("scale") is None else layer["scale"],
            "radius": layer.get("radius") or 0.0,
            "bg": None if isinstance(layer.get("text"), str)
                  else _colour(layer, "backgroundColor"),
            "hidden": bool(layer.get("hidden")),
            "scrollX": layer.get("contentOffset.x") or 0.0,
            "scrollY": layer.get("contentOffset.y") or 0.0,
            "symbol": id(symbol) if symbol else None,
            "timing": timing,
        }

    # -- tree walking --------------------------------------------------------

    def visit(self, layer, parent_key, states, seen_keys, index=0,
              symbol_capture=None):
        """Register a layer under its parent and record its state for a screen."""
        name = layer.get("name") or "layer"
        key = f"{parent_key}/{name}" if parent_key else name
        # Sibling names repeat; disambiguate only when a screen reuses one.
        if key in seen_keys:
            n = 2
            while f"{key}#{n}" in seen_keys:
                n += 1
            key = f"{key}#{n}"
        seen_keys.add(key)

        if key not in self.nodes:
            self.nodes[key] = self._static(layer)
            self.order.append(key)
            self.children.setdefault(key, [])
            if parent_key:
                if key not in self.children.setdefault(parent_key, []):
                    self.children[parent_key].append(key)
            else:
                self.roots.append(key)

        state = self._state(layer)
        state["z"] = index
        states[key] = state
        # An event is scoped to the screen its trigger layer belongs to, so
        # remember where each layer object was seen.
        self.layer_screen[id(layer)] = self.current_screen
        if symbol_capture is not None:
            symbol_capture(layer, key)

        # A symbol instance draws the screen it points at, in its own space.
        symbol = layer.get("prototypeLayer")
        source = symbol if symbol else layer
        # Layers are listed back to front, so the list index is the depth.
        for i, child in enumerate(source.get("subPictures") or []):
            self.visit(child, key, states, seen_keys, i, symbol_capture)

        # A symbol instance runs its own little state machine inside this layer.
        if symbol:
            self.capture_symbol(key, symbol)
        return key

    def capture_symbol(self, key, symbol_screen):
        """Record every state the symbol inside this layer can be in."""
        if key in self.symbol_specs:
            return
        owner = symbol_screen.get("owner") or {}
        spec = {"initial": symbol_screen.get("name"), "states": {}, "events": []}
        self.symbol_specs[key] = spec
        for screen in (owner.get("screens") or []):
            states = {}
            seen = set()
            for i, child in enumerate(screen.get("subPictures") or []):
                self.visit(child, key, states, seen, i)
            spec["states"][screen["name"]] = states
        for event in (owner.get("transitions") or []):
            target, trigger = event.get("action"), event.get("dependent")
            if target and trigger:
                spec["events"].append({
                    "type": event.get("type"),
                    "trigger": trigger.get("name"),
                    "target": target.get("name"),
                })


def build(prototype):
    """Produce the model dict handed to the renderer."""
    builder = Builder(prototype)
    screens = []
    screen_index = {}

    for screen in prototype["screens"]:
        states = {}
        seen = set()
        builder.current_screen = screen["name"]
        for i, child in enumerate(screen.get("subPictures") or []):
            builder.visit(child, "", states, seen, i)
        screen_index[id(screen)] = screen["name"]
        screens.append({
            "name": screen["name"],
            "w": screen.get("size.width", 375.0),
            "h": screen.get("size.height", 812.0),
            "bg": _colour(screen, "backgroundColor") or "#fff",
            "states": states,
        })

    # Events: taps target a layer, auto-advances target the screen itself.
    events = []
    for event in (prototype.get("transitions") or []):
        target = event.get("action")
        trigger = event.get("dependent")
        if not target or not trigger:
            continue
        is_screen = trigger.get("__class__") == "PRScreen"
        events.append({
            "type": event.get("type"),
            "trigger": trigger.get("name"),
            "triggerIsScreen": is_screen,
            # Which screen this event is active on. For an auto-advance the
            # trigger is the screen itself.
            "screen": trigger.get("name") if is_screen
                      else builder.layer_screen.get(id(trigger)),
            "target": target.get("name"),
        })

    # Drivers: one layer's property continuously drives another's.
    drivers = []
    for screen in prototype["screens"]:
        for link in (screen.get("links") or []):
            in_prop = PROPERTY_BY_INDEX.get(link.get("inputProperty"))
            out_prop = PROPERTY_BY_INDEX.get(link.get("outputProperty"))
            if not in_prop or not out_prop:
                continue
            drivers.append({
                "screen": screen["name"],
                "input": link["inputLayer"].get("name"),
                "inputProp": in_prop,
                "output": link["outputLayer"].get("name"),
                "outputProp": out_prop,
                "keyframes": [[k["input"], k["output"]] for k in link["keyframes"]],
            })

    return {
        "width": screens[0]["w"],
        "height": screens[0]["h"],
        "screens": screens,
        "order": builder.order,
        "nodes": builder.nodes,
        "children": builder.children,
        "roots": builder.roots,
        "events": events,
        "drivers": drivers,
        "images": {v: k for k, v in builder.images.items()},
        "symbols": builder.symbol_specs,
    }
