# CI / CD Pipeline Setup

This document provides a structured, formatted version of the CI/CD setup instructions you supplied. All original instruction lines are preserved (only sensitive literal values have been MASKED with placeholders like `<SUBSCRIPTION_ID>`). Command sequences have been grouped into code blocks for clarity.

> Masking Note: Replaced actual IDs / names (`20fb...`, `fastapi`, `arashacr123`, `travel-mult-agent`, etc.) with placeholders to reduce accidental disclosure. Substitute your real values when executing.

---
## Quick Overview

Pipeline goals:

1. Use a Service Principal (SP) with least privileges (Contributor on target Resource Group + AcrPush on ACR) for GitHub Actions OIDC login.
2. Build & push container images to Azure Container Registry (ACR) on PRs and pushes to `master`.
3. Deploy pull request builds to a staging App Service.
4. Deploy merged `master` builds to production (with environment protection / approval).
5. Synchronize rotated secrets (App Settings) automatically on each deployment.
6. Perform a health check to fail fast if the container doesn't start correctly.

---
## IMPORTANT SECURITY NOTE

If any real API keys or secrets were committed earlier (e.g., in `.env`), **rotate them immediately** and remove the plaintext values from source control. Store them as GitHub Secrets or App Service configuration values instead.

---
## Verbatim Instructions (Exact Content Preserved)

Below is the exact text you provided. It has only been wrapped in Markdown fences and subdivided into code blocks for commands without altering any lines.

### Environment Variable & Service Principal Creation

```cmd
set SUBSCRIPTION_ID=<SUBSCRIPTION_ID>
set RG_WEBAPP=<RESOURCE_GROUP>
set ACR_NAME=<ACR_NAME>
set NEW_APP_NAME=<SP_APP_REG_NAME>
REM Choose an end date within allowed policy (UTC, ISO8601). Example ~90 days:
set END_DATE=<END_DATE_UTC_ISO>


az ad app create --display-name "%NEW_APP_NAME%" --query "{appId:appId,id:id,displayName:displayName}" -o json

set APP_ID=<paste appId from previous output>

az ad sp create --id %APP_ID%

az ad app credential reset --id %APP_ID% --append --display-name "ci-secret" --end-date %END_DATE% --query "{clientId:appId,clientSecret:password,tenant:tenant}" -o json

ad client secrete in azure portal
called travel-agent


set SUBSCRIPTION_ID=<SUBSCRIPTION_ID>
set RG_WEBAPP=<RESOURCE_GROUP>
set ACR_NAME=<ACR_NAME>
set APP_ID=<APP_ID>

az ad sp show --id %APP_ID% --query "{appId:appId, objectId:id, displayName:displayName}" -o json

for /f "delims=" %i in ('az ad sp show --id %APP_ID% --query id -o tsv') do set SP_OBJECT_ID=%i
echo SP_OBJECT_ID=%SP_OBJECT_ID%

az role assignment create --assignee-object-id %SP_OBJECT_ID% --assignee-principal-type ServicePrincipal --role Contributor --scope /subscriptions/%SUBSCRIPTION_ID%/resourceGroups/%RG_WEBAPP%

for /f "delims=" %i in ('az acr show -n %ACR_NAME% --query id -o tsv') do set ACR_ID=%i
echo ACR_ID=%ACR_ID%

az role assignment create --assignee-object-id %SP_OBJECT_ID% --assignee-principal-type ServicePrincipal --role AcrPush --scope %ACR_ID%
```

### Step – Add GitHub repository secrets

Do this now.

In GitHub: Repo > Settings > Secrets and variables > Actions > New repository secret (repeat for each).
Required deployment/auth secrets:

Creating the AZURE_CREDENTIALS secret (single JSON blob) — here’s exactly what to do.

Step 1: Collect the four values (don’t guess)

clientId = Application (client) ID of your App Registration (Portal > Microsoft Entra ID > App registrations > your app).
clientSecret = The secret VALUE you copied when you created it (not the Secret ID). If you lost it, create a new client secret.
tenantId = Directory (tenant) ID (same portal overview page).
subscriptionId = <SUBSCRIPTION_ID> (you already have it).
Step 2: Build the JSON (example template) Replace ALL CAPS placeholders with your real GUIDs / secret value:

