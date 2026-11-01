# FreedomNAS Module Template

Starting point for a new FreedomNAS module. Clone **only this repo** — not
`freedomnas-core` — to build a module; this is the whole point of the
manifest-driven module system: a module is discovered by directory scan at
runtime, so nothing here needs to live inside `freedomnas-core`.

A "module" is a background component with a health check (ZFS pool
monitoring, share service monitoring, ...), registered with `freedomnas-core`'s
`Orchestrator`. A **community module** additionally exposes a WebUI page and
API — that's everything under `modules/example/frontend/` and
`api_routes.py.example` in this repo. If your module has no WebUI, delete
those and set `"webui": null` in `manifest.json` (see `modules/storage` in
`freedomnas-core` for what a WebUI-less core module's manifest looks like).

## Directory structure

```
freedomnas-module-template/
├── modules/example/                  ← code, installed to /usr/lib/freedomnas/modules/example/
│   ├── __init__.py                     exports the module class
│   ├── module.py                       implements FreedomNASModule (start/stop/health_check/reconcile)
│   ├── manifest.json                   discovery metadata — see field reference below
│   ├── api_routes.py.example           WebUI-only: JSON API endpoints
│   └── frontend/                       WebUI-only
│       ├── templates/example.html.example
│       └── static/                      mounted at /static/modules/example/
│           ├── icons.svg                   sidebar icon (an SVG <symbol>)
│           └── js/example.js.example
├── profiles/example/                 ← OS command fragments, installed to /usr/lib/freedomnas/profiles/example/
│   └── example-debian.json             one file per supported OS
├── debian/                            .deb packaging (control/rules/changelog)
├── PKGBUILD                           Arch packaging
└── README.md                          this file
```

## 1. Rename everything

| Placeholder            | Appears in                                              | Replace with |
|-------------------------|---------------------------------------------------------|--------------|
| `example`               | directory names, `manifest.json`'s `"id"`, `route_prefix`, `page_route`, package names | your module's id (kebab/snake-case) |
| `ExampleModule`         | `module.py`, `__init__.py`, `manifest.json`'s `"entry_point"` | `YourModuleModule` |
| `Example` / "Example"   | docstrings, `manifest.json`'s `"name"`, page titles      | your module's display name |
| `freedomnas-module-example` | `debian/control`, `debian/rules`, `PKGBUILD`         | `freedomnas-module-<your-id>` |

## 2. `module.py` — the module contract

Implement `FreedomNASModule` (from `freedomnas.orchestrator`, provided by the
`freedomnas-core` dependency):

- `name` (property) — must match `manifest.json`'s `"id"`.
- `start()` — called once when the Orchestrator (re)starts the module. Must
  be idempotent.
- `stop()` — called on shutdown. Must be idempotent.
- `health_check()` — called every ~30s by the heartbeat thread. Must never
  raise (catch everything internally); return `False` on failure. After 5
  consecutive failures the Orchestrator's circuit breaker disables the
  module.
- `reconcile(desired, mode)` — optional. Called by the reconciler at every
  boot and when a configuration is restored, after pools, users and shares,
  with this module's own section of `config.yaml` (`modules.<id>`). It
  brings what the module manages back to that section and returns the
  reconciler's `ActionResult`s; in `"additive"` mode it removes nothing.
  Keep the base class's default (nothing to do) if the module stores
  nothing.
- `prepare(desired)` — optional. Called by the installer inside the chroot of
  the system it installs, when it restores a configuration that has this
  module's section: install the packages the module needs and nothing else
  (no service, no pool); the first boot's reconcile does the rest.
- `links()` — optional. The module's web pages every account of the NAS may
  open, listed on the WebUI's account page: dicts with `"name"`, `"title"`
  and one of `"path"`, `"url"`, or `"scheme"` + `"port"`.

### The module's configuration

Every module has its own section of `config.yaml`, `modules.<id>`, read
with `self._config.get_module_config("<id>")` and replaced with
`set_module_config("<id>", section)`. It travels with the rest of the
configuration (the `.freedomnas` dataset), so `reconcile()` can rebuild
the module's state on a reinstalled box or on another edition. As in the
core, every change is a dual write: the engine call that changes the
system first, then the configuration.

**Golden rule**: never hardcode an OS-native command in Python. Always go
through `self._engine.execute()` / `get_command()` / `get_profile_value()` —
that's what resolves the right command from your `profiles/example/` fragment
for the OS actually running, without an `if os == "debian"` in sight.

## 3. `manifest.json` — field reference

```json
{
  "id": "example",
  "name": "Example",
  "version": "1.0.0",
  "type": "community",
  "description": "...",
  "entry_point": "module:ExampleModule",
  "supported_os": ["debian"],
  "depends_on": [],
  "after": [],
  "webui": { ... or null }
}
```

- **id** — unique, matches the containing directory name and `profiles/<id>/`.
  Community modules are installed to `<root>/modules/` and the core's own
  modules sit inside the core; both are loaded, and a community module that
  takes the id of a core one (`storage`, `network`, `shares`, `users`,
  `updates`) is ignored.
- **type** — `"community"` for a module like this one (own repo/package);
  `"core"` is reserved for the modules that ship inside `freedomnas-core`
  itself.
- **entry_point** — `"<file_stem>:<ClassName>"`. `freedomnas-core`'s
  `ModuleLoader` loads `{module_dir}/{file_stem}.py` **by file path**, not
  through Python's package import machinery — that's exactly what lets this
  module live in its own repo instead of being an importable subpackage of
  `freedomnas-core`.
- **supported_os** — module (and its `profiles/<id>/<id>-<os>.json` fragment)
  is silently skipped on any OS not listed here. Start with what you can
  actually test; add more once you've verified them.
- **depends_on** — other module ids this one requires (informational for now
  — nothing enforces it yet).
- **after** — optional: module ids whose reconcile must run before this
  one's when they are installed (e.g. `"after": ["proxy"]` in
  freedomnas-containers, so Caddy is there before the apps' sites are
  written). A module that is not installed is ignored.
