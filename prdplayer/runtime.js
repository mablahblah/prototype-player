/* Player runtime: drives a Principle prototype as a state machine.
   Screens are states; a layer present on several screens animates between the
   values it holds on each, using the timing Principle recorded per property. */
(function () {
  var M = window.__PROTO__;
  var stage = document.getElementById("stage");
  var els = {};            // layer key -> element
  var byName = {};         // layer name -> list of keys, for events and drivers
  var current = null;
  var autoTimer = null;
  var symbolTimers = {};   // host layer key -> pending auto-advance

  // Transform-driven properties share one CSS transition, so they share timing.
  var TRANSFORM_PROPS = ["x", "y", "angle", "scale"];

  function css(n) { return Math.round(n * 1000) / 1000; }

  function build(key, parent) {
    var node = M.nodes[key];
    var el = document.createElement("div");
    el.className = "l";
    el.dataset.key = key;
    if (node.clip) el.style.overflow = "hidden";
    if (node.scrollX || node.scrollY) {
      el.style.overflow = node.scrollX ? "auto hidden" : "hidden auto";
      el.dataset.scroll = "1";
    }
    if (node.image) {
      var img = document.createElement("img");
      img.src = M.images[node.image];
      img.draggable = false;
      el.appendChild(img);
    }
    if (node.text) {
      var t = document.createElement("span");
      t.className = "t";
      t.textContent = node.text;
      if (node.fontSize) t.style.fontSize = node.fontSize + "px";
      if (node.color) t.style.color = node.color;
      if (node.weight) t.style.fontWeight = node.weight;
      // Principle's alignment enum: 0 left, 1 centre, 2 right.
      var align = ["flex-start", "center", "flex-end"][node.textAlign || 0];
      t.style.justifyContent = align;
      el.appendChild(t);
    }
    if (node.border && node.borderWidth) {
      el.style.border = node.borderWidth + "px solid " + node.border;
    }
    if (node.shadowColor && node.shadowRadius) {
      el.style.boxShadow = node.shadowX + "px " + node.shadowY + "px " +
        node.shadowRadius + "px " + node.shadowColor;
    }
    (byName[node.name] = byName[node.name] || []).push(key);
    els[key] = el;
    parent.appendChild(el);
    (M.children[key] || []).forEach(function (c) { build(c, el); });
  }

  function transition(state) {
    // Build a CSS transition list from the per-property timing Principle stored.
    var timing = (state && state.timing) || {};
    var parts = [];
    var tf = null;
    TRANSFORM_PROPS.forEach(function (p) {
      var t = timing[p];
      // Several properties collapse into one transform; the slowest one wins.
      if (t && (!tf || t.duration + t.delay > tf.duration + tf.delay)) tf = t;
    });
    function line(prop, t) {
      return prop + " " + t.duration + "s cubic-bezier(" + t.curve.join(",") +
        ") " + t.delay + "s";
    }
    if (tf) parts.push(line("transform", tf));
    if (timing.opacity) parts.push(line("opacity", timing.opacity));
    return parts.join(", ");
  }

  function apply(state, el, animate) {
    el.style.transition = animate ? transition(state) : "none";
    if (!state) {
      // Absent from this screen: fade out and stop taking input.
      el.style.opacity = 0;
      el.style.pointerEvents = "none";
      return;
    }
    el.style.pointerEvents = state.hidden ? "none" : "";
    el.style.zIndex = state.z;
    el.style.width = css(state.w) + "px";
    el.style.height = css(state.h) + "px";
    el.style.left = css(state.x - state.w / 2) + "px";
    el.style.top = css(state.y - state.h / 2) + "px";
    el.style.opacity = state.hidden ? 0 : css(state.opacity);
    el.style.borderRadius = css(state.radius) + "px";
    el.style.background = state.bg || "";
    var tr = "";
    if (state.angle) tr += "rotate(" + css(state.angle) + "deg) ";
    if (state.scale !== 1) tr += "scale(" + css(state.scale) + ") ";
    el.style.transform = tr;
    if (el.dataset.scroll) {
      el.scrollLeft = state.scrollX;
      el.scrollTop = state.scrollY;
    }
  }

  function screenByName(name) {
    return M.screens.filter(function (s) { return s.name === name; })[0];
  }

  function settle(states) {
    // How long a state's own entry animation takes to come to rest. Principle
    // stores timing on the layers being animated to, so this reads the state
    // just arrived at, and an auto-advance waits that long before firing.
    var max = 0;
    Object.keys(states).forEach(function (k) {
      var t = states[k].timing || {};
      Object.keys(t).forEach(function (p) {
        max = Math.max(max, t[p].duration + t[p].delay);
      });
    });
    return max;
  }

  function runSymbol(host, stateName, animate) {
    // A symbol is its own state machine running inside one layer.
    var spec = M.symbols[host];
    if (!spec) return;
    var states = spec.states[stateName];
    if (!states) return;
    Object.keys(states).forEach(function (k) {
      if (els[k]) apply(states[k], els[k], animate);
    });
    clearTimeout(symbolTimers[host]);
    var auto = spec.events.filter(function (e) {
      return e.type === 7 && e.trigger === stateName;
    })[0];
    if (auto) {
      symbolTimers[host] = setTimeout(function () {
        runSymbol(host, auto.target, true);
      }, settle(states) * 1000);
    }
  }

  function interpolate(keyframes, input) {
    // Drivers describe a piecewise-linear curve of input -> output.
    if (input <= keyframes[0][0]) return keyframes[0][1];
    for (var i = 1; i < keyframes.length; i++) {
      var a = keyframes[i - 1], b = keyframes[i];
      if (input <= b[0]) {
        var span = b[0] - a[0];
        var t = span === 0 ? 0 : (input - a[0]) / span;
        return a[1] + (b[1] - a[1]) * t;
      }
    }
    return keyframes[keyframes.length - 1][1];
  }

  function runDrivers() {
    var screen = screenByName(current);
    if (!screen) return;
    M.drivers.filter(function (d) { return d.screen === current; })
      .forEach(function (d) {
        (byName[d.input] || []).forEach(function (inKey) {
          var inEl = els[inKey];
          if (!inEl) return;
          var value = d.inputProp === "scrollX" ? inEl.scrollLeft : inEl.scrollTop;
          (byName[d.output] || []).forEach(function (outKey) {
            var outEl = els[outKey], st = screen.states[outKey];
            if (!outEl || !st) return;
            var out = interpolate(d.keyframes, value);
            outEl.style.transition = "none";
            if (d.outputProp === "opacity") {
              outEl.style.opacity = css(out);
            } else if (d.outputProp === "x") {
              outEl.style.left = css(out - st.w / 2) + "px";
            } else if (d.outputProp === "y") {
              outEl.style.top = css(out - st.h / 2) + "px";
            }
          });
        });
      });
  }

  function go(name, animate) {
    var screen = screenByName(name);
    if (!screen) return;
    current = name;
    stage.style.background = screen.bg;
    M.order.forEach(function (key) {
      apply(screen.states[key], els[key], animate !== false);
    });
    // Each symbol on this screen restarts from its own initial state.
    Object.keys(symbolTimers).forEach(function (h) { clearTimeout(symbolTimers[h]); });
    Object.keys(M.symbols).forEach(function (host) {
      if (screen.states[host]) runSymbol(host, M.symbols[host].initial, false);
    });
    // Drivers set their outputs from the scroll position on arrival.
    requestAnimationFrame(runDrivers);
    document.querySelectorAll("[data-screen]").forEach(function (b) {
      b.classList.toggle("on", b.dataset.screen === name);
    });

    clearTimeout(autoTimer);
    var auto = M.events.filter(function (e) {
      return e.type === 7 && e.triggerIsScreen && e.trigger === name;
    })[0];
    if (auto) {
      autoTimer = setTimeout(function () { go(auto.target); },
        settle(screen.states) * 1000);
    }
  }

  // -- wire up -------------------------------------------------------------
  M.roots.forEach(function (k) { build(k, stage); });

  Object.keys(els).forEach(function (key) {
    if (els[key].dataset.scroll) els[key].addEventListener("scroll", runDrivers);
  });

  // A layer name can trigger different destinations on different screens, so
  // the handler resolves the event against whichever screen is showing.
  var taps = M.events.filter(function (e) {
    return e.type === 0 && !e.triggerIsScreen;
  });
  taps.map(function (e) { return e.trigger; })
    .filter(function (n, i, a) { return a.indexOf(n) === i; })
    .forEach(function (name) {
      (byName[name] || []).forEach(function (key) {
        var el = els[key];
        if (!el) return;
        el.style.cursor = "pointer";
        el.addEventListener("click", function (ev) {
          var match = taps.filter(function (e) {
            return e.trigger === name && e.screen === current;
          })[0];
          if (!match) return;
          ev.stopPropagation();
          go(match.target);
        });
      });
    });

  function fit() {
    // Prototypes come in any size, including landscape and desktop, so scale
    // the whole device down when it will not fit the window at full size.
    var frame = document.getElementById("frame");
    var w = M.width, h = M.height;
    // Below 700px the panel wraps underneath, so the device gets the full width.
    var availW = window.innerWidth - (window.innerWidth < 700 ? 48 : 290);
    var availH = window.innerHeight - 48;
    var s = Math.min(1, availW / w, availH / h);
    device.style.transform = "scale(" + s + ")";
    frame.style.width = w * s + "px";
    frame.style.height = h * s + "px";
  }
  var device = document.getElementById("device");
  window.addEventListener("resize", fit);
  fit();

  window.__go = go;
  go(M.screens[0].name, false);
})();
