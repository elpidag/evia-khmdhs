# Deploying the Forestry Works Tracker

The site (`atlas/` + `atlas_api/`) runs as **one container on Google Cloud Run**,
built and rolled out by **GitHub Actions on every push to `main`**. Everything it
serves is committed to this repository — the three SQLite DBs, the pdftotext
sidecars, the geo layers, the story images — so **a deploy is a pure function of
a git commit**. There is no database to migrate and nothing to upload by hand.

```
push to main ─► GitHub Actions (.github/workflows/deploy.yml)
                  OIDC token ─► Workload Identity Federation ─► atlas-deployer (no key, no secret)
                  docker build ─► europe-west1-docker.pkg.dev/PROJECT/atlas/atlas:SHA
                  gcloud run deploy atlas
Cloud Run :8080 ─► node atlas/server.mjs        SvelteKit SSR + /api,/pdf proxy (gzip on pages)
                     └─► 127.0.0.1:5050        gunicorn atlas_api.app:create_app()
```

Nothing here changes local development: `npm run dev` + `python -m atlas_api`
work exactly as before, and the password gate is inert unless its environment
variable is set.

---

## Publishing a change

**Push to `main`.** The workflow builds the image and rolls it out; the site is
updated about five minutes later. Whoever pushes, publishes — either laptop, no
Google account needed. Watch it: GitHub → **Actions** → *deploy*; the last step
prints the service URL.

A failed build never takes the site down: the previous revision keeps serving.

## Undo a bad deploy

Console → Cloud Run → `atlas` → **Revisions** → *Manage traffic* → send 100 % to
the previous revision → Save. Seconds, no rebuild. Then fix forward on `main`.

## The private-preview password (optional)

Set (the site asks for a password and tells search engines not to index it):

```bash
gcloud run services update atlas --region=europe-west1 \
  --update-env-vars=ATLAS_BASIC_AUTH='atlas:THE-PASSWORD'
```

Remove (the site is public — the "go live" switch):

```bash
gcloud run services update atlas --region=europe-west1 \
  --remove-env-vars=ATLAS_BASIC_AUTH
```

Both take ~20 seconds and no rebuild. **The password is never committed** — it
lives only as a Cloud Run environment variable, and the workflow deliberately
sets no environment variables, so deploys preserve it. Public is the default.

---

## One-time setup (≈ 20 minutes, ~15 commands)

Needs: a Google account with a **billing account** (a card — the free tier is
only granted to projects linked to one), the `gcloud` CLI, and write access to
this repository. Nothing is needed from the repository owner: the workflow file
lives in the repo and holds no secret.

### 1 · Project

```bash
gcloud auth login
# The project that exists: its id was typed «schorched» on creation and a
# Google project ID can never be changed; only the display name was
# corrected to "Scorched Forests". The id appears nowhere on the site —
# the service URL carries the project NUMBER.
export PROJECT_ID=schorched-forests
gcloud projects create "$PROJECT_ID" --name="Scorched Forests"
gcloud config set project "$PROJECT_ID"
# link the billing account: console → Billing → My projects → the project → Change billing
export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
echo "$PROJECT_ID $PROJECT_NUMBER"              # → both go into the workflow (step 8)
```

### 2 · APIs

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com
```

### 3 · Image repository, with a cleanup policy

Artifact Registry is free to 0.5 GB and every image is ~150 MB, so old versions
must be pruned. Keep the two newest, delete anything older than a week:

```bash
gcloud artifacts repositories create atlas --repository-format=docker --location=europe-west1
cat > /tmp/atlas-cleanup.json <<'JSON'
[
  {"name": "keep-newest", "action": {"type": "Keep"}, "mostRecentVersions": {"keepCount": 2}},
  {"name": "delete-old",  "action": {"type": "Delete"}, "condition": {"olderThan": "604800s"}}
]
JSON
gcloud artifacts repositories set-cleanup-policies atlas --location=europe-west1 \
  --policy=/tmp/atlas-cleanup.json --no-dry-run