- **webui** — `null` for a module with no WebUI. Otherwise:
  - **api_routes** — filename of your FastAPI router file (e.g. `"api_routes.py"`).
  - **route_prefix** — where its endpoints are mounted (e.g. `/api/example`).
  - **router_attr** — the router variable's name inside `api_routes.py` (usually `"router"`).
  - **templates_dir** / **static_dir** — relative paths, added to the WebUI's
    template search path / mounted at `/static/modules/<id>/`.
  - **page_route** / **page_template** — if set, freedomnas-webui registers a
    page at `page_route` that renders `page_template` (which must live under
    `templates_dir`). Omit both if your module is API-only (embedded into an
    existing core page, say) with no page of its own.
  - **nav** — the page's sidebar entry, placed before System:
    `{"label": "Example", "icon": "icons.svg#example", "level": "advanced"}`.
    `icon` is `<file>#<symbol id>` inside `static_dir` (without it a generic
    module icon is shown); `level` is the lowest UI level that shows the
    entry: `assisted` (default), `advanced` or `expert`. Leave `nav` out and
    the page is reachable only by its address.

## 4. `profiles/example/example-<os>.json` — OS command fragment

One file per OS you support, containing only the category key(s) *your*
module owns (don't duplicate `os_name`, `packages`, `system`, etc. — those
live in `freedomnas-profiles`' `os/` and are already loaded for every
module). `freedomnas-core`'s engine merges this in automatically at startup
by scanning every profile subdirectory next to `os/`, `init/`, and
`packages/` — no code change needed anywhere else. See
`freedomnas-profiles`' README ("How the Core Engine Uses Profiles") for the
full merge algorithm, and any of its `storage/`, `network/`, `shares/`,
`users/` fragments for real examples.

At runtime the engine scans one single directory (`/usr/lib/freedomnas/profiles/`)
that every package — `freedomnas-profiles` and every community module's own
`.deb`/`PKGBUILD` — drops its subdirectory into. `profiles/example/` in
*this* repo only exists so the packaging scripts have something to copy;
it must land as a sibling of `os/`, `init/`, `storage/`, etc. at install
time, not nested inside this module's own install path.

