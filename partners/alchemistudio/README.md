# AlchemiStudio

Partner blueprints for **AlchemiStudio** — an AI platform (agentic Copilot, AIOS
computer-use sandbox, and RAG) for SUSE AI Factory.

| Blueprint | What it deploys |
|---|---|
| [`alchemistudio-with-vllm`](blueprints/alchemistudio-with-vllm-0.1.0.yaml) | AlchemiStudio + in-cluster **vLLM** (Qwen2.5-3B-Instruct, Apache-2.0/open stack) as the Copilot model, plus a bundled CPU embedding server for RAG — fully self-hosted (no NGC / HuggingFace / cloud keys). |

## Notes for reviewers

- **Gateway:** the chart deploys **Apache APISIX** into the `apisix` namespace by default
  (`gateway.mode: bundled`) as the ingress / TLS / OIDC-routing layer; `gateway.mode: external`
  routes through an existing gateway instead. See the blueprint's `spec.description`.
- **Chart hosting (open question):** the `alchemistudio-platform` component references
  `chartRepo: alchemi-helm-charts` — a Helm repo we currently host. We'd welcome guidance on
  the preferred way to surface a partner chart to AI Factory (Application Collection, a partner
  registry, or a ClusterRepo the operator registers). The `vllm` component already uses
  `application-collection`.
- **Images / credentials (open question):** AlchemiStudio is a commercial product and its
  images are pulled from our registry with a **scoped, read-only (pull-only)** token. We're
  happy to adopt SUSE's preferred distribution model (mirroring into Application Collection or a
  partner registry) instead of embedding a pull token.
