# Tensormesh blueprints for SUSE AI Factory

Tensormesh maintains one blueprint in this folder. It runs the SUSE AI open vLLM
serving stack (serving engine + router) with **Tensormesh Platform's KV cache**
enabled, so repeated prompt context is served from cache instead of recomputed on
the GPU.

| Blueprint | What it installs |
|---|---|
| Tensormesh Platform on SUSE AI (vLLM) (`tensormesh-suse-ai`) | The SUSE Application Collection `vllm-stack` chart (vLLM serving engine + router) plus the Tensormesh Platform cache (an `LMCacheEngine` + coordinator). The vLLM pod is wired to the cache directly in Helm values — no admission webhook — by appending `--kv-transfer-config` and reading its value from the engine's connection ConfigMap |

## Before you install

- **SUSE AI Factory** with `aif-operator` able to render partner blueprints. On a
  release that supports partner catalogs, add this catalog in AI Factory
  **Settings > Blueprint Catalogs > Add Catalog**: Repository URL
  `https://github.com/SUSE/partner-blueprints.git`, Branch `main`, Paths
  `partners`.
- **A SUSE AI subscription**, with Application Collection access configured in AI
  Factory. The vLLM serving stack (`vllm-stack`) and its image come from the
  Application Collection.
- **A GPU node** with the NVIDIA GPU Operator / device plugin, and a default
  `StorageClass` for the model PVC.
- **A `RuntimeClass` named `nvidia`.** The SUSE AI Factory GPU operator may create
  `nvidia-experimental` instead; add an `nvidia` RuntimeClass pointing at the same
  containerd handler, or the engine is rejected.
- **The workload namespace labelled** `pod-security.kubernetes.io/enforce=privileged`
  — the engine runs privileged with a `/dev/shm` mount for cross-process CUDA IPC.
- **Tier-1 prerequisite:** the Tensormesh Platform operator + webhook + CRDs
  installed once, cluster-wide, in their own namespace, with the engine disabled.
  The webhook does not mutate pods in its own namespace, so the operator cannot
  live in the workload namespace; this blueprint does not use the webhook, but the
  operator reconciles the `LMCacheEngine` CR it creates.
- **Two chart sources, registered as Rancher ClusterRepos:**
  - The SUSE Application Collection, with pull credentials.
  - A `tensormesh` ClusterRepo for the `tensormesh-platform` chart — see below.

## The `tensormesh` ClusterRepo

The `tensormesh-platform` chart is served from the Tensormesh distribution gateway
at `artifacts.tensormesh.ai`. A blueprint cannot add a repository to AI Factory, so
register it once per cluster, named `tensormesh`.

> **Use the charts _namespace_ URL, not the chart path.** The deployer builds the
> pull URL as `<ClusterRepo URL>/<chart name>`, so the URL must end at `.../charts`:
>
> ```
> oci://artifacts.tensormesh.ai/tensormesh-production/charts
> ```
>
> A chart-level URL (`.../charts/tensormesh-platform`) resolves to a doubled,
> non-existent path and fails with "repository not found".

The ClusterRepo authenticates with your Tensormesh registry token via a basic-auth
`clientSecret` (username `_token`, password `<token>`) in `cattle-system`.

## The Tensormesh registry token

The operator, coordinator and CacheBlend images are **private** on
`artifacts.tensormesh.ai` and are pulled with your Tensormesh registry token (the
engine/serving image is the public open-source `lmcache/vllm-openai`). The chart
enforces, at render time, that a pull credential is present in the Helm values.

Pre-create a `docker-registry` Secret named **`tensormesh-gateway-pull`** in the
workload namespace; the blueprint references it on the coordinator:

```shell
kubectl -n <workload-namespace> create secret docker-registry tensormesh-gateway-pull \
  --docker-server=artifacts.tensormesh.ai \
  --docker-username=_token \
  --docker-password=<your-tensormesh-token>
```

The Tier-1 operator install needs the same token (its image is private too); pass
it there with the chart's `imagePullSecret.password`.

| | Pre-created Secret (this blueprint) | `imagePullSecret.password` |
|---|---|---|
| You | Create `tensormesh-gateway-pull` as above; the blueprint lists it in `coordinator.spec.imagePullSecrets` | Set `imagePullSecret.password: <token>` and the chart creates + wires the Secret itself |
| The token sits | In the Secret | In the Helm values / AIWorkload |
| Good for | Keeping the token out of the workload spec | A quick single install |

## Install

1. Register the `tensormesh` ClusterRepo (namespace URL + token clientSecret) and
   ensure the Application Collection ClusterRepo is present.
2. Create the `tensormesh-gateway-pull` Secret in the target namespace.
3. Install the Tier-1 Tensormesh Platform operator (engine disabled) if not already
   present.
4. In AI Factory: **Blueprints > Tensormesh Platform on SUSE AI (vLLM) > Install**.
   Set the target namespace (PSS-privileged) and deploy. AI Factory installs both
   components from their ClusterRepos.

## Verify the cache

Send the same long prompt to the model twice (temperature 0). The warm repeat is
served from cache: the engine logs `Stored <N> tokens` on the first request and
`Retrieved <N> tokens` on the second, and vLLM reports a non-zero external prefix
cache hit rate.

## Support

This is a community / integration blueprint, not a SUSE-supported product. For
assistance or to report issues, contact Tensormesh at **huyn@tensormesh.ai**.
