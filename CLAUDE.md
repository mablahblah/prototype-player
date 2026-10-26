# PRD Proto Player

Rebuilds prototypes from old and outdated prototyping tools into small standalone web pages, so they can be used again without their original application. Read-only — the prototypes are usable, never editable.

This repository is a worked example of the converter and the player. The prototype archive, the project brief and the planning notes are not published with it — anyone using this brings their own `.prd` files. Locally those live in `protos/` and `docs/`, both ignored by git.

## Tech Stack

- **Converter**: Python 3, standard library only — `plistlib` reads the archive format.
- **Output**: one self-contained HTML file per `.prd` prototype. No framework, no build step, no assets on disk; images are inlined as data URIs.
- **Sites**: a React site is built with its own Vite, which needs Node.js; a plain site is copied. This is the one exception to the two lines above: the converter calls Node, and a site is a folder of files rather than one page.

## Commands

```
python3 convert.py    # sync protos/show/ and protos/hide/ into out/show/ and out/hide/
```

A generated `.prd` page opens directly from disk. A site needs a server with `out/` as its root, since its addresses start there.

## Architecture

```
convert.py                 # CLI entry point
prdplayer/
├── unarchive.py           # NSKeyedArchiver plist -> plain Python objects
├── model.py               # Principle object tree -> flat model for the player
├── render.py              # model -> one standalone HTML file; a site's preview page
├── runtime.js             # the player: state machine, drivers, symbols
└── site.config.mjs        # Vite config that builds a React site to work inside a folder
protos/                    # source prototypes, read-only — local only, not published
├── show/                  # .prd files and sites the player lists
└── hide/                  # .prd files and sites generated but left off the list
out/
├── show/                  # generated from protos/show/ — rebuilt by the converter, published
│   └── {site}/            # a site: index.html is its preview, app/ the site itself
├── hide/                  # generated from protos/hide/ — rebuilt by the converter, published
└── html-conversions/      # written by hand, nothing regenerates them — published
    └── ra-prototype-set/  # a set of related prototypes; each has its own folder,
                           # holding index.html and its own copy of the course outline
```

## Source Formats

`protos/` holds the source prototypes. `.prd` is the current focus.

- **`.prd` — Principle (macOS).** 15 files. An Apple binary property list written by `NSKeyedArchiver`, holding an object graph of `PRPrototype`, `PRScreen`, `PRLayer`, `PRImage`, `PRLink` and `PRKeyframe`. Structured data, not compiled web code — so conversion is translation, not decompilation.
- **`.pie` — ProtoPie.** 7 files. Encrypted; not convertible.
- **`.framer` — Framer Classic.** One folder. Empty; nothing to convert.
- **React site.** A folder holding a `package.json`, built with Vite. The site's files are never edited; `site.config.mjs` moves its page addresses into the hash (`#/alt`), so a reload or shared link works on a static server, and puts the site's folder in front of addresses that point at its `public/` files.
- **Plain site.** A folder holding an `index.html` and no `package.json`. Copied without its `.md` files; addresses that named one of its files from the server's root, and links to the root itself, get the site's folder in front.

Each site gets a preview page like the hand-made ones: the site in a desktop window that fills the room, with the panel and copy embed control beside it. Its name and description come from the first heading and first sentence of its `prototype-summary.md`, or its folder name.

The first three are documented locally in `docs/tech/other-formats.md`, which is not published.

## Terminology

- **Screen**: a `PRScreen` — one artboard the prototype can display.
- **Layer**: a `PRLayer` — a nestable visual element on a screen.
- **Link**: a `PRLink` — a transition from one screen to another, triggered by an interaction.
- **Keyframe**: a `PRKeyframe` — an animated property value, driving motion within a screen.
- **Player**: the generated web page that renders a converted prototype.

## How Things Work Here

- Fidelity is judged against how the prototype looked and behaved in its original tool's preview.
- Prototypes in `protos/` are the archive and are never modified. Conversion only reads them.
- `protos/` is the record of what exists. Each sync converts or builds both folders, deletes any page whose source is gone from its folder, and rebuilds the list. Moving a source between `show/` and `hide/` moves its page; deleting the source deletes its page.
- A hidden page is left off the list, but it is still published at its own web address.
- A prototype with no links and no keyframes is still valid — it renders as a still.
- Every page carries its own copy of the styles and scripts it needs, so the hand-written pages repeat each other almost line for line. That duplication is the price of a page that works anywhere with no assets beside it, and it is deliberate.

## Workflow: Rocket-Ship

Work is feature-driven and iterative. `/plan-feature` moves the next backlog item into CURRENT-FEATURE, scopes it with acceptance criteria, and produces a spec. `/start-work-session` builds iteratively with tournament-style sub-agents, and `/end-work-session` closes the session and writes the hand-off — run the pair once per session until the feature is done. `/ship-feature` verifies ACs, runs audit and documentation, generates changelogs, and merges.