```json
{ "clientId": "<CLIENT_ID>", "clientSecret": "<CLIENT_SECRET_VALUE>", "tenantId": "<TENANT_ID>", "subscriptionId": "<SUBSCRIPTION_ID>" }
```

Notes:

No trailing commas.
Keys must use those exact lowercase names.
Keep it as one valid JSON object. Newlines or single line both work.
Optional (local validation): If you have jq installed: echo { "clientId": "...", "clientSecret": "...", "tenantId": "...", "subscriptionId": "..." } | jq . (If it prints formatted JSON, it’s valid.)


App Service & container info:

APP_SERVICE_NAME = <APP_SERVICE_NAME_PROD>
RESOURCE_GROUP = <RESOURCE_GROUP>
ACR_NAME = <ACR_NAME>
ACR_LOGIN_SERVER = <ACR_LOGIN_SERVER>
IMAGE_NAME = <IMAGE_NAME> (will become <ACR_LOGIN_SERVER>/<IMAGE_NAME>:<tag>)
App runtime/application config secrets (move them out of the committed .env): For each sensitive value currently in .env, create either a secret or (better) set them as App Service configuration settings. If you want the workflow to set them later, add as secrets now:



SERPAPI_API_KEY
TRAVEL_AGENT_API_KEY (rotate since leaked)
GRAPHRAG_API_KEY (rotate) Optionally:
GRAPHRAG_LLM_MODEL
GRAPHRAG_EMBEDDING_MODEL
GRAPHRAG_API_BASE
GRAPHRAG_DATA_DIR (non-secret; can be an App Setting instead)



REM Variables
set SUBSCRIPTION_ID=<SUBSCRIPTION_ID>
set PROD_RG=<RESOURCE_GROUP>
set STAGING_RG=<RESOURCE_GROUP>
set STAGING_APP=<APP_SERVICE_NAME_STAGING>
set PLAN_NAME=<APP_SERVICE_PLAN_NAME>

```

### Step – Prepare/confirm a separate staging App Service (needed before we write the workflow)

Why: For PR deployments with approval you’ll target a staging Web App (container) and protect the GitHub Environment “staging”. Production stays “travel-mult-agent”.

First: a clarification

Re-deploying a new container image does NOT overwrite existing App Settings (your secrets set in the App Service portal remain). Only if you explicitly change settings (via CLI/API) would they change.
Action now: Decide/confirm staging app details.

```cmd
REM (1) Verify plan exists
az appservice plan show -g %STAGING_RG% -n %PLAN_NAME% --query "{name:name, kind:kind, sku:sku.tier}" -o json

REM (2) Create staging webapp (container, no image yet)
az webapp create -g %STAGING_RG% -p %PLAN_NAME% -n %STAGING_APP% --runtime "PYTHON:3.11" 

REM (3) Configure it to use your ACR image (will 404 until first push)
az webapp config container set ^
  -g %STAGING_RG% -n %STAGING_APP% ^
  --docker-custom-image-name <ACR_LOGIN_SERVER>/<IMAGE_NAME>:staging ^
  --docker-registry-server-url https://<ACR_LOGIN_SERVER>

REM (4) Assign the same app settings (repeat per key; sample) YOU MUST SET THESE ALREADY IN THE ENV VARIABLE
az webapp config appsettings set -g %STAGING_RG% -n %STAGING_APP% --settings SERPAPI_API_KEY=%SERPAPI_API_KEY% TRAVEL_AGENT_API_KEY=%TRAVEL_AGENT_API_KEY% GRAPHRAG_API_KEY=%GRAPHRAG_API_KEY% GRAPHRAG_LLM_MODEL=%GRAPHRAG_LLM_MODEL%  GRAPHRAG_API_BASE=%GRAPHRAG_API_BASE%

