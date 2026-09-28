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
- **Version**: `MAJOR.MINOR` (e.g. `1.0`, `1.1`). Create a new folder for each release instead of modifying a published one.

## What a version should include

- `README.md` with prerequisites, deployment steps, validation and cleanup.
- Deployment artifacts (Helm values, manifests, scripts) as needed.
- Declared compatibility: SUSE AI Factory version, with/without NVIDIA, tested hardware.

## Partners

| Partner | Blueprints |
|---------|------------|
| [example.com](example.com) | [my-awesome-blueprint](example.com/my-awesome-blueprint) |
