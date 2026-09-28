# partner-blueprints

Partner blueprints for **SUSE AI Factory**.

A blueprint is a validated, reproducible recipe that shows how to deploy a partner solution (application, model, tooling, integration) on top of SUSE AI Factory. Blueprints cover both deployment flavors:

- **SUSE AI Factory with NVIDIA** — GPU-accelerated stacks (NVIDIA GPU Operator, NIM, etc.).
- **SUSE AI Factory without NVIDIA** — CPU-only or alternative accelerator stacks.

## Repository layout

```
blueprints/
├── catalog.yaml                  # BlueprintCatalog listing all blueprints
└── <partner>/                    # Partner name or domain (e.g. acme, example.com)
    ├── README.md                 # Partner overview
    └── <blueprint-name>/
        ├── README.md             # Blueprint overview, version index
        ├── 1.0.0/
        │   ├── README.md         # Version-specific docs
        │   └── <blueprint-name>-1-0-0.yaml  # Blueprint manifest
        └── 1.1.0/
            ├── README.md
            └── <blueprint-name>-1-1-0.yaml
```

See [`blueprints/README.md`](blueprints/README.md) for details and contribution guidelines.

## Contributing

1. Create a folder under `blueprints/` for your organization (if it doesn't exist).
2. Add a folder per blueprint, with one subfolder per version.
3. Add the `Blueprint` manifest to each version folder.
4. Register the blueprint in [`blueprints/catalog.yaml`](blueprints/catalog.yaml).
5. Fill in the READMEs following the example in [`blueprints/example.com`](blueprints/example.com).
6. Open a pull request.
