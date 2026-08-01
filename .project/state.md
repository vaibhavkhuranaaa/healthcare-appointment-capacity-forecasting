# Current state

- Lifecycle: M1–M5 and R1–R3 are complete
- Deployment: public Cloudflare Workers Free application verified at `https://healthcare-appointment-capacity-forecasting.vaibhavkhurana.workers.dev`
- Publication: public release verified against deployed source SHA `6e8f390`
- Contract health: public GPAD aggregate dashboard, deployment, and evidence verified
- AWS authentication check: verified read-only on 2026-07-31 for account `074642416888` in `us-east-2`. No cloud operation was attempted.
- Data-source transition: NHS GPAD April 2026 was human-approved, derived into a compact checksum-verified national fixture, and tested on 2026-07-31. The GPAD workflow and local dashboard preview are verified; the synthetic workflow is historical evidence only.
