# Example partner

This folder shows the exact shape a partner submission takes. It is **not** a
real partner and is excluded from the aggregate `partners/catalog.yaml`, but CI validates
it with the same rules, so it always stays correct.

```
example/
└── blueprints/
    └── example-chatbot-1.0.0.yaml   # one kind: Blueprint per file
```

To onboard, copy this layout to `partners/<your-partner>/` and open a pull
request. See [CONTRIBUTING.md](../CONTRIBUTING.md).
