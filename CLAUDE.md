# PRD Proto Player

Rebuilds prototypes from old and outdated prototyping tools into small standalone web pages, so they can be used again without their original application. Read-only — the prototypes are usable, never editable.

This repository is a worked example of the converter and the player. The prototype archive, the project brief and the planning notes are not published with it — anyone using this brings their own `.prd` files. Locally those live in `protos/` and `docs/`, both ignored by git.

## Tech Stack

- **Converter**: Python 3, standard library only — `plistlib` reads the archive format.
- **Output**: one self-contained HTML file per prototype. No framework, no build step, no assets on disk; images are inlined as data URIs.

## Commands

```
python3 convert.py "protos/<name>.prd"    # convert one prototype into out/
python3 convert.py protos/*.prd           # convert the whole archive
```

Open the generated file in `out/` directly — it needs no server.

## Architecture

```
convert.py                 # CLI entry point
prdplayer/
├── unarchive.py           # NSKeyedArchiver plist -> plain Python objects
├── model.py               # Principle object tree -> flat model for the player
├── render.py              # model -> one standalone HTML file
└── runtime.js             # the player: state machine, drivers, symbols
protos/                    # source prototypes, read-only — local only, not published
out/
├── prince-protos/         # generated from .prd — rebuilt by the converter, not published
└── html-conversions/      # written by hand, nothing regenerates them — published
```

## Source Formats

`protos/` holds the source prototypes. `.prd` is the current focus.

- **`.prd` — Principle (macOS).** 15 files. An Apple binary property list written by `NSKeyedArchiver`, holding an object graph of `PRPrototype`, `PRScreen`, `PRLayer`, `PRImage`, `PRLink` and `PRKeyframe`. Structured data, not compiled web code — so conversion is translation, not decompilation.
- **`.pie` — ProtoPie.** 7 files. Encrypted; not convertible.
- **`.framer` — Framer Classic.** One folder. Empty; nothing to convert.

All three are documented locally in `docs/tech/other-formats.md`, which is not published.

## Terminology

- **Screen**: a `PRScreen` — one artboard the prototype can display.
- **Layer**: a `PRLayer` — a nestable visual element on a screen.
- **Link**: a `PRLink` — a transition from one screen to another, triggered by an interaction.
- **Keyframe**: a `PRKeyframe` — an animated property value, driving motion within a screen.
- **Player**: the generated web page that renders a converted prototype.

## How Things Work Here

- Fidelity is judged against how the prototype looked and behaved in its original tool's preview.
- Prototypes in `protos/` are the archive and are never modified. Conversion only reads them.
- A prototype with no links and no keyframes is still valid — it renders as a still.
- Every page carries its own copy of the styles and scripts it needs, so the hand-written pages repeat each other almost line for line. That duplication is the price of a page that works anywhere with no assets beside it, and it is deliberate.

## Workflow: Rocket-Ship

Work is feature-driven and iterative. `/plan-feature` moves the next backlog item into CURRENT-FEATURE, scopes it with acceptance criteria, and produces a spec. `/start-work-session` builds iteratively with tournament-style sub-agents, and `/end-work-session` closes the session and writes the hand-off — run the pair once per session until the feature is done. `/ship-feature` verifies ACs, runs audit and documentation, generates changelogs, and merges.
