# Exchange

FastAPI serves currency quotes using the Bacen PTAX client in `rates.py`.
Quotes are cached in memory for five minutes by default. A failed refresh can serve a stale quote.

`GET /exchange/{from}/{to}` accepts three-letter currency codes and returns
`sell`, `buy`, `date`, and `id-account`. The rate comes from
[Bacen PTAX](https://insper.github.io/platform/2026.2/exercises/exchange/bacen/).
`/exchanges/{from}/{to}` is also supported. `GET /exchange/currencies` lists the
currencies quoted by PTAX. The health endpoint is `GET /exchange/health-check`.
Run the API behind the gateway, which
authenticates the user and sets the `id-account` header. Keep the Exchange server
on a private network. `just run` from the parent is for local development.

## CI/CD

From this repository, run `uv run --locked python -m unittest test_rates` to test
the PTAX client, or `uv run --locked uvicorn main:app` to start the API.
The [workflow](.github/workflows/ci-cd.yml) builds the image, runs the PTAX tests
inside it, and checks the HTTP health and authentication responses.

To publish from `main`, set the `DOCKERHUB_IMAGE` Actions variable to the
team's public Docker Hub repository (for example, `team/exchange`). Set
`DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` as Actions secrets with permission
to push there. The image is tagged with the Exchange commit SHA.

For EKS rollout, set these Actions variables in the Exchange repo.

| Variable | Value |
| --- | --- |
| `EKS_CLUSTER_NAME` | The team's EKS cluster in `sa-east-1` |
| `EKS_NAMESPACE` | The namespace that owns the Exchange Deployment and Service |
| `EKS_DEPLOY_ROLE_ARN` | An AWS role for the Exchange workflow with `eks:DescribeCluster` |

Set the role's GitHub OIDC subject to
`repo:pato-nego@317014205/Exchange@1412079538:ref:refs/heads/main` and its
audience to `sts.amazonaws.com`. Give that IAM role access to the cluster and
permission to apply the Deployment and Service and watch the rollout in the
Exchange namespace. The GitHub runner needs network access to the cluster API.

Give the dedicated Exchange worker the label `workload=exchange`. The manifest
also tolerates the matching `NoSchedule` taint. Gateway and Order can call the
ClusterIP Service on port 8000 by its Kubernetes DNS name.

The workflow applies the [manifests](k8s/) with the published image digest and
waits for the rollout. Use **Run workflow** on `main` to run the configured
pipeline manually.
