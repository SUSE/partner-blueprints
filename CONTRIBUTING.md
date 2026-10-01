# Contributing

Blueprints are contributed by partners via pull request. This repo hosts many
partners; you only ever touch your own `partners/<partner>/` folder.

## Onboarding a new partner

1. **You (partner):** open an onboarding issue using the *Partner onboarding*
   template with your folder slug and a maintainer contact.
2. **SUSE maintainers:** acknowledge the issue and reserve your `partners/<slug>/`
   folder name.
3. **You (partner):** open your first blueprint PR (below). SUSE maintainers
   review and merge every PR.

## Adding or updating a blueprint

1. Copy [`example/blueprints/example-chatbot-1.0.0.yaml`](example/blueprints/example-chatbot-1.0.0.yaml)
   into `partners/<partner>/blueprints/`.
2. Rename it to `<blueprint-name>-<version>.yaml` and edit the CR.
3. Run the checks locally before pushing:
   ```bash
   python scripts/catalog.py validate
   python scripts/catalog.py gen          # updates catalog.yaml
   ```
4. Commit **both** your blueprint and the regenerated `catalog.yaml`, then open
   a PR.

## Rules CI enforces

| Rule | Why |
|------|-----|
| `kind: Blueprint`, `apiVersion: ai-factory.suse.com/v1alpha1` | It's a Blueprint CR |
| filename = `<blueprint-name>-<version>.yaml` | predictable layout |
| `metadata.name` = `<name>-<version>` with dots→dashes | operator slug convention |
| labels `blueprint-name` / `blueprint-version` match filename & `spec.version` | no drift |
| `spec.source: Partner` | partner blueprints are labelled Partner, never SUSE or Nvidia |
| optional `spec.icon`: `https://` URL on a public DNS hostname, or a base64 `png`/`gif`/`jpeg`/`webp` `data:` URI, max 16384 characters (no `http://`, SVG, IP addresses or internal hostnames) | the UI only renders icons that meet these rules |
| required: `displayName`, `description`, `components` | usable catalog entry |
| the CR validates against the live Blueprint CRD schema | valid on the cluster |
| a `blueprint-name` is owned by exactly one partner | no cross-partner collisions |
| `catalog.yaml` is regenerated (not stale) | aggregate never drifts |

## Review

Opening a PR automatically:

- runs the validation gate (all checks above),
- labels the PR by partner folder,
- posts a validation summary comment,
- requests SUSE maintainer review (via `CODEOWNERS`).

A SUSE maintainer merges once checks pass and reviews approve.

## Writing good blueprints

- Pin chart versions and image tags — reproducibility matters in air-gapped installs.
- Put prerequisites (StorageClass, cert-manager, GPUs), exposed endpoints, and
  any model/licensing notes in `spec.description`.
- For `spec.icon`, prefer a small `data:` URI (a 64×64 PNG or WebP is plenty):
  it renders in air-gapped clusters, where an `https://` logo cannot load. Keep
  it inline in the blueprint; don't commit image files under `partners/`,
  since Fleet ships everything under that path to every cluster.
- Prefer stable in-cluster service names (`fullnameOverride`) over release-name
  coupling, so a blueprint installs under any namespace.
