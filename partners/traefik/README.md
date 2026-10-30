# Traefik Labs blueprints for SUSE AI Factory

Traefik Labs maintains two blueprints in this folder. Each install runs its own
Traefik Hub, from the official Traefik Helm chart, next to the cluster's ingress
controller, and leaves that controller as it is.

| Blueprint | What it installs |
|---|---|
| [Traefik Hub AI and MCP Governance Demo](README.traefik-hub-ai-mcp-governance-demo.md) (`traefik-hub-ai-mcp-governance-demo`) | A SUSE AI stack behind Traefik Hub, with Keycloak sign-in: models per group, token budgets, data masking, prompt guards and MCP tool control. Not for production |
| [Traefik Hub AI and MCP Gateway Installer](README.traefik-hub-ai-mcp-gateway.md) (`traefik-hub-ai-mcp-gateway`) | Traefik Hub with the AI Gateway and MCP Gateway on, plus the SUSE OpenTelemetry Collector. You add the routes for the model and MCP servers you run |

## Before you install

- SUSE AI Factory with aif-operator 2.3.0 or later. On 2.3.0, add this catalog in
  AI Factory **Settings > Blueprint Catalogs > Add Catalog**: Repository URL
  `https://github.com/SUSE/partner-blueprints.git`, Branch `main`, Paths
  `partners`.
- A SUSE AI subscription, with Application Collection access set up in AI Factory.
  The SUSE components of both blueprints come from the Application Collection.
- Traefik's Helm repository in AI Factory, as below.
- A Traefik Hub license key for each install.

Both blueprints install the official Traefik Helm chart from Traefik's Helm
repository. A blueprint cannot add a repository to AI Factory, so add it once per
cluster, named `traefik`, in one of two ways:

- In the AI Factory UI: **Settings > Repositories > Add Repository**, Repository
  Name `traefik`, Repository Type `Helm`, Repository URL
  `https://traefik.github.io/charts`, then **Apply**.
- With `kubectl`:

  ```shell
  kubectl -n aif-operator patch settings.ai-factory.suse.com settings \
    --type=json -p '[{"op":"add","path":"/spec/customRepos/-",
    "value":{"name":"traefik","type":"helm",
    "url":"https://traefik.github.io/charts"}}]'
  ```

  If AI Factory runs in another namespace, find it with
  `kubectl get settings.ai-factory.suse.com -A`. If the Settings have no
  `spec.customRepos` yet, the command fails with "The request is invalid": create
  the list instead, with `"path":"/spec/customRepos","value":[{...}]` and the same
  entry between the braces. On an existing list, that form replaces the list.

## License key

Each install needs its own key. Request a trial at
<https://info.traefik.io/traefik-hub-signup>. Give the key to the `traefik`
component in one of two ways:

| | `licenseToken` | `licenseSecret: true` |
|---|---|---|
| You | In the wizard, open the `traefik` component's YAML and set `global.blueprint.licenseToken: <license-key>`. The install creates Secret `traefik-hub-license` from it | Before you install, create Secret `traefik-hub-license`, key `token`, in the target namespace, then set `global.blueprint.licenseSecret: true` |
| The key sits | In plain text in the AIWorkload, the Fleet objects, the Helm release and the Secret | In the Secret |
| Good for | A quick trial | Shared clusters |

To create the Secret:

```shell
kubectl create namespace <namespace>
kubectl -n <namespace> create secret generic traefik-hub-license \
  --from-literal=token=<license-key>
```

The wizard proposes `traefik-hub-ai-mcp-governance-demo-system` for the demo and
`traefik-hub-ai-mcp-gateway-system` for the installer. Set `hub.token` if you give
the Secret another name.

Set one of the two. With neither or both, the install stops and AI Factory shows
the `traefik` component as Pending. The message sits on that component's Fleet
HelmOp, which you open from the workload's details.

## Documentation

Traefik Hub documentation: <https://doc.traefik.io/traefik-hub/>. The blueprints
use the [AI Gateway](https://doc.traefik.io/traefik-hub/ai-gateway/overview), the
[MCP Gateway](https://doc.traefik.io/traefik-hub/mcp-gateway/mcp), the
[JWT middleware](https://doc.traefik.io/traefik-hub/api-gateway/secure/middleware/jwt),
the [WAF](https://doc.traefik.io/traefik-hub/api-gateway/secure/middleware/waf-guide)
and the license Secret of the
[Kubernetes installation guide](https://doc.traefik.io/traefik-hub/api-gateway/setup/installation/kubernetes).

## Support

Traefik Labs maintains this folder. For questions and issues, contact Andrea
Cervesato <andrea.cervesato@traefik.io>, Traefik Labs.
