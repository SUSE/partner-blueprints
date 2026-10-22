# AlchemiStudio

Partner blueprints for **AlchemiStudio** — an AI platform (agentic Copilot, AIOS
computer-use sandbox, and RAG) for SUSE AI Factory.

| Blueprint | What it deploys |
|---|---|
| [`alchemistudio-with-vllm`](blueprints/alchemistudio-with-vllm-0.1.0.yaml) | AlchemiStudio + in-cluster **vLLM** (Qwen2.5-3B-Instruct, open stack) as the Copilot model, plus a bundled CPU embedding server for RAG — fully self-hosted (no NGC / HuggingFace / cloud keys). |

## Prerequisites

- **SUSE AI Factory** (aif-operator) on a Rancher-managed RKE2 cluster.
- **An HTTP ClusterRepo for the Rancher partner charts** (`http-partner-charts`) — the
  `alchemistudio-platform` chart is pulled from it. Use the HTTP index, **not** Rancher's default
  git-backed `rancher-partner-charts`: the chart unpacks to more than Fleet's 1 MiB bundle
  limit, which only git-backed repos hit.

  ```bash
  kubectl apply -f - <<'EOF'
  apiVersion: catalog.cattle.io/v1
  kind: ClusterRepo
  metadata:
    name: http-partner-charts
  spec:
    url: https://partner-charts.rancher.io
  EOF
  ```

- **One free GPU** with ≥16 GB memory (e.g. NVIDIA T4) on a node with runtimeclass `nvidia`.
  vLLM claims a whole GPU (see step 1 below to check).
- **Kata is optional.** The blueprint sets `kata.enabled: false`, so the code sandbox and AIOS
  computer run as standard containers on any Linux node — a stock RKE2 cluster works. For
  production / multi-user installs, prepare a Kata node (KVM-capable, Kata runtime installed,
  labelled `kata=true` and tainted `pool=kata:NoSchedule`) and set `kata.enabled: true` to run
  user code in Kata micro-VMs.
- **Storage — three StorageClasses.** The names are set in the blueprint's component values;
  change them before registering the blueprint if your cluster has no Longhorn, or the data
  pods stay `Pending` on unbound PVCs.

  | Used for | Access mode | Blueprint value | Default |
  |---|---|---|---|
  | Postgres, Redis, SeaweedFS, etcd, OpenBao | ReadWriteOnce | `global.storageClass` | `longhorn` |
  | Shared AIOS / file data volume (mounted by several pods) | **ReadWriteMany** | `aios.dataPlane.storageClass` | `longhorn` |
  | vLLM model cache (GPU node, usually not a Longhorn node) | ReadWriteOnce | vllm `storageClass` | `local-path` |

  Longhorn RWX needs an NFS client on the nodes; any RWX-capable class (e.g. NFS) works.
