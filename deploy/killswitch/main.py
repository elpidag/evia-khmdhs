"""Budget killswitch: detach billing from the project when the budget is hit.

OPTIONAL, and blunt on purpose — detaching billing STOPS THE SITE. It exists
because Google Cloud has no spending cap: a budget alert only emails you. Wire
it only if you want a hard guarantee of €0 and prefer the site down to a bill.

Deploy (once, from the repository root):

  gcloud pubsub topics create billing-alerts

  gcloud functions deploy stop-billing --gen2 --region=europe-west1 \
      --runtime=python312 --source=deploy/killswitch \
      --entry-point=stop_billing --trigger-topic=billing-alerts \
      --set-env-vars=GCP_PROJECT_ID=YOUR_PROJECT_ID

Then: Billing → Budgets & alerts → your budget → Manage notifications →
"Connect a Pub/Sub topic to this budget" → billing-alerts.

The function's service account needs `roles/billing.projectManager` on the
BILLING ACCOUNT (Billing → Account management → Add principal), otherwise it
can read the alert but not act on it.

To bring the site back: Billing → re-link the project to the billing account.
"""
from __future__ import annotations

import base64
import json
import os

import functions_framework
from googleapiclient import discovery

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
PROJECT_NAME = f"projects/{PROJECT_ID}"


@functions_framework.cloud_event
def stop_billing(cloud_event) -> None:
    payload = json.loads(
        base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    )
    cost = float(payload.get("costAmount", 0))
    budget = float(payload.get("budgetAmount", 0))
    if cost <= budget:
        print(f"cost {cost} within budget {budget} — nothing to do")
        return

    billing = discovery.build("cloudbilling", "v1", cache_discovery=False)
    projects = billing.projects()
    info = projects.getBillingInfo(name=PROJECT_NAME).execute()
    if not info.get("billingAccountName"):
        print("billing already detached")
        return

    projects.updateBillingInfo(
        name=PROJECT_NAME, body={"billingAccountName": ""}
    ).execute()
    print(f"BILLING DETACHED from {PROJECT_NAME}: cost {cost} > budget {budget}")
