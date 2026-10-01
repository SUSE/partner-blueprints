#!/usr/bin/env python3
"""Validate partner blueprints and (re)generate the aggregate root catalog.

Subcommands:
  validate            Check every Blueprint CR under partners/ and example/.
  gen                 Rewrite catalog.yaml's membership from partners/**.
  gen --check         Fail (non-zero) if catalog.yaml is stale, changing nothing.

A Blueprint file must live at  partners/<partner>/blueprints/<name>-<version>.yaml
and carry matching labels (see check_file). The example/ tree is validated the
same way but is never added to the aggregate catalog.

Output is deterministic (sorted membership) so the CI drift check is stable; if a
partner ever needs custom key ordering in catalog.yaml, template it here instead.
"""
import argparse
import glob
import os
import re
import sys
from urllib.parse import urlsplit

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_FILE = os.path.join(ROOT, "catalog.yaml")

NAME_LABEL = "ai-factory.suse.com/blueprint-name"
VERSION_LABEL = "ai-factory.suse.com/blueprint-version"
CATEGORY_LABEL = "ai-factory.suse.com/category"

# Partner blueprints always declare source Partner, so a submission cannot claim
# SUSE or Nvidia provenance. Needs an operator whose CRD includes Partner.
PARTNER_SOURCE = "Partner"

# spec.icon rules. The CRD enforces the scheme, raster types and size; the host
# rules mirror the SUSE AI Factory UI (browserSafeBlueprintIcon), which silently
# skips icons pointing at IP addresses or internal names. Checking here tells
# the partner at PR time instead of shipping a logo that never renders.
ICON_MAX_LENGTH = 16384
DATA_ICON = re.compile(r"^data:image/(png|gif|jpeg|webp);base64,[A-Za-z0-9+/=]+$")
HTTPS_ICON = re.compile(r"^https://[^\s\"'<>/][^\s\"'<>]*$")
DNS_HOST = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")
NUMERIC_LABEL = re.compile(r"^(\d+|0x[0-9a-f]*)$")
PRIVATE_HOST_SUFFIX = re.compile(r"\.(localhost|local|internal|svc)$")

# Static header of the aggregate catalog. Edit branding here — the blueprints
# list and categories below are generated from the partner folders.
CATALOG_HEADER = {
    "apiVersion": "ai-factory.suse.com/v1alpha1",
    "kind": "BlueprintCatalog",
    "metadata": {"name": "partner-catalog"},
    "spec": {
        "displayName": "Partner Blueprints",
        "description": "Community and partner-contributed blueprints for SUSE AI Factory.",
    },
}


# partners/<partner>/blueprints/*.yaml ; the example is one partner folder's worth
# at example/blueprints/*.yaml (copy example/ -> partners/<partner>/ to onboard).
GLOBS = {
    "partners": os.path.join(ROOT, "partners", "*", "blueprints", "*.yaml"),
    "example": os.path.join(ROOT, "example", "blueprints", "*.yaml"),
}


def blueprint_files(root_dir):
    """All blueprint *.yaml under root_dir, sorted for determinism."""
    return sorted(glob.glob(GLOBS[root_dir]))


