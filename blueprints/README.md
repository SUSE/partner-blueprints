# Blueprints

Each top-level folder here belongs to one partner.

## Structure

| Level | Path | Purpose |
|-------|------|---------|
| Partner | `blueprints/<partner>/` | Partner name or domain. Holds partner info and all its blueprints. |
| Blueprint | `blueprints/<partner>/<blueprint>/` | One solution. README describes it and lists versions. |
| Version | `blueprints/<partner>/<blueprint>/<version>/` | Immutable, versioned deployment instructions and artifacts. |

## Naming conventions

- **Partner**: company name or domain, lowercase (e.g. `acme`, `example.com`).
- **Blueprint**: lowercase, hyphen-separated (e.g. `rag-chatbot`).
- **Version**: `MAJOR.MINOR.PATCH` (e.g. `1.0.0`, `1.1.0`). Create a new folder for each release instead of modifying a published one.

## Catalog

[`catalog.yaml`](catalog.yaml) is a `BlueprintCatalog` (`ai-factory.suse.com/v1alpha1`) listing every blueprint in this repository. Add one entry per blueprint version under `spec.blueprints`, with `name` (version dots replaced by dashes) and `file` (path relative to `catalog.yaml`):

```yaml
    - name: my-awesome-blueprint-1-1-0
      file: example.com/my-awesome-blueprint/1.1.0/my-awesome-blueprint-1-1-0.yaml
```

## What a version should include

- `<blueprint>-<X-Y-Z>.yaml` (e.g. `my-awesome-blueprint-1-1-0.yaml`): the `Blueprint` manifest (`ai-factory.suse.com/v1alpha1`).
- `README.md` with prerequisites, deployment steps, validation and cleanup.
- Extra artifacts (Helm values, scripts) as needed.
- Declared compatibility: SUSE AI Factory version, with/without NVIDIA, tested hardware.

## Partners

| Partner | Blueprints |
|---------|------------|
| [example.com](example.com) | [my-awesome-blueprint](example.com/my-awesome-blueprint) |