```

### 4 · Two identities: the deployer and the runtime

The deployer is what GitHub Actions becomes; the runtime is what the container
runs as (it needs no Google permission at all — the site only reads its own
files).

```bash
gcloud iam service-accounts create atlas-deployer --display-name="Atlas deployer (GitHub Actions)"
gcloud iam service-accounts create atlas-runtime  --display-name="Atlas runtime (Cloud Run)"
export SA_DEPLOY=atlas-deployer@$PROJECT_ID.iam.gserviceaccount.com
export SA_RUN=atlas-runtime@$PROJECT_ID.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_DEPLOY" --role=roles/run.admin
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_DEPLOY" --role=roles/artifactregistry.writer
# the deployer may deploy AS the runtime identity
gcloud iam service-accounts add-iam-policy-binding "$SA_RUN" --member="serviceAccount:$SA_DEPLOY" --role=roles/iam.serviceAccountUser
```

### 5 · Keyless trust for GitHub Actions (Workload Identity Federation)

GitHub signs each workflow run with an OIDC token; Google trusts that token —
and ONLY for pushes to `main` of `elpidag/evia-khmdhs` — in exchange for the
deployer identity. No key is ever created, so there is nothing to leak.

```bash
gcloud iam workload-identity-pools create github --location=global --display-name="GitHub Actions"
gcloud iam workload-identity-pools providers create-oidc github \
  --location=global --workload-identity-pool=github --display-name="GitHub" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository == 'elpidag/evia-khmdhs' && assertion.ref == 'refs/heads/main'"
gcloud iam service-accounts add-iam-policy-binding "$SA_DEPLOY" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/elpidag/evia-khmdhs"
```

### 6 · Budget alert

Console → Billing → **Budgets & alerts** → Create budget → this project → amount
**€3** → alerts at 50 / 90 / 100 % → email. (A €1 budget would already fire at
about nine thousand visits — see Costs.) The optional hard stop lives in
`deploy/killswitch/`.

### 7 · Fonts: nothing to do

The Adobe Fonts web project in `atlas/src/app.html`
(`use.typekit.net/drh1gfl.css`) loads on any hostname. Adobe dropped domain
lists from web projects — its help page says to add the embed code to any
website, no matter where it is hosted — and the kit was probed on 2026-09-02
with a registered, an unregistered and no referer alike: the CSS and the font
files came back identical. There is no domain to register and no publish step;
the web project's optional domain field is informational only.

### 8 · The workflow, and the first deploy

In `.github/workflows/deploy.yml` fill in the two values at the top
(`PROJECT_ID`, `PROJECT_NUMBER`), commit, merge into `main`, push. The first run
creates the service (`gcloud run deploy` creates it when absent) and prints its
URL. Open it.

### 9 · Keep one instance warm (free)

Cloud Run starts a container for the first visitor after ~15 idle minutes
(3–4 s). A request every five minutes keeps one instance alive, and Cloud Run
bills CPU only while a request is being handled, so this stays inside the free
tier (≈ 8,640 tiny requests a month of the 2 million allowed):
[cron-job.org](https://cron-job.org) (free, no card) → new cron job → URL
`https://<the service URL>/api/meta` → every 5 minutes.

---

## Testing the container locally

```bash
docker build -t atlas:local .
docker run --rm -p 8099:8080 atlas:local
```

Then `http://localhost:8099`. The image is the same one Cloud Run gets, so this
catches deployment problems before they ship. With `-e ATLAS_BASIC_AUTH=test:test`
the preview gate can be tried; with `-e ATLAS_PDF_CACHE_BUDGET_MB=1` the PDF
cache budget (below).

## Manual deploy (fallback when GitHub Actions is unavailable)

The workflow's own three commands, from a laptop with Docker and `gcloud`:

```bash
gcloud auth login && gcloud auth configure-docker europe-west1-docker.pkg.dev
IMG=europe-west1-docker.pkg.dev/$PROJECT_ID/atlas/atlas:$(git rev-parse --short HEAD)
docker build -t "$IMG" . && docker push "$IMG"
gcloud run deploy atlas --image="$IMG" --region=europe-west1 --platform=managed --port=8080 \
  --cpu=1 --memory=1Gi --concurrency=40 --min-instances=0 --max-instances=3 --timeout=120 \
  --cpu-boost --service-account=atlas-runtime@$PROJECT_ID.iam.gserviceaccount.com --allow-unauthenticated
```

