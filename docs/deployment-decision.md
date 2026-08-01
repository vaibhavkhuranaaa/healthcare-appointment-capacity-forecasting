# Deployment decision

## Decision

**2026-07-26: retain the verified local-only demo.** No provider, cloud
resource, hosted URL, public exposure, paid capacity, or deployment pipeline is
approved for this project at this time.

## Rationale

The local workflow already satisfies the first-demo review path: it runs from
documented commands against a checksum-verified synthetic fixture and produces
versioned evaluation evidence. Hosting would add cost, access control,
operational ownership, and a public-claim review without improving that local
proof.

## Decision record

| Item | Decision |
| --- | --- |
| Provider | None |
| Direct metered service cost | $0 |
| Exposure | Local machine only; no network endpoint or public URL |
| Data | Included fully synthetic aggregate fixture only |
| Teardown / recovery | Delete `build/capacity_forecasting.duckdb`; no external resources exist |
| Revisit trigger | A human approves a named provider, cost boundary, intended visibility, and teardown plan for a demonstrated sharing need |

This is not a deployment approval. A future hosting decision must update
`.project/approvals.yml` before any provider resource is created.

## Superseding hosting direction (2026-07-31)

A human has now approved **AWS**, **public visibility**, and **free-tier-only**
hosting. If verification fails, resources must be retained until the human
requests deletion. This is approval in principle, not permission to guess the
AWS service or create resources without a valid AWS authentication context.

Before provisioning, choose one of these distinct scopes:

1. A static public evidence page that documents the validated local workflow.
2. A public interactive application, which requires a separate hosted runtime
   design and has a materially different cost and security profile.

## Proposed interactive application plan (awaiting exact approval)

The human selected option 2 on 2026-07-31, and read-only AWS authentication was
verified for account `074642416888` in `us-east-2`. This is a proposed plan,
not a provisioning or publication approval.

| Item | Proposed decision |
| --- | --- |
| Application | A browser-only capacity dashboard. It loads the included, checksum-verified synthetic aggregate fixture and runs the published weekday-baseline calculation in the visitor's browser. It exposes no AWS API, database, upload, account, or clinical workflow. |
| AWS services | One private S3 bucket in `us-east-2` and one global CloudFront distribution with the bucket as its only origin. Use CloudFront Origin Access Control (OAC); keep all S3 Block Public Access controls enabled. |
| Public exposure | Only the CloudFront distribution URL is public, HTTPS-only, with the default CloudFront certificate and no custom domain. The S3 bucket and its object URLs are not public. |
| Deliberately excluded | No Lambda, ECS, App Runner, API Gateway, database, Route 53, ACM custom certificate, WAF, CloudFront Functions, Lambda@Edge, Origin Shield, logging delivery, or paid cache invalidation. |
| Data and claims | The public bundle contains only the approved synthetic aggregate fixture and disclosed benchmark evidence. It must prominently state: no PHI, no clinical recommendations, and synthetic benchmark results only. |
| Cost boundary | Keep S3 within 5 GB storage, 20,000 GET requests, and 2,000 PUT requests per month. CloudFront's standing free allocation is 1 TB data transfer out and 10 million HTTP/HTTPS requests per month. Before release, create a cost budget alert at the smallest supported threshold; this alerts but does not cap usage. Do not enable features outside these limits. |
| Recovery on failed verification | Retain the bucket and distribution as approved; do not delete automatically. Stop the release, record the failure, and wait for human direction. No public announcement or custom-domain cutover occurs before verification succeeds. |

### Approval requested

Approve this exact plan only if the account's applicable Free Tier or credits
cover the proposed use and you accept that a budget alert cannot guarantee a
hard spend cap. If approved, record the approval in `.project/approvals.yml`,
commit the exact source revision, then provision and verify that revision.

## Cost-minimum alternative: Cloudflare Pages (awaiting provider selection)

