# Partners

Each partner owns one subfolder here. Blueprints live under
`partners/<partner>/blueprints/` as one `kind: Blueprint` file per version:

```
partners/
└── acme/
    └── blueprints/
        ├── acme-rag-1.0.0.yaml
        └── acme-rag-1.1.0.yaml
```

- A `blueprint-name` may only be owned by **one** partner folder (CI enforces this).
- Multiple versions of the same blueprint are fine — one file each.
- Every PR is reviewed and merged by SUSE maintainers.

See the top-level [`example/`](../example/) for a working template and
[`CONTRIBUTING.md`](../CONTRIBUTING.md) for the full flow.