- **cert-manager** for `tls.mode=acme` (Let's Encrypt), or your own cert with `tls.mode=byo`.
- **Egress** to `dp.apps.rancher.io`, `ghcr.io`, `huggingface.co` and `alchemiacr.azurecr.io`
  (mirror these for an air-gapped install).

## Install — step by step

1. **Check for a free GPU.**

   ```bash
   for node in $(kubectl get nodes -o jsonpath='{.items[*].metadata.name}'); do
     allocatable=$(kubectl get node "$node" -o jsonpath='{.status.allocatable.nvidia\.com/gpu}')
     if [ -n "$allocatable" ] && [ "$allocatable" -gt 0 ]; then
       allocated=$(kubectl get pods -A --field-selector spec.nodeName="$node",status.phase!=Failed,status.phase!=Succeeded \
         -o jsonpath='{range .items[*].spec.containers[*]}{.resources.requests.nvidia\.com/gpu}{"\n"}{end}' \
         | grep -v '^$' | awk '{s+=$1} END {print s+0}')
       echo "Node: $node | Total: $allocatable | Allocated: $allocated | Free: $((allocatable - allocated))"
     fi
   done
   ```

   You need `Free >= 1` on at least one node.

2. **Create the `http-partner-charts` ClusterRepo** and **check the StorageClass names** in
   the blueprint match your cluster (see Prerequisites).

3. **Choose how the app is reached** — edit the blueprint before installing (blueprint values
   are baked; the install wizard does not take per-value input). Set **one** of:
   - `global.domain: ai.example.com` — real domain (production). You'll add DNS records in step 6.
   - `gateway.loadBalancerIP: <reserved static IP>` — no domain; the app is served at
     `<ip>.nip.io` with no DNS setup. Prefer [sslip.io](https://sslip.io)? Also set
     `global.wildcardDns: sslip.io`.

   If both are blank the install stops with a clear message.

4. **Install** from the AI Factory UI: *Blueprints → AlchemiStudio + vLLM → Install →
   Fleet Bundle → target cluster → Install.*

5. **Wait for the APISIX gateway** (namespace `apisix`) to get an external IP — this IP fronts
   every AlchemiStudio hostname:

   ```bash
   kubectl -n apisix get svc apisix-gateway -w   # wait until EXTERNAL-IP is set, then Ctrl+C
   ```

6. **Real domain only:** create DNS A-records for `alchemi-app`, `alchemi-auth`, `alchemi-ops`
   and `alchemi-zenith` `.<your-domain>` pointing at that IP. The TLS certificate is issued
   automatically once DNS resolves.

7. **Get the URLs and the first login:**

   ```bash
   kubectl -n alchemi get configmap alchemi-endpoints -o jsonpath='{.data.APP_URL}{"\n"}'
   kubectl -n alchemi get configmap alchemi-endpoints -o jsonpath='{.data.ADMIN_EMAIL}{"\n"}'
   kubectl -n alchemi get secret alchemi-secrets -o jsonpath='{.data.FIRST_USER_PASSWORD}' | base64 -d; echo
   ```

   Keycloak asks for a new password on first login. vLLM needs a few minutes on first install
   to download the model weights.

## What this blueprint deploys

The `alchemistudio-platform` chart creates its own namespaces (and removes them on uninstall).
The blueprint's target namespace is `alchemi`.

| Namespace | Created by | What runs there |
|---|---|---|
| `alchemi` | blueprint target | App tier: web, ai, worker, workflow, zenith, compute-api, embeddings (TEI), AIOS workers |
| `alchemi-data` | platform chart | PostgreSQL (pgvector), Redis, SeaweedFS object store |
| `auth` | platform chart | Keycloak (login / OIDC) |
| `observability` | platform chart | OpenObserve (logs, metrics, traces) |
| `albox` | platform chart | Code sandboxes and the AIOS computer (in Kata micro-VMs when `kata.enabled: true`) |
| `apisix` | platform chart | APISIX gateway + etcd — `apisix-gateway` is the external LoadBalancer |
| `openbao` | platform chart | OpenBao (secrets store) |
| `external-secrets` | platform chart | External Secrets Operator |
| `vllm-serve` | vllm component | vLLM engine + router (GPU) |

**One instance per cluster.** Because the platform chart uses these fixed namespaces (and
installs cluster-wide pieces such as the External Secrets Operator), only one AlchemiStudio
instance can run per cluster today.

**Why vLLM has its own namespace:** it's intentional. The GPU model server is the expensive,
independently-sized part of the stack, so keeping it separate lets you apply GPU quotas and
policies to it, and upgrade or swap the model (e.g. to a larger model) without touching the
platform namespaces.

## Notes for reviewers

- **Gateway:** the chart deploys **Apache APISIX** into the `apisix` namespace as
  AlchemiStudio's own application router: it maps each AlchemiStudio hostname to its service,
  carries a wildcard route for apps users build inside AlchemiStudio, and handles CORS, rate
  limiting, HTTPS redirects and long timeouts for AI requests. Doing this with plain `Ingress`
  objects would need controller-specific annotations (ingress-nginx vs Traefik). APISIX stays
  in its own namespace and doesn't touch the cluster's ingress controller.
  - **Reaching it from outside:** by default `apisix-gateway` is a LoadBalancer Service. To
    use the cluster's own ingress / gateway as the entry point instead, set
    `gateway.serviceType: ClusterIP` and route the AlchemiStudio hostnames (including the
    wildcard) to the `apisix-gateway` Service on ports 80/443. APISIX still terminates TLS, so
    it needs the certificate (`tls.mode: acme` or `byo`), and the front gateway must pass HTTPS
    through to it unchanged (TLS passthrough) and forward port 80 for the ACME challenge.
  - **Roadmap:** we plan to make APISIX optional in a future release, so the platform can run
    directly behind the cluster's ingress controller or an existing gateway.
- **Chart source:** the `alchemistudio-platform` component uses the `http-partner-charts`
  ClusterRepo (`https://partner-charts.rancher.io`) — the same certified chart published via
  rancher/partner-charts, served over HTTP because the git-backed repo exceeds Fleet's 1 MiB
  bundle limit for this chart. The `vllm` component uses `application-collection`.
- **Images / credentials:** AlchemiStudio is a commercial product; its images are pulled from
  our registry with a **scoped, read-only (pull-only)** trial token, the same model as our
  published Rancher partner chart.