Cloudflare Pages can host the same browser-only application with no server-side
functions, database, upload, or user accounts. Its Free plan permits 500 builds
per month, up to 20,000 deployed files, and unlimited static requests. This
avoids AWS S3 and CloudFront metered overage risk for this small public portfolio
demo. It does, however, replace the approved-in-principle AWS provider with a
third-party hosting account.

| Option | Cost-control outcome | Operational trade-off | Recommendation |
| --- | --- | --- | --- |
| AWS S3 + CloudFront | Low expected cost, but AWS free allocations can be exceeded and a budget alert is not a hard cap. | Uses the already authenticated AWS account; private origin and public CDN need two AWS resources and a budget alert. | Use only if AWS demonstration value is more important than a hard $0 hosting boundary. |
| Cloudflare Pages Free, static-only | $0 plan and unlimited static requests; no paid plan, Pages Functions, Workers, R2, or add-ons enabled. | Requires a Cloudflare account and deployment authorization; the app remains entirely public and static. | **Lowest-cost choice** for this synthetic, browser-only portfolio application. |
| GitHub Pages | No direct hosting invoice, but its limits are soft (100 GB/month) and the project would need an eligible GitHub Pages repository. | Less suitable while no remote exists and the project must remain a focused public application. | Do not select. |

### Provider decision required

The prior AWS approval remains valid in principle, but it is not an approval to
switch providers. Choose exactly one before provisioning:

1. **AWS S3 + CloudFront** — retain the proposed AWS plan and accept its
   alert-only overage control.
2. **Cloudflare Pages Free** — replace AWS with the static-only $0 plan and
   authorize a Cloudflare deployment account.

## Proposed dynamic plan: Cloudflare Workers Free (awaiting exact approval)

The human declined a browser-only application and selected a dynamic Cloudflare
runtime on 2026-07-31. This supersedes the Cloudflare Pages proposal if it is
approved. It does not authorize account creation, deployment, or publication.

| Item | Proposed decision |
| --- | --- |
| Runtime | One Cloudflare Worker on the Workers Free plan, with a `workers.dev` HTTPS URL only. Its static assets provide the dashboard; `POST /api/forecast` runs the deterministic weekday-baseline capacity calculation. |
| Request contract | Accept only numeric capacity-scenario values within a documented range. Reject files, text fields, identifiers, cookies, authorization headers, cross-origin requests, and unsupported methods without echoing request content. |
| Data boundary | Bundle only the approved NHS GPAD national aggregate derivative and its version metadata into the Worker. No KV, D1, R2, Durable Objects, Queues, Workers AI, analytics binding, Logpush, external fetch, secrets, database, user accounts, or persistence. |
| Public exposure | The `workers.dev` URL is public HTTPS. The dashboard and the forecast endpoint are intentionally public; no other endpoint, custom domain, or source-data upload is exposed. |
| Cost boundary | Stay on Workers Free only: 100,000 dynamic requests/day, 10 ms CPU/request, 128 MB memory, 3 MB compressed Worker bundle, and 20,000 static assets/version. The free quota resets at midnight UTC; after exhaustion, configure fail-closed behavior so requests receive an error instead of bypassing the Worker. Never enable Workers Paid, which has a $5/month minimum. |
| Verification and release | Deploy only a committed source revision. Confirm the Worker version and source SHA in the public release evidence; verify public-aggregate data disclosures, input rejection, CORS, security headers, response correctness, and the public URL before public announcement. |
| Recovery | If verification fails, retain the Worker and its deployed versions, stop release activity, record the failure, and await human direction. Do not automatically delete or roll back resources; Cloudflare supports a deliberate rollback to a previous Worker version when directed. |

### Exact approval requested

Approve **Cloudflare Workers Free** for this public dynamic application only if
you accept a public `workers.dev` URL, quota-exhaustion errors as the hard $0
spend boundary, and the retain-on-failure policy above. Approval will replace
the AWS-in-principle hosting direction in `.project/approvals.yml` before any
Cloudflare account or resource is created.