## 5. Adding a WebUI page (community modules only)

1. Rename `api_routes.py.example` → `api_routes.py` and replace its example
   endpoint with your real ones. It runs inside the WebUI process, so it can
   `from api.deps import authenticate, get_engine, get_config` exactly like
   `freedomnas-webui`'s own route files.
2. Rename `frontend/templates/example.html.example` → `example.html` (or
   whatever `page_template` says) — it extends `base.html` from
   `freedomnas-webui`, so nav/layout/theme come for free.
3. Rename `frontend/static/js/example.js.example` → `example.js`, referenced
   from the template as `/static/modules/<id>/js/example.js`, and draw your
   sidebar icon in `frontend/static/icons.svg`.
4. That's it — `freedomnas-webui`'s `api/module_discovery.py` scans
   `modules/*/manifest.json` at startup and mounts anything with a `webui`
   block. Nothing in `freedomnas-webui` itself needs editing.

## 6. Local testing before packaging

Point an existing `freedomnas-core` checkout's module loader at this repo's
`modules/` directly — no install needed. The profile fragment is separate:
copy (or symlink) this repo's `profiles/example/` into a **copy** of the
`freedomnas-profiles` checkout first, so it sits as a sibling of `os/`,
`init/`, etc. exactly like a real install would merge it in (see the note in
section 4):

```bash
# from a freedomnas-core checkout, with this repo and freedomnas-profiles as sibling directories
cp -r ../freedomnas-module-template/profiles/example ../freedomnas-profiles/example

python -c "
from module_loader import ModuleLoader
from engine import FreedomNASEngine
from config import ConfigurationManager
from orchestrator import Orchestrator

engine = FreedomNASEngine(profile_dir='../freedomnas-profiles', os_override='debian')
config = ConfigurationManager(config_path='/tmp/test-config.yaml')
orch = Orchestrator(engine, config)
loader = ModuleLoader(engine, config, modules_dir='../freedomnas-module-template/modules')
print(loader.load_all(orch))
"

# remove the copy once you're done testing — don't commit it into freedomnas-profiles
rm -rf ../freedomnas-profiles/example
```

For the WebUI side, run `freedomnas-webui` with
`api.module_discovery.discover_community_modules(modules_dir="../freedomnas-module-template/modules")`
(temporarily, for testing — the real install path is
`/usr/lib/freedomnas/modules`) and confirm your page/API/static assets are
reachable.

Also run your OS's command by hand once (the exact string
`engine.get_command("category", "action", ...)` produces) before trusting
`health_check()` — the engine won't validate that a command actually does
what you think.

## 7. Packaging

The compat level is `debhelper-compat (= 13)` in `debian/control`; a
`debian/compat` file beside it makes debhelper stop with "compat level
specified both". A module needs freedomnas-core and freedomnas-webui newer
than 0.9.12 (`freedomnas-core (>> 0.9.12)`): 0.9.12 loads only one modules
directory, so a community module would hide the core ones.

`debian/` and `PKGBUILD` both do the same three things: copy
`modules/example/` to `/usr/lib/freedomnas/modules/example/`, copy
`profiles/example/` to `/usr/lib/freedomnas/profiles/example/`, and delete
any leftover `*.example` placeholder files. Rename the package
(`freedomnas-module-example` → `freedomnas-module-<your-id>`) in
`debian/control`, `debian/rules`, `debian/changelog`, and `PKGBUILD`, then
build the same way `freedomnas-profiles` does (see its README/CONTRIBUTING).

Keep the name exactly `freedomnas-module-<your-id>`, with `<your-id>` the
`id` in `manifest.json` (an ebuild goes in `app-nas/`): the WebUI's Plugins
page finds modules by that name in the edition's package repository, lists
them with the package's short description (`Description:` first line in
`debian/control`, `pkgdesc` in `PKGBUILD`), and installs or removes them from
there. Write that description as one clear sentence about what the module
adds.
