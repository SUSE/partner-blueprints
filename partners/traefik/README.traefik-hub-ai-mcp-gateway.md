# Traefik Hub AI and MCP Gateway Installer

`traefik-hub-ai-mcp-gateway` installs Traefik Hub with its AI Gateway and MCP Gateway
on, next to the cluster's ingress controller, for the model servers and MCP servers
you already run. It creates no route and no Ingress: you add them, as in
[Routes](#routes). Two components:

- `traefik`: the official Traefik Helm chart, running its own Traefik Hub v3.21.4.
  This Traefik reads its own namespace and the resources of its class,
  `traefik-hub-ai-mcp-gateway`, and nothing else. It has no IngressClass, and its
  Service, `traefik-hub`, is a ClusterIP.
- `opentelemetry-collector`: the SUSE Application Collection chart. It receives
  Traefik's OTLP traces and metrics, logs a summary of them, and forwards them over
  OTLP once you set an endpoint, for example SUSE Observability's.

## Install

Check the [requirements of both blueprints](README.md#before-you-install).

1. Add Traefik's Helm repository once per cluster, as in
   [Before you install](README.md#before-you-install).
2. Get a Traefik Hub license key. Each install needs its own key. Request a trial at
   <https://info.traefik.io/traefik-hub-signup>.
3. Give the key in one of two ways:
   - In the wizard, open the `traefik` component's YAML and set:

     ```yaml
     global:
       blueprint:
         licenseToken: <license-key>
     ```

     AI Factory then keeps the key in plain text in the workload.
   - Before you install, create the Secret in the target namespace:

     ```shell
     kubectl create namespace traefik-hub-ai-mcp-gateway-system
     kubectl -n traefik-hub-ai-mcp-gateway-system \
       create secret generic traefik-hub-license \
       --from-literal=token=<license-key>
     ```

     Then set `licenseSecret: true` under `global.blueprint`.

   Without either, the install stops; the `traefik` component's Fleet HelmOp shows
   why.

Install it once per namespace: the blueprint pins its release names, `traefik-hub`
and `otel-collector`.

## Settings

| Setting | What |
|---|---|
| `global.blueprint.licenseToken` | The license key. The install creates the Secret that `hub.token` names from it |
| `global.blueprint.licenseSecret` | `true`: you created that Secret, key `token`, before installing |
| `hub.token` | The name of the license Secret, `traefik-hub-license` by default |

On the `opentelemetry-collector` component: `export.endpoint` (OTLP gRPC
`host:port`; empty means the debug exporter alone), `export.clusterName` (the
cluster name in SUSE Observability) and `export.apiKey` (the SUSE Observability API
key, which the chart keeps in a Secret).

The Traefik chart creates two cluster-scoped objects per install: a
ValidatingAdmissionPolicy and its binding, `traefik-hub-<namespace>-secret-types`.
Helm installs the chart's Traefik and Traefik Hub CRDs when the cluster lacks them,
and leaves them when you uninstall.

## Routes

Put the routes in the installer's namespace, on the `web` entry point, with
`ingressClassName: traefik-hub-ai-mcp-gateway` so that this Traefik serves them and
the cluster's ingress controller ignores them. This Traefik reads its own namespace
alone: to reach a backend in another namespace, add an ExternalName Service in this
one.

The examples serve, on host `ai.example.com`, an OpenAI-compatible model server
(Service `vllm`, port 8000, namespace `models`) and an MCP server (Service
`mcp-server`, port 8080, path `/mcp`, namespace `tools`). Save them in a file and
apply it with `kubectl -n traefik-hub-ai-mcp-gateway-system apply -f <file>`.

A WAF rule for both routes. It rejects request bodies containing U+017F and U+212A
because some backends fold them into ASCII keys:

```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: block-folding-characters
spec:
  plugin:
    coraza:
      directives:
        - 'SecRuleEngine On'
        - 'SecRequestBodyAccess On'
        - 'SecRequestBodyLimit 1048576'
        - 'SecRequestBodyLimitAction Reject'
        - 'SecAction "id:1716,phase:1,pass,nolog,ctl:forceRequestBodyVariable=On"'
        - 'SecRule REQUEST_BODY "@rx \x{017f}|\x{212a}" "id:1717,phase:2,deny,status:403,log,severity:CRITICAL,msg:folding_raw"'
        - 'SecRule REQUEST_BODY "@rx \\u017[fF]|\\u212[aA]" "id:1718,phase:2,deny,status:403,log,severity:CRITICAL,msg:folding_escape"'
```

The AI Gateway: `/v1/chat/completions` and `/v1/models`, with a `max_tokens` cap
that clients cannot change:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-backend
spec:
  type: ExternalName
  externalName: vllm.models.svc
  ports:
    - name: http
      port: 8000
---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: chat-completion
spec:
  plugin:
    chat-completion:
      params:
        maxTokens: 1024
---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: ai
spec:
  ingressClassName: traefik-hub-ai-mcp-gateway
  entryPoints:
    - web
  routes:
    - kind: Rule
      match: Host(`ai.example.com`) && (Path(`/v1/chat/completions`) || Path(`/v1/models`))
      middlewares:
        - name: block-folding-characters
        - name: chat-completion
      services:
        - name: ai-backend
          port: 8000
```

The MCP Gateway: `tools/list`, `ping` and `tools/call` of the listed tools
(`initialize` and `notifications/initialized` pass in any case). Other methods get
403, and `tools/list` shows the listed tools alone:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mcp-backend
spec:
  type: ExternalName
  externalName: mcp-server.tools.svc
  ports:
    - name: http
      port: 8080
---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: mcp-policy
spec:
  plugin:
    mcp:
      policies:
        - action: allow
          match: Equals(`mcp.method`, `tools/list`) || Equals(`mcp.method`, `ping`)
        - action: allow
          match: Equals(`mcp.method`, `tools/call`) && (Equals(`mcp.params.name`, `list_models`))
      defaultAction: deny
      listPolicies:
        - action: show
          match: Equals(`mcp.params.name`, `list_models`)
      listDefaultAction: hide
---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: mcp
spec:
  ingressClassName: traefik-hub-ai-mcp-gateway
  entryPoints:
    - web
  routes:
    - kind: Rule
      match: Host(`ai.example.com`) && Path(`/mcp`)
      middlewares:
        - name: block-folding-characters
        - name: mcp-policy
      services:
        - name: mcp-backend
          port: 8080
```

These routes accept any caller. Before you expose them, put a
[JWT middleware](https://doc.traefik.io/traefik-hub/api-gateway/secure/middleware/jwt)
first in their `middlewares`.

To reach the host from outside the cluster, an Ingress of the cluster's ingress
controller sends it to this Traefik. The ingress controller terminates TLS: add
`spec.tls`, and the cert-manager annotation if cert-manager issues the certificate.
The two annotations make a Traefik ingress controller (RKE2's default) serve the host
over HTTPS alone; other controllers ignore them.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: traefik-hub
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
spec:
  rules:
    - host: ai.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: traefik-hub
                port:
                  name: web
```

Then any MCP client can connect to `https://ai.example.com/mcp`, and:

```shell
curl https://ai.example.com/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"<model>","messages":[{"role":"user","content":"Hi"}]}'
```

Traefik Hub documentation: <https://doc.traefik.io/traefik-hub/>, with the
[AI Gateway](https://doc.traefik.io/traefik-hub/ai-gateway/overview) and the
[MCP Gateway](https://doc.traefik.io/traefik-hub/mcp-gateway/mcp).