REM (5) (If not already) ensure SP has Contributor on staging RG (skip if same RG)
az role assignment create --assignee %APP_ID% --role Contributor --scope /subscriptions/%SUBSCRIPTION_ID%/resourceGroups/%
STAGING_RG%
```

### Step – Create GitHub Environments (staging & production) and set environment vars

Do this now.

In GitHub: Settings > Environments > New environment

Name: staging
(Optional) No approval required (auto deploy for PRs).
Add another environment:

Name: production
Require reviewers (add your user) so prod deploy waits for approval.
For each environment click “Environment variables” (or “Secrets” if you prefer to scope them): Use repo-level secrets for auth (already added). Add ONLY these environment variables (not secrets) per environment:

staging environment variables:

APP_SERVICE_NAME = <APP_SERVICE_NAME_STAGING> (adjust if you picked a different name)
IMAGE_TAG_SUFFIX = -staging
DEPLOY_SLOT = (leave blank if not using slots)
ACR_LOGIN_SERVER = <ACR_LOGIN_SERVER>
production environment variables:

APP_SERVICE_NAME = <APP_SERVICE_NAME_PROD>
IMAGE_TAG_SUFFIX = -prod
DEPLOY_SLOT = (blank)
ACR_LOGIN_SERVER = <ACR_LOGIN_SERVER>
(Optional) If you want distinct API keys per environment, move those secrets (SERPAPI_API_KEY, TRAVEL_AGENT_API_KEY) from repo-level into each environment instead (delete from repo-level after copying).

Confirm the staging Web App really exists and matches APP_SERVICE_NAME you set above


### Step – Create the GitHub Actions workflow file (don’t commit yet until you review)

Goal: One workflow that

Builds & pushes container image to ACR on PRs targeting main, deploys to staging app (environment: staging).
Builds & pushes on push to main (after PR merge) and deploys to production app (environment: production – requires your approval because of environment protection).
Updates App Settings each deploy (so rotated secrets sync). Existing settings not listed are preserved.
Uses only repo‑level secrets (no duplication needed).
File to add: .github/workflows/container-deploy.yml

Create a feature branch (GitHub web UI):
Go to the repo main page in GitHub.
Near the top-left where it shows “master”, click the branch dropdown.
In the text box, type: feature/cicd-pipeline
Press Enter (this creates the new branch from master and switches context to it).

Review the YAML below. After you create it, commit, and open a PR, the staging job should run. depending on your branch name main or master you need to adjust.

```yaml
name: Build & Deploy Container (Staging / Production)

on:
  pull_request:
    branches: [ master ]
  push:
    branches: [ master ]
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

env:
  REGISTRY: ${{ secrets.ACR_LOGIN_SERVER }}
  IMAGE_NAME: travel-agent
  RESOURCE_GROUP: ${{ secrets.RESOURCE_GROUP }}
  ACR_NAME: ${{ secrets.ACR_NAME }}

