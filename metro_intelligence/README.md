# Metro E-commerce Intelligence Hub

Private Streamlit SIAM analysis with an executive dashboard, governed Arabic/English questions, reviewed read-only SQL plans, ingestion reconciliation, quality warnings and OIDC access control.

## Run

Python 3.12 was tested. From this directory:

```sh
python3 -m venv /tmp/metro-venv
/tmp/metro-venv/bin/pip install -r requirements.lock.txt
/tmp/metro-venv/bin/python -m unittest discover -s tests -v
/tmp/metro-venv/bin/streamlit run app.py --server.headless true
```

For personal use, see [ابدئي هنا.md](ابدئي%20هنا.md) and double-click `Start Metro.bat` (Windows) or `Start Metro.command` (macOS) after installing Python 3.12. These explicitly enable personal mode; access is allowed only with loopback server binding and loopback browser IP, and is always denied in team mode. Personal mode does not require OIDC. Launchers have not been run on Windows/macOS hardware.

For the private team site see [TEAM_DEPLOYMENT.md](TEAM_DEPLOYMENT.md), `Dockerfile`, and `compose.yaml`. These are deployment files, not a published site.

The default server binds to loopback. For deployment use a private HTTPS reverse proxy with access controls, appropriate request limits, identity-provider MFA/session policies, and restricted egress. Do not publish business data on an unauthenticated public server. The default/team server is deliberately locked until authentication is configured.

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` on the private server and supply real OIDC settings securely. Register the exact HTTPS callback with the provider. Explicitly assign verified email identities to `analyst` or `executive`; unlisted users are denied. The provider must return `email_verified=true`. Both roles can analyze; only analysts can export. Roles do not provide branch-level data isolation. Configure a trusted identity provider; role assignment is administrative. Live OIDC has not been exercised without company credentials.

No workbook or result is stored on disk or in a shared Streamlit cache. Data stays in the authenticated Streamlit session; logout clears application session state. OIDC cookies and session lifetime remain governed by Streamlit and the identity provider. Memory, infrastructure, reverse-proxy logging, backups and deployed host security require operational controls. There is no durable audit log or scheduled import yet.

## Confirmed mapping

| Source sheet (exact name) | Channel | Detail |
| --- | --- | --- |
| `Insta` | Instashop | App |
| `Online Metro` | Metro Website | Website |
| `Online Value` | valU | In-app store |
| `طلبات كاشير مترو ` (trailing space) | Talabat | Cash via rider |
| `طلبات اون لاين مترو` | Talabat | Card in Talabat |

Unknown sheets are excluded and reported. Missing mapped sheets warn. A recognized sheet missing required columns stops ingestion to avoid publishing a partial total. Numeric corruption blocks affected metrics; invalid months are warned and excluded by time filters. Repeated rows are retained and flagged, never silently removed. Negative sales are retained as potential returns/corrections. Source-row references and workbook SHA-256 identify evidence. Reconciliation compares loaded totals to source-sheet numeric totals; an independent finance control total is still needed. No year or currency is assumed from filenames. Rankings of products use article descriptions, so shared descriptions aggregate together.

## Governed assistant

The local bilingual interpreter supports recorded sales, quantity, and sales without tax; channel/month/branch/department/category/product/payment grouping; named channel and numeric month filters; and top 1–50 groups. It is rule based, not an LLM. Unsupported or unclear questions should be rephrased; always review the visible plan before execution. Arabic digit characters are accepted by Python's numeric parser. Complex time ranges and unrestricted language are not supported locally.

Optionally configure `[ai]` for an approved HTTPS OpenAI-compatible service. Users must opt in to send question text; no workbook rows or computed results are sent. Provider access is not live-tested. The LLM proposes a fixed-schema plan, never executable SQL; identifiers are allowlisted, SQL limit values parameterized, and the database is read-only during query execution. Bad model output fails closed. Review plans because valid model interpretations can still misunderstand a question. SQL, filters, matched rows, source sheets and scope totals are displayed. Dashboard filters apply first. Top-N displayed rows may not sum to the scope total.

Neither mode invents profit, orders, AOV, unique customers, forecasts, missing periods, or causes. Recommendations are conservative investigation steps. Month-over-month comparisons require consecutive observed months, a nonzero prior value, and warn about unverified completeness.

## Validation and current limitations

The original MVP startup was executed successfully before changes. Tests now use clearly synthetic five-sheet workbooks to check mapping, totals, corrupted/missing values, unsupported questions, injection rejection, evidence, roles, export escaping, mocked AI contract, anonymous locking, and dashboard/query interaction. Authentication in the authorized UI test is mocked; it does not prove live OIDC.

The supplied January–September workbook exceeded the attachment tool's 32 MiB transfer limit and has not been analyzed. Provide split or reduced exports to validate production figures and source semantics. No real business metrics have been asserted. File upload has compressed/expanded size guards, but large-workbook resource isolation should be assessed before production use. This is a tested development foundation, not a production security certification.

## Public demonstration site (no sign-in)

For non-confidential data, deploy `metro_intelligence/public_app.py` from repository branch `main` on Streamlit Community Cloud. Use Python 3.12 in Advanced settings. The root requirements.txt installs the tested lockfile. No OIDC credentials or secrets are needed. This entrypoint shows a public-data warning and allows anonymous uploads and queries; it does not create a shared gallery or retain workbooks on disk. Uploads belong to the visitor's session. Public visitors have no CSV export controls. Do not use confidential workbooks. External AI remains optional and requires separate approved server configuration and user opt-in. `app.py` remains the private entrypoint; team deployments reject the public entrypoint.

From this folder, local public-demo command: `streamlit run public_app.py`. Publishing still requires a Streamlit Cloud account connected to GitHub; a Git push alone does not create a live site.
