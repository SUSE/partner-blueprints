# my-awesome-blueprint 1.0.0

## Compatibility

| Component | Version |
|-----------|---------|
| SUSE AI Factory | x.y |
| Kubernetes (RKE2) | x.y |
| NVIDIA GPU Operator | x.y (NVIDIA flavor only) |

**Tested hardware**: e.g. 2x NVIDIA L40S / CPU-only x86_64 nodes.

## Prerequisites

- Running SUSE AI Factory cluster.
- `kubectl` and `helm` access to the cluster.
- (NVIDIA flavor) GPU nodes with the NVIDIA GPU Operator installed.
- Partner-specific credentials or licenses, if any.

## Deployment

### With NVIDIA

```bash
helm install my-awesome-blueprint <chart> -f values-nvidia.yaml
```

### Without NVIDIA

```bash
helm install my-awesome-blueprint <chart> -f values-cpu.yaml
```

## Validation

Steps to confirm the deployment works (health checks, sample request, expected output).

## Cleanup

```bash
helm uninstall my-awesome-blueprint
```

## Changelog

- Initial release.
