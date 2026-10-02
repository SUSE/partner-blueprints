# SUSE AI Factory — Partner Blueprints

A single catalog repository hosting **partner-contributed blueprints** for
[SUSE AI Factory](https://github.com/SUSE/aif). Each partner curates their own
folder; SUSE AI Factory syncs the whole repo into a cluster via Fleet.

A **Blueprint** is a `kind: Blueprint` custom resource
(`ai-factory.suse.com/v1alpha1`) describing an AI workload as a set of Helm
components and their values. This repo also publishes an aggregate
[`partners/catalog.yaml`](partners/catalog.yaml) — a `BlueprintCatalog` CR listing every partner
blueprint. Its blueprints list is **generated** by `scripts/catalog.py gen`, not
hand-edited: contributors regenerate it and commit it with their blueprint, and
CI fails the PR if it's stale.

## Repository layout

```
partner-blueprints/
├── partners/                 # one folder per partner
│   ├── catalog.yaml          # aggregate BlueprintCatalog CR (run `catalog.py gen`; CI checks it)
│   └── <partner>/blueprints/<name>-<version>.yaml
├── example/                  # a working template (validated, not published)
├── scripts/                  # validation + catalog generation
└── .github/workflows/        # the PR validation gate
```

## How SUSE AI Factory consumes this repo

The operator adds an external catalog at runtime through its Helm values —
one entry becomes one Fleet `GitRepo` that applies the CRs in this repo:

```yaml
# aif-operator values.yaml
blueprintCatalogs:
  - name: partner-blueprints
    repoURL: https://github.com/<org>/partner-blueprints.git
    branch: main
    paths: [partners]
```

Fleet applies every `Blueprint` under `partners/**` plus the aggregate
`BlueprintCatalog`, and garbage-collects anything removed from the repo.

Partner blueprints use `spec.source: Partner` and may set an optional
`spec.icon`. Both need an aif-operator whose Blueprint CRD includes them;
older operators (2.2.0 and earlier) reject `source: Partner`, so Fleet cannot
apply these blueprints on those clusters.

## Contributing a blueprint

1. Read [CONTRIBUTING.md](CONTRIBUTING.md).
2. Copy [`example/`](example/) to `partners/<your-partner>/`.
3. Open a pull request. CI validates schema + conventions; a SUSE maintainer
   and your team review before merge.

## Validation locally

```bash
python scripts/catalog.py validate     # schema/convention checks
python scripts/catalog.py gen          # regenerate partners/catalog.yaml
```

## License

[Apache License 2.0](LICENSE).
