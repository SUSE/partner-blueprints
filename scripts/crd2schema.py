#!/usr/bin/env python3
"""Convert Blueprint/BlueprintCatalog CRDs into JSON schemas for kubeconform.

The schemas evolve in the operator repo, so CI fetches the live CRDs and runs
this instead of vendoring frozen copies. For each served version it writes
schemas/<kind lower>_<version>.json, which matches the kubeconform
-schema-location template used in the validate workflow.

Usage: python scripts/crd2schema.py OUTDIR crd1.yaml [crd2.yaml ...]
"""
import json
import os
import sys

import yaml


def main(argv):
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    outdir, crd_paths = argv[1], argv[2:]
    os.makedirs(outdir, exist_ok=True)
    written = 0
    for path in crd_paths:
        with open(path, encoding="utf-8") as fh:
            crd = yaml.safe_load(fh)
        if not crd or crd.get("kind") != "CustomResourceDefinition":
            print(f"skip {path}: not a CRD", file=sys.stderr)
            continue
        kind = crd["spec"]["names"]["kind"].lower()
        for ver in crd["spec"]["versions"]:
            if not ver.get("served", True):
                continue
            schema = ver["schema"]["openAPIV3Schema"]
            out = os.path.join(outdir, f"{kind}_{ver['name']}.json")
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(schema, fh, indent=2)
            written += 1
            print(f"wrote {out}")
    if not written:
        print("no schemas written", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