def load(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def partner_of(path):
    """partners/acme/blueprints/x.yaml -> acme ; example/blueprints/x.yaml -> example"""
    parts = os.path.relpath(path, ROOT).replace("\\", "/").split("/")
    return parts[1] if parts[0] == "partners" else parts[0]


def icon_errors(icon):
    """Return errors for an optional spec.icon value (empty list if valid)."""
    if icon is None:
        return []
    if not isinstance(icon, str) or not icon:
        return ["spec.icon must be a non-empty string when set"]
    if len(icon) > ICON_MAX_LENGTH:
        return [f"spec.icon is {len(icon)} characters; the limit is {ICON_MAX_LENGTH}"]
    if icon.startswith("data:"):
        if DATA_ICON.match(icon):
            return []
        return ["spec.icon data: URI must be base64 png, gif, jpeg or webp "
                "(data:image/<type>;base64,...); SVG is not allowed"]
    if not HTTPS_ICON.match(icon):
        return ["spec.icon must be an https:// URL or a base64 raster data: URI "
                "(http:// is not allowed)"]
    try:
        host = (urlsplit(icon).hostname or "").rstrip(".")
    except ValueError:
        host = ""
    # Plain ASCII DNS names only: the browser would decode percent-encoding,
    # IDN and full-width dots before resolving, so allowing them hides the real host.
    if not DNS_HOST.match(host):
        return ["spec.icon must use a public DNS hostname (no IP address, "
                "single-label, percent-encoded or non-ASCII host)"]
    if NUMERIC_LABEL.match(host.rsplit(".", 1)[-1]):
        return ["spec.icon must use a public DNS hostname, not an IP address"]
    if PRIVATE_HOST_SUFFIX.search(host):
        return ["spec.icon must not point at an internal hostname "
                "(.localhost, .local, .internal, .svc)"]
    return []


def check_file(path):
    """Return (info, errors) for one blueprint file. info is None on hard failure."""
    errors = []
    try:
        doc = load(path)
    except yaml.YAMLError as exc:
        return None, [f"invalid YAML: {exc}"]
    if not isinstance(doc, dict):
        return None, ["not a YAML mapping"]

    if doc.get("kind") != "Blueprint":
        return None, [f"kind must be 'Blueprint', got {doc.get('kind')!r}"]
    if doc.get("apiVersion") != "ai-factory.suse.com/v1alpha1":
        errors.append(f"apiVersion must be ai-factory.suse.com/v1alpha1, got {doc.get('apiVersion')!r}")

    meta = doc.get("metadata") or {}
    labels = meta.get("labels") or {}
    name = labels.get(NAME_LABEL)
    version = labels.get(VERSION_LABEL)
    if not name:
        errors.append(f"missing label {NAME_LABEL}")
    if not version:
        errors.append(f"missing label {VERSION_LABEL}")

    # filename must be <name>-<version>.yaml
    stem = os.path.splitext(os.path.basename(path))[0]
    if name and version and stem != f"{name}-{version}":
        errors.append(f"filename should be '{name}-{version}.yaml', got '{stem}.yaml'")

    # metadata.name slug convention: dots in version become dashes
    if name and version:
        want = f"{name}-{version}".replace(".", "-")
        if meta.get("name") != want:
            errors.append(f"metadata.name should be '{want}', got {meta.get('name')!r}")

    spec = doc.get("spec") or {}
    if version and spec.get("version") != version:
        errors.append(f"spec.version should match label ({version}), got {spec.get('version')!r}")
    for field in ("displayName", "description", "components", "source"):
        if not spec.get(field):
            errors.append(f"spec.{field} is required")
    if spec.get("source") and spec.get("source") != PARTNER_SOURCE:
        errors.append(f"spec.source must be '{PARTNER_SOURCE}', got {spec.get('source')!r}")
    errors.extend(icon_errors(spec.get("icon")))

    info = {
        "name": name,
        "version": version,
        "partner": partner_of(path),
        "category": labels.get(CATEGORY_LABEL),
    }
    return info, errors


def validate():
    """Validate partners/ and example/. Returns (ok, summary_markdown)."""
    problems = {}  # path -> [errors]
    infos = []  # (path, info)
    for root_dir in ("partners", "example"):
        for path in blueprint_files(root_dir):
            info, errs = check_file(path)
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            if errs:
                problems[rel] = errs
            if info:
                infos.append((rel, info))

    # cross-file: unique (name, version); a name owned by one partner only
    seen_nv = {}
    owner = {}
    for rel, info in infos:
        name, version, partner = info["name"], info["version"], info["partner"]
        if not name or not version:
            continue
        nv = (name, version)
        if nv in seen_nv:
            problems.setdefault(rel, []).append(
                f"duplicate blueprint {name} {version} (also in {seen_nv[nv]})")
        else:
            seen_nv[nv] = rel
        # example/ is exempt from cross-partner ownership
        if rel.startswith("partners/"):
            if name in owner and owner[name] != partner:
                problems.setdefault(rel, []).append(
                    f"blueprint-name '{name}' already owned by partner '{owner[name]}'")
            else:
                owner[name] = partner

    ok = not problems
    lines = []
    if ok:
        lines.append(f"✅ {len(infos)} blueprint(s) valid.")
    else:
        lines.append(f"❌ {len(problems)} file(s) with problems:")
        for rel in sorted(problems):
            lines.append(f"\n**{rel}**")
            for e in problems[rel]:
                lines.append(f"- {e}")
    return ok, "\n".join(lines)


def build_catalog():
    """Aggregate BlueprintCatalog dict, membership derived from partners/."""
    members = {}  # name -> category (or None)
    categories = set()
    for path in blueprint_files("partners"):
        info, errs = check_file(path)
        if errs or not info or not info["name"]:
            continue
        members[info["name"]] = info["category"]
        if info["category"]:
            categories.add(info["category"])

    doc = {
        "apiVersion": CATALOG_HEADER["apiVersion"],
        "kind": CATALOG_HEADER["kind"],
        "metadata": dict(CATALOG_HEADER["metadata"]),
        "spec": dict(CATALOG_HEADER["spec"]),
    }
    if categories:
        doc["spec"]["categories"] = sorted(categories)
    doc["spec"]["blueprints"] = [
        ({"name": n, "category": members[n]} if members[n] else {"name": n})
        for n in sorted(members)
    ]
    return doc


def dump_catalog(doc):
    header = (
        "# GENERATED FILE - do not edit the blueprints list by hand.\n"
        "# Regenerate with: python scripts/catalog.py gen\n"
    )
    return header + yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)


def gen(check_only):
    text = dump_catalog(build_catalog())
    if check_only:
        current = ""
        if os.path.exists(CATALOG_FILE):
            with open(CATALOG_FILE, encoding="utf-8") as fh:
                current = fh.read()
        if current != text:
            print("❌ catalog.yaml is stale. Run: python scripts/catalog.py gen", file=sys.stderr)
            return False
        print("✅ catalog.yaml is up to date.")
        return True
    with open(CATALOG_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"Wrote {CATALOG_FILE}")
    return True


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # emoji-safe on Windows consoles
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    g = sub.add_parser("gen")
    g.add_argument("--check", action="store_true", help="fail if catalog.yaml is stale")
    ap.add_argument("--summary", help="write the markdown summary to this file")
    args = ap.parse_args()

    if args.cmd == "validate":
        ok, summary = validate()
        print(summary)
        if args.summary:
            with open(args.summary, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(summary)
        sys.exit(0 if ok else 1)
    else:
        sys.exit(0 if gen(args.check) else 1)


if __name__ == "__main__":
    main()