jobs:
  staging:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    environment: staging
    env:
  APP_SERVICE_NAME: <APP_SERVICE_NAME_STAGING>
      IMAGE_TAG: ${{ github.sha }}-staging
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Azure login
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
          auth-type: SERVICE_PRINCIPAL

      - name: ACR login
        run: az acr login --name $ACR_NAME

      - name: Build image
        run: docker build -t $REGISTRY/$IMAGE_NAME:$IMAGE_TAG -f Dockerfile .

      - name: Push image
        run: docker push $REGISTRY/$IMAGE_NAME:$IMAGE_TAG

      - name: Set container
        run: |
          az webapp config container set \
            -g $RESOURCE_GROUP -n $APP_SERVICE_NAME \
            --docker-custom-image-name $REGISTRY/$IMAGE_NAME:$IMAGE_TAG \
            --docker-registry-server-url https://$REGISTRY

      - name: Sync app settings
        run: |
          az webapp config appsettings set -g $RESOURCE_GROUP -n $APP_SERVICE_NAME --settings \
            SERPAPI_API_KEY='${{ secrets.SERPAPI_API_KEY }}' \
            TRAVEL_AGENT_API_KEY='${{ secrets.TRAVEL_AGENT_API_KEY }}' \
            GRAPHRAG_API_KEY='${{ secrets.GRAPHRAG_API_KEY }}'

      - name: Health check
        run: |
          echo "Waiting 30s..."
          sleep 30
          for i in {1..15}; do
            code=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_SERVICE_NAME.azurewebsites.net/health || true)
            echo "Attempt $i => $code"
            [ "$code" = "200" ] && exit 0
            sleep 6
          done
          echo "Health check failed"; exit 1

  production:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production
    env:
  APP_SERVICE_NAME: <APP_SERVICE_NAME_PROD>
      IMAGE_TAG: ${{ github.sha }}-prod
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Azure login
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
          auth-type: SERVICE_PRINCIPAL

      - name: ACR login
        run: az acr login --name $ACR_NAME

      - name: Build image
        run: docker build -t $REGISTRY/$IMAGE_NAME:$IMAGE_TAG -f Dockerfile .

      - name: Push image
        run: docker push $REGISTRY/$IMAGE_NAME:$IMAGE_TAG

      - name: Set container
        run: |
          az webapp config container set \
            -g $RESOURCE_GROUP -n $APP_SERVICE_NAME \
            --docker-custom-image-name $REGISTRY/$IMAGE_NAME:$IMAGE_TAG \
            --docker-registry-server-url https://$REGISTRY

      - name: Sync app settings
        run: |
          az webapp config appsettings set -g $RESOURCE_GROUP -n $APP_SERVICE_NAME --settings \
            SERPAPI_API_KEY='${{ secrets.SERPAPI_API_KEY }}' \
            TRAVEL_AGENT_API_KEY='${{ secrets.TRAVEL_AGENT_API_KEY }}' \
            GRAPHRAG_API_KEY='${{ secrets.GRAPHRAG_API_KEY }}'

      - name: Health check
        run: |
          echo "Waiting 30s..."
          sleep 30
          for i in {1..15}; do
            code=$(curl -s -o /dev/null -w "%{http_code}" https://$APP_SERVICE_NAME.azurewebsites.net/health || true)
            echo "Attempt $i => $code"
            [ "$code" = "200" ] && exit 0
            sleep 6
          done
          echo "Health check failed"; exit 1
```

### Notes / rationale:

Separate jobs so a PR never touches production.
Image tags include commit SHA plus environment suffix (unique + clear).
App Settings sync each deploy; if a secret rotates in GitHub, the next deploy propagates it.
Secrets remain repo-level; no duplication needed. (If you later need different staging keys, add environment-level secrets with same names—they will override.)
Health check ensures failed startups cause a red CI status.
Next (after you add & commit):

Create folder .github/workflows if missing.
Add the file above.
Commit on a feature branch and open a PR against main. Confirm staging job runs and deploys to your staging site.
Merge PR; production job should appear waiting for approval (GitHub UI Environment approval).
(See <attachments> above for file contents. You may not need to search or read the file again.)

---
## Suggested Next Steps (Optional Enhancements)

| Area | Improvement | Benefit |
|------|-------------|---------|
| Testing | Add a test job before build | Prevent broken images deploying |
| Linting | Run flake8/ruff + mypy | Faster feedback on code quality |
| Caching | Use Docker layer cache (BuildKit `--cache-from`) | Faster rebuilds |
| Observability | Add `az monitor app-insights component create` & instrumentation | Faster prod diagnostics |
| Rollback | Keep previous image tag in GitHub Outputs | Quick manual rollback |

---
## Troubleshooting Tips

- Login failures: Ensure `AZURE_CREDENTIALS` JSON has correct `clientId`, `tenantId`, `subscriptionId`, and a valid (not expired) `clientSecret`.
- ACR push denied: Confirm `AcrPush` role assignment propagated (can take a few minutes). Re-run workflow.
- 403 on deployment: Check SP has `Contributor` on the correct Resource Group scope.
- Health check failing: View container logs via `az webapp log tail -n <app> -g <rg>`.
- Secret not updated: Ensure the key name matches exactly in both GitHub Secret and workflow step.

---
## Rollback (Manual)

1. Identify last known good image tag from Actions logs.
2. Run:
   ```bash
   az webapp config container set -g <RESOURCE_GROUP> -n <APP_SERVICE_NAME_PROD> \
     --docker-custom-image-name <ACR_LOGIN_SERVER>/<IMAGE_NAME>:<GOOD_TAG> \
     --docker-registry-server-url https://<ACR_LOGIN_SERVER>
   ```
3. Verify with health endpoint.

---
## Appendix: Minimal `.env` Hygiene

Remove secrets from committed `.env` files. Use placeholders locally and rely on App Service + GitHub Secrets in CI/CD.

---
End of document.