## What the container does differently from `npm run dev`

- **The SSR document is gzipped** (`atlas/server.mjs` wraps the page path in the
  `compression` middleware). adapter-node precompresses the static assets at
  build time and Flask gzips its JSON, but nothing compresses a rendered page,
  and the data pages' documents are ~220 KB.
- **`.geojson` files are gzipped in the image** (Dockerfile stage 1):
  SvelteKit's precompress covers html/js/json/css/svg/xml/wasm only, and the
  1.2 MB EFFIS layer would ship raw.
- **The PDF cache has a budget.** Cloud Run's writable filesystem is
  *in-memory* — every cached PDF is RAM — and a pinger-kept instance lives for
  days. Once the PDFs in a cache directory reach `ATLAS_PDF_CACHE_BUDGET_MB`
  (200 in the image; 0 = unlimited, the local default) the proxy still serves
  every download but stops keeping them. The committed `.txt` sidecars are
  never touched.
- **The API's two geo layers are copied explicitly** (`effis_fires.geojson`,
  `evia_works_zones.geojson`): `queries_extra` reads them from
  `atlas/static/geo/` at request time, which the SvelteKit build does not ship
  to the Python side.

## Costs and safeguards

Expected: **€0.10–0.50 per month.** Cloud Run's free tier (2 M requests,
180,000 vCPU-s, 360,000 GiB-s per month) covers this traffic many times over;
GitHub Actions minutes are free on a public repository; the image repository
stays under its 0.5 GB allowance with the cleanup policy. The one line with no
European free amount is outbound data: ≈ €0.11 per GB, and a visit weighs about
1 MB — **1,000 visits ≈ €0.11, 10,000 ≈ €1.10 a month.**

Protections, in order:

1. `--min-instances=0` — an idle site costs nothing.
2. `--max-instances=3`, `--concurrency=40` — caps what can ever run.
3. `atlas/static/robots.txt` denies `/pdf/` and `/api/` — a crawler walking the
   document proxy is the one realistic way to run up both egress and ΚΗΜΔΗΣ
   traffic; the cache budget bounds what such a walk can do to memory.
4. The €3 budget with email alerts (step 6).
5. Optional hard stop: `deploy/killswitch/` detaches billing when the budget is
   exceeded. It is the only true guarantee of €0, and it takes the site down
   rather than spending money.

**Do not** follow tutorials that add a *Global External Application Load
Balancer* for a custom domain — that costs ~€18/month. Cloud Run domain mapping
or Cloudflare in front are both free, and Cloudflare would also cache the map
layers at its edge.

## Working on this repository from two machines

- `main` on GitHub is the only source of truth; whoever pushes, publishes.
- A data refresh ships automatically: the SQLite files are in git, so the next
  build carries them.
- SQLite is binary, so if both machines regenerate a DB the same day git cannot
  merge it. Resolve by taking either side and re-running `python -m khmdhs.refresh` —
  everything derived is regenerable.
- The deploy lives in files nothing else touches (`Dockerfile`, `.dockerignore`,
  `deploy/`, `.github/workflows/deploy.yml`, this file). The shared files it
  edits are `atlas/server.mjs` (the password gate and the page gzip),
  `atlas/static/robots.txt`, `atlas_api/pdf_proxy.py` / `app.py` (the cache
  budget) and `atlas/package.json` (the `compression` dependency).

## What is deliberately NOT deployed

`data/processed/arogi.sqlite`. The ΑΡΩΓΗ pages left the site on 2026-08-23 and
its decision documents name private individuals, so the DB is not put on a
public server at all. The data, the harvest and `queries_extra.arogi_*` stay in
the repository. Likewise the gitignored PDF caches, the DEM cache and the raw
layers: the image carries ~150 MB of the ~3.3 GB under `data/`.
