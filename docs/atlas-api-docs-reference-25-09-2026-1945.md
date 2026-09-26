# Atlas API — full reference

**Source:** docs.mothquantum.com (Docusaurus site, generated from `moth-api v0.41.0`,
snapshot dated 2026-09-25 on the Endpoints page) and github.com/moth-quantum. Pulled
live on 25 September 2026, 19:20–19:45, by fetching every guide page and every
engine's raw `.md` export (`/engines/<slug>.md`) plus `/llms.txt` for the page index.
This is the real, published API — not third-party inference. It supersedes
`compass_artifact_wf-743a2294-0967-5f82-856f-d5384c9a3d2b_text_markdown.md`, which was
written before this site was checked and got several things wrong (see §5).

Full API reference with try-it: https://api.mothquantum.com/docs
Machine-readable spec: https://api.mothquantum.com/openapi.json
Dashboard (API keys, jobs, credits): https://platform.mothquantum.com

---

## Contents

1. Quickstart and concepts
2. Guides (auth, submitting jobs, job status, assets, errors, endpoints)
3. Engine catalog — all 20 public engines, full params
4. What's in the moth-quantum GitHub org
5. What this changes for our build plan

---

## 1. Quickstart and concepts

Run a quantum engine from your code in minutes: pick an engine, submit a job, poll, fetch the result.

```python
import time, requests

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": "Bearer MOTH_API_KEY"}

job = requests.post(f"{API}/engines/coin-toss-v1/process", headers=H, json={"params": {"shots": 10}}).json()
while requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()["status"] not in ("completed", "failed", "cancelled"): time.sleep(2)
result = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()   # {"result": {...}}
```

### Concepts

| Concept | What it is |
|---|---|
| **Engine** | A registered quantum program with a fixed `engine_id`, a JSON Schema for its `params`, and declared input/output files. Public engines are listed for everyone; private engines only for their owner. |
| **Job** | One run of an engine, identified by `job_id`. Moves `queued → processing → completed`, or ends `failed` or `cancelled`. |
| **Asset** | A file you uploaded, or a file a job produced. Identified by `asset_id`. Uploads are inputs; job outputs become assets you can download. |
| **API key** | A `moth_` bearer token created in the dashboard. Every API call carries one. |

### Basics

| | |
|---|---|
| Base URL | `https://api.mothquantum.com/api/v1` for every call. |
| Auth | `Authorization: Bearer <your key>` on every request. |
| Format | JSON in, JSON out. Errors are `application/problem+json` (RFC 7807): `title`, `status`, `detail`, `errors[]`. |
| Rate limit | 300 requests/minute per key; over that returns `429`. |
| Timeout | Each job has a `run_policy.timeout` (18000s / 5h seen on every engine checked). A run still going after that is cancelled and ends `failed`. |

---


## 2. Guides

### Getting started

Run a quantum coin toss from your terminal. Five steps, one engine that needs no file input.

#### 1. Create an API key

In the [dashboard](https://platform.mothquantum.com){target="_blank" rel="noopener noreferrer"} open **API keys** and create one. The key is shown once, then never again. Put it in your environment:

```bash
export MOTH_API_KEY="moth_…"
```

The snippets below assume the base URL `https://api.mothquantum.com/api/v1` and this header on every request: `Authorization: Bearer $MOTH_API_KEY`.

#### 2. List engines

- curl
- Python
- JavaScript

```bash
curl -s https://api.mothquantum.com/api/v1/engines \
  -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
import os, requests

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

engines = requests.get(f"{API}/engines", headers=H).json()["engines"]
print([e["engine_id"] for e in engines])
```

```javascript
const API = "https://api.mothquantum.com/api/v1";
const H = { Authorization: `Bearer ${process.env.MOTH_API_KEY}` };

const { engines } = await (await fetch(`${API}/engines`, { headers: H })).json();
console.log(engines.map(e => e.engine_id));
```

Every engine you can use, with its `engine_id`. To view the schema for a specific engine's parameters and results, visit its [Engines](/docs/engines) page or use the `GET /engines/{engine_id}` endpoint, as shown in [Reading an engine definition](/docs/working-with-engines#reading-an-engine-definition).

#### 3. Submit a job

- curl
- Python
- JavaScript

```bash
JOB_ID=$(curl -s -X POST https://api.mothquantum.com/api/v1/engines/coin-toss-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{"params": {"shots": 10}}' | jq -r .job_id)
echo $JOB_ID
```

```python
job = requests.post(f"{API}/engines/coin-toss-v1/process", headers=H,
                    json={"params": {"shots": 10}}).json()
job_id = job["job_id"]
```

```javascript
const job = await (await fetch(`${API}/engines/coin-toss-v1/process`, {
  method: "POST",
  headers: { ...H, "Content-Type": "application/json" },
  body: JSON.stringify({ params: { shots: 10 } }),
})).json();
const jobId = job.job_id;
```

```json
{"job_id": "…", "status": "queued", "submitted_at": "…"}
```

`params` is validated against the engine's schema before anything runs. An unknown or out-of-range field is a `422` listing every problem at once.

#### 4. Poll status

- curl
- Python
- JavaScript

```bash
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status \
  -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
import time

while True:
    st = requests.get(f"{API}/jobs/{job_id}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
```

```javascript
let st;
do {
  await new Promise(r => setTimeout(r, 2000));
  st = await (await fetch(`${API}/jobs/${jobId}/status`, { headers: H })).json();
} while (!["completed", "failed", "cancelled"].includes(st.status));
```

`status` goes `queued`, `processing`, then `completed` or `failed`. Poll every couple of seconds; do not busy-loop.

#### 5. Fetch the result

- curl
- Python
- JavaScript

```bash
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result \
  -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
res = requests.get(f"{API}/jobs/{job_id}/result", headers=H).json()
print(res["result"])
```

```javascript
const res = await (await fetch(`${API}/jobs/${jobId}/result`, { headers: H })).json();
console.log(res.result);
```

Coin toss returns its counts inline in `result`. Engines that produce files return an `outputs` array with a presigned download URL per file instead. See [Job status and results](/docs/job-status-and-results).

#### Next

- An engine that takes an image: [Assets](/docs/assets), then [Examples](/docs/examples).
- What every field means: its page in the [Engines](/docs/engines).


---

### Authentication

Every request carries a bearer token:

```text
Authorization: Bearer moth_…
```

#### API keys

Programmatic access uses an API key, a token starting with `moth_`. Create, disable, and revoke keys in the [dashboard](https://platform.mothquantum.com){target="_blank" rel="noopener noreferrer"}. The plaintext is shown exactly once at creation and is never stored by the platform. If you lose it, revoke it and create another.

Keys are scoped to your account: they see your private engines, your jobs, and your assets, and nothing of anyone else's. Rate limit: 300 requests per minute per key. Exceeding it returns `429`.

Keys cannot manage other keys. The key endpoints under `/api/v1/keys` accept only a dashboard session, so a leaked key cannot mint or revoke keys.

#### Dashboard sessions

The web dashboard signs in with Supabase and calls the same API with a short-lived session token. You never need one for your own code. Use a key.

#### Check who you are

- curl
- Python
- JavaScript

```bash
curl -s https://api.mothquantum.com/api/v1/me -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
import os, requests
r = requests.get("https://api.mothquantum.com/api/v1/me",
                 headers={"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"})
print(r.status_code, r.json())
```

```javascript
const r = await fetch("https://api.mothquantum.com/api/v1/me",
  { headers: { Authorization: `Bearer ${process.env.MOTH_API_KEY}` } });
console.log(r.status, await r.json());
```

Returns your user id. A `401` here means the key is invalid, disabled, or revoked.

#### Ownership and 404

Resources you do not own return `404 Not Found`, never `403`. Another user's private engine, job, asset, or key looks exactly like one that does not exist. Design retries and error handling around that: a 404 on something you created means the id is wrong, and a 404 on something you did not create is expected.

#### Keep keys out of code

Read the key from the environment or a secret store. Never commit it. If a key appears in a repository, revoke it immediately in the dashboard; there is no way to make a leaked key safe again.


---

### Submitting jobs

`POST /api/v1/engines/{engineID}/process` with a JSON body:

- curl
- Python
- JavaScript

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/blur-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{"params": {"strength": 0.5, "style": "rx"}, "input_files": {"image": "<asset_id>"}}'
```

```python
job = requests.post(f"{API}/engines/blur-v1/process", headers=H, json={
    "params": {"strength": 0.5, "style": "rx"},
    "input_files": {"image": asset_id},
}).json()
```

```javascript
const job = await (await fetch(`${API}/engines/blur-v1/process`, {
  method: "POST",
  headers: { ...H, "Content-Type": "application/json" },
  body: JSON.stringify({ params: { strength: 0.5, style: "rx" }, input_files: { image: assetId } }),
})).json();
```

Field

Required

Meaning

`params`

if the engine has parameters

Validated against the engine's `params_schema`.

`input_files`

for engines that declare input slots

Slot name to the id of an asset you uploaded and completed. See [Assets](/docs/assets).

#### What happens

1.  `params` is validated against the schema. Unknown fields fail: schemas default to `additionalProperties: false`.
2.  Each `input_files` entry is checked: the asset must exist, be yours, and be `uploaded`.
3.  The job is recorded and handed to the engine's worker.
4.  You get `202 Accepted` with a `job_id`. Nothing has run yet.

```json
{"job_id": "…", "status": "queued", "submitted_at": "2026-09-08T10:00:00Z"}
```

#### Validation errors

One `422` lists every violation, so fix them all in one round trip:

```json
{
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "validation failed",
  "errors": [
    {"location": "body.params.strength", "message": "expected number <= 1", "value": 3},
    {"location": "body.params.mode", "message": "additional properties are not allowed"}
  ]
}
```

#### Other responses

Status

Meaning

`404`

Unknown engine, or an engine you cannot see.

`415`

The engine takes files but the request carried none it could use.

`422`

Params or input files rejected. See `errors[]`.

`429`

Over 300 requests per minute on this key. Back off.

`503`

The job runtime is unavailable. Retry with backoff; nothing was recorded.

Next: [Job status and results](/docs/job-status-and-results).


---

### Job status and results

#### Status values

```text
queued ──▶ processing ──▶ completed
                     └──▶ failed
                     └──▶ cancelled
```

`completed`, `failed`, and `cancelled` are terminal and never change. A job only moves forward; a stale read never shows it going back. Workers may report transient states such as `fetching` while processing; treat anything not in the list above as `processing`.

#### Polling

- curl
- Python
- JavaScript

```bash
# JOB_ID is the job_id from your submit response
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
def wait(job_id):
    while True:
        st = requests.get(f"{API}/jobs/{job_id}/status", headers=H).json()
        if st["status"] in ("completed", "failed", "cancelled"):
            return st
        time.sleep(2)
```

```javascript
async function wait(jobId) {
  for (;;) {
    const st = await (await fetch(`${API}/jobs/${jobId}/status`, { headers: H })).json();
    if (["completed", "failed", "cancelled"].includes(st.status)) return st;
    await new Promise(r => setTimeout(r, 2000));
  }
}
```

```json
{
  "job_id": "…", "engine_id": "blur-v1", "status": "completed",
  "submitted_at": "…", "updated_at": "…",
  "outputs": [{"slot": "result", "output_asset_id": "…", "content_type": "image/png"}],
  "progress": null, "warnings": null, "error": null
}
```

- `outputs` lists each output file the job has produced so far, one per declared slot.
- `error` is set on failure: `{type, message, retryable}`. `retryable: true` means resubmitting may succeed.

Poll every two to five seconds. There is no webhook today.

`GET /jobs/{jobID}` returns the last persisted row without asking the runtime, and `GET /jobs` lists your jobs newest first with cursor pagination. Use them for history; use `/status` for live state.

#### Fetching the result

- curl
- Python
- JavaScript

```bash
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
res = requests.get(f"{API}/jobs/{job_id}/result", headers=H).json()
for out in res.get("outputs") or []:
    open(out["slot"], "wb").write(requests.get(out["url"]).content)
print(res.get("result"))
```

```javascript
const res = await (await fetch(`${API}/jobs/${jobId}/result`, { headers: H })).json();
for (const out of res.outputs ?? []) {
  const bytes = Buffer.from(await (await fetch(out.url)).arrayBuffer());
  await fs.promises.writeFile(out.slot, bytes);
}
console.log(res.result);
```

Two shapes, decided by the engine:

**File outputs.** One entry per declared output slot, each with a presigned `url` that needs no auth header and expires at `expires_at`. Every output is also an asset you own, so it is listed under your assets and can be downloaded again later.

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345678",
      "filename": "blur-v1-1b9d6bcd-result.png",
      "content_type": "image/png",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

**Inline result.** Engines that produce no files return JSON in `result`. This lives with the job runtime and is not kept as an asset.

```json
{"result": {"counts": {"0": 4, "1": 6}}}
```

#### Result status codes

Status

Meaning

`409`

Not finished yet, or the job failed. Check `/status`.

`410`

Finished, but no result is retrievable any more. File outputs survive as assets; an inline result that has aged out of the runtime is gone.

`404`

Not your job, or no such job.

#### Retention

File outputs are stored as assets and count toward your [storage quota](/docs/assets#quotas). Delete them like any asset when you no longer need them. Inline JSON results are retained only for a limited time by the job runtime; copy what you need when you fetch it.


---

### Assets

An asset is a file the platform stores for you: either an input you uploaded or an output a job produced. File bytes never pass through the API. Uploads go straight to object storage through a presigned URL, and downloads come back the same way.

#### Uploading, in three calls

- curl
- Python
- JavaScript

```bash
# 1. Register the upload
ASSET=$(curl -s -X POST https://api.mothquantum.com/api/v1/assets \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d "{\"filename\": \"image.png\", \"content_type\": \"image/png\", \"size_bytes\": $(stat -f%z image.png)}")
ASSET_ID=$(echo "$ASSET" | jq -r .asset_id)

# 2. PUT the bytes with exactly the returned headers (Content-Type shown; copy any others from upload.headers)
curl -s -X PUT "$(echo "$ASSET" | jq -r .upload.url)" -H "Content-Type: image/png" --data-binary @image.png

# 3. Complete
curl -s -X POST https://api.mothquantum.com/api/v1/assets/$ASSET_ID/complete -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
import os, requests
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

path = Path("image.png"); data = path.read_bytes()

# 1. Register the upload. content_type and size_bytes are signed into the URL.
asset = requests.post(f"{API}/assets", headers=H, json={
    "filename": path.name, "content_type": "image/png", "size_bytes": len(data)}).json()

# 2. PUT the bytes to the presigned URL with exactly the headers returned.
requests.put(asset["upload"]["url"], data=data, headers=asset["upload"]["headers"]).raise_for_status()

# 3. Complete. The platform verifies size and type; the asset becomes "uploaded".
requests.post(f"{API}/assets/{asset['asset_id']}/complete", headers=H).raise_for_status()

asset["asset_id"]   # pass this in a job's input_files
```

```javascript
import fs from "node:fs/promises";

const API = "https://api.mothquantum.com/api/v1";
const H = { Authorization: `Bearer ${process.env.MOTH_API_KEY}` };

const data = await fs.readFile("image.png");

// 1. Register the upload. content_type and size_bytes are signed into the URL.
const asset = await (await fetch(`${API}/assets`, {
  method: "POST", headers: { ...H, "Content-Type": "application/json" },
  body: JSON.stringify({ filename: "image.png", content_type: "image/png", size_bytes: data.byteLength }),
})).json();

// 2. PUT the bytes to the presigned URL with exactly the headers returned.
await fetch(asset.upload.url, { method: "PUT", headers: asset.upload.headers, body: data });

// 3. Complete. The platform verifies size and type; the asset becomes "uploaded".
await fetch(`${API}/assets/${asset.asset_id}/complete`, { method: "POST", headers: H });

asset.asset_id;   // pass this in a job's input_files
```

Rules that trip people up:

- The PUT must send the exact `Content-Type` and `Content-Length` you declared. Storage rejects a mismatch.
- The upload URL expires; `upload.expires_at` tells you when. Register again if it lapses.
- Until you call complete, the asset is `pending`, cannot be used in a job, and still counts toward quota.
- Images are checked at completion. Accepted image types are `image/png` and `image/jpeg` for uploads that get scanned; a rejected image fails complete with a `422` and a reason.
- Maximum upload size is 100 MiB, lower for scanned images.

#### Using an asset in a job

Put the id under the engine's input slot name:

```json
{"params": {"strength": 0.5}, "input_files": {"image": "<asset_id>"}}
```

The engine's [catalog page](/docs/engines) lists slot names and accepted types.

#### Downloading

- curl
- Python
- JavaScript

```bash
curl -s https://api.mothquantum.com/api/v1/assets/$ASSET_ID/download -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
dl = requests.get(f"{API}/assets/{asset_id}/download", headers=H).json()
Path("out.png").write_bytes(requests.get(dl["download_url"]).content)
```

```javascript
const dl = await (await fetch(`${API}/assets/${assetId}/download`, { headers: H })).json();
await fs.writeFile("out.png", Buffer.from(await (await fetch(dl.download_url)).arrayBuffer()));
```

Returns `download_url` and `expires_at`. Fetch the bytes from that URL with no auth header. Works for uploads and for job outputs alike; a job's result response includes these URLs already.

#### Listing and deleting

`GET /assets?kind=upload|output` lists your assets with cursor pagination. `DELETE /assets/{assetID}` removes the object and its record. Deleting an output does not affect the job record.

#### Quotas

- curl
- Python
- JavaScript

```bash
curl -s https://api.mothquantum.com/api/v1/me/storage -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
print(requests.get(f"{API}/me/storage", headers=H).json())
```

```javascript
console.log(await (await fetch(`${API}/me/storage`, { headers: H })).json());
```

Two limits, fixed per account when first used: an upload quota and a total quota across uploads and job outputs. Create-asset is refused past the upload quota; submitting a job is refused at or past the total. Pending uploads count until completed or deleted, so clean up abandoned registrations.

#### Reference

[Create an asset](/docs/endpoints), [Complete an upload](/docs/endpoints), [Get a download URL](/docs/endpoints), [List assets](/docs/endpoints), [Delete an asset](/docs/endpoints), [Storage usage](/docs/endpoints).


---

### Engines

An engine is a registered quantum program. The catalog tells you what each one accepts and produces; the [Engines](/docs/engines) renders the same data as pages.

#### Reading an engine definition

- curl
- Python
- JavaScript

```bash
curl -s https://api.mothquantum.com/api/v1/engines/blur-v1 -H "Authorization: Bearer $MOTH_API_KEY"
```

```python
engine = requests.get(f"{API}/engines/blur-v1", headers=H).json()
print(engine["params_schema"], engine["input_files"], engine["output_files"])
```

```javascript
const engine = await (await fetch(`${API}/engines/blur-v1`, { headers: H })).json();
console.log(engine.params_schema, engine.input_files, engine.output_files);
```

The fields you use when calling it:

Field

Meaning

`engine_id`

The id in the URL, for example `blur-v1`.

`params_schema`

JSON Schema for the `params` object you send. Unknown fields are rejected.

`input_files`

Named file slots the engine reads. Each has accepted MIME types and whether it is required. You upload the file as an asset and pass its id under the slot name.

`output_files`

Named output slots the engine writes. Each completed job returns one asset per slot.

`credits_per_run`

Cost of one job.

`run_policy.timeout`

Seconds a run may take before it fails.

`error_codes`

Engine-specific failure codes you may see in a `422`.

`visibility`, `owner`

`public` engines are visible to everyone. `private` ones only to their owner.

The fields `queue`, `sidecar_endpoint`, `has_*` and `estimate*` are internal to the runtime. Ignore them.

#### Public and private

Listing engines returns every public engine plus your own private ones. Another user's private engine is a `404`. There is no way to discover it, and no `403` that would confirm it exists.

#### Publishing your own engine

Engines are registered with `POST /api/v1/engines` and updated with `PATCH /api/v1/engines/{engineID}`. New engines default to `visibility: private` and `credits_per_run: 1`. The `engine_id` and `owner` are fixed at creation. Built-in engines owned by `moth` cannot be changed through the API.

Registering the definition is the catalog half. The engine's worker is deployed separately; see the engine authoring guides in the moth-quantum GitHub organisation. Until a worker is running, jobs for the engine queue and time out.

#### Reference

- [List engines](/docs/endpoints#engines), [Get engine](/docs/endpoints#engines), [Create engine](/docs/endpoints#engines), [Update engine](/docs/endpoints#engines).


---

### Errors and rate limits

Every error is `application/problem+json` (RFC 7807):

```json
{
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "validation failed",
  "errors": [
    {"location": "body.params.shots", "message": "expected integer >= 1", "value": 0}
  ]
}
```

`errors[]` is present when there is more than one thing to say, each with a `location` in the request, a `message`, and the offending `value`.

#### Status codes

Status

When

What to do

`401`

Missing, invalid, disabled, or revoked key

Check the `Authorization` header and the key in the dashboard.

`404`

The resource does not exist, or is not yours

Never a `403`. See [Authentication](/docs/authentication#ownership-and-404).

`409`

Wrong state: result not ready, upload already completed

Poll status, or stop retrying the completed action.

`410`

Result no longer retrievable

Use the output assets if the engine produced files.

`415`

Engine needs files the request did not provide

Upload assets and pass them in `input_files`.

`422`

Validation failed

Read `errors[]`; fix every entry. For jobs, engine-specific codes appear in `errors[].message`.

`429`

Rate limit

Wait and retry with backoff.

`502`

Upstream storage or key service failed

Retry.

`503`

Job runtime unavailable

Retry with backoff; the job was not recorded.

`500`

Unexpected

Retry once; report if it persists.

#### Engine errors on a job

A job that fails during processing shows `status: failed` and an `error` object on `/status`:

```json
{"status": "failed", "error": {"type": "processing_failed", "message": "…", "retryable": false}}
```

Each engine's catalog page lists its `error_codes`. `retryable: true` means the same submission may succeed if repeated.

#### Rate limits

300 requests per minute per API key. A `429` carries no reset header today, so back off for a few seconds and retry. Polling every two to five seconds stays well inside the limit.

#### Reporting a problem

Include the `job_id` or `asset_id`, the timestamp, and the full error body. Never include your API key.


---

### Examples

Two complete scripts, one per engine shape. Each is runnable with `MOTH_API_KEY` set. Every engine page in the [catalog](/docs/engines) carries the same script filled in with that engine's own parameters.

#### JSON in, JSON out

`coin-toss-v1`: no files, inline result.

- Python
- JavaScript

```python
import os, time, requests

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

def wait(job_id):
    while True:
        st = requests.get(f"{API}/jobs/{job_id}/status", headers=H).json()
        if st["status"] in ("completed", "failed", "cancelled"):
            return st
        time.sleep(2)

job = requests.post(f"{API}/engines/coin-toss-v1/process", headers=H,
                    json={"params": {"shots": 100}}).json()
st = wait(job["job_id"])
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")
print(requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()["result"])
```

```javascript
const API = "https://api.mothquantum.com/api/v1";
const H = { Authorization: `Bearer ${process.env.MOTH_API_KEY}` };

async function wait(jobId) {
  for (;;) {
    const st = await (await fetch(`${API}/jobs/${jobId}/status`, { headers: H })).json();
    if (["completed", "failed", "cancelled"].includes(st.status)) return st;
    await new Promise(r => setTimeout(r, 2000));
  }
}

const job = await (await fetch(`${API}/engines/coin-toss-v1/process`, {
  method: "POST", headers: { ...H, "Content-Type": "application/json" },
  body: JSON.stringify({ params: { shots: 100 } }),
})).json();
const st = await wait(job.job_id);
if (st.status !== "completed") throw new Error(JSON.stringify(st.error));
console.log((await (await fetch(`${API}/jobs/${job.job_id}/result`, { headers: H })).json()).result);
```

#### File in, file out

`blur-v1`: upload an image, blur it, download the result.

- Python
- JavaScript

```python
import os, time, requests
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

def upload(path: Path, content_type: str) -> str:
    data = path.read_bytes()
    a = requests.post(f"{API}/assets", headers=H, json={
        "filename": path.name, "content_type": content_type, "size_bytes": len(data)}).json()
    requests.put(a["upload"]["url"], data=data, headers=a["upload"]["headers"]).raise_for_status()
    requests.post(f"{API}/assets/{a['asset_id']}/complete", headers=H).raise_for_status()
    return a["asset_id"]

def wait(job_id):
    while True:
        st = requests.get(f"{API}/jobs/{job_id}/status", headers=H).json()
        if st["status"] in ("completed", "failed", "cancelled"):
            return st
        time.sleep(2)

image_id = upload(Path("photo.png"), "image/png")

job = requests.post(f"{API}/engines/blur-v1/process", headers=H, json={
    "params": {"strength": 0.5, "style": "rx", "size": 1024},
    "input_files": {"image": image_id},
}).json()

st = wait(job["job_id"])
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:                       # blur-v1 declares one slot: "result"
    Path(f"{out['slot']}.png").write_bytes(requests.get(out["url"]).content)
```

```javascript
import fs from "node:fs/promises";

const API = "https://api.mothquantum.com/api/v1";
const H = { Authorization: `Bearer ${process.env.MOTH_API_KEY}` };

async function upload(path, contentType) {
  const data = await fs.readFile(path);
  const a = await (await fetch(`${API}/assets`, {
    method: "POST", headers: { ...H, "Content-Type": "application/json" },
    body: JSON.stringify({ filename: path, content_type: contentType, size_bytes: data.byteLength }),
  })).json();
  await fetch(a.upload.url, { method: "PUT", headers: a.upload.headers, body: data });
  await fetch(`${API}/assets/${a.asset_id}/complete`, { method: "POST", headers: H });
  return a.asset_id;
}

async function wait(jobId) {
  for (;;) {
    const st = await (await fetch(`${API}/jobs/${jobId}/status`, { headers: H })).json();
    if (["completed", "failed", "cancelled"].includes(st.status)) return st;
    await new Promise(r => setTimeout(r, 2000));
  }
}

const imageId = await upload("photo.png", "image/png");

const job = await (await fetch(`${API}/engines/blur-v1/process`, {
  method: "POST", headers: { ...H, "Content-Type": "application/json" },
  body: JSON.stringify({ params: { strength: 0.5, style: "rx", size: 1024 }, input_files: { image: imageId } }),
})).json();

const st = await wait(job.job_id);
if (st.status !== "completed") throw new Error(JSON.stringify(st.error));

const res = await (await fetch(`${API}/jobs/${job.job_id}/result`, { headers: H })).json();
for (const out of res.outputs) {                 // blur-v1 declares one slot: "result"
  await fs.writeFile(`${out.slot}.png`, Buffer.from(await (await fetch(out.url)).arrayBuffer()));
}
```

#### Patterns worth copying

- Treat `failed` and `cancelled` as terminal and read `error` before deciding to resubmit.
- Upload once, submit many. An asset id can be reused across jobs.
- Delete output assets you have downloaded; they count toward your quota.


---

### Endpoints reference

Base URL `https://api.mothquantum.com/api/v1`, bearer auth on every call. 56 operations
total as of the 2026-09-25 snapshot; the ones that matter for our pipeline:

#### auth

| Method | Path | Does |
|---|---|---|
| GET | `/me` | Current user identity. `401` here means the key is invalid/disabled/revoked. |

#### engines

| Method | Path | Does |
|---|---|---|
| GET | `/engines` | List visible engines (public + your private ones), by ID ascending. |
| GET | `/engines/{engineID}` | Full definition of one engine: `params_schema`, `input_files`, `output_files`, `credits_per_run`, `run_policy.timeout`, `error_codes`, `visibility`. |
| POST | `/engines` | Register your own engine (defaults to `visibility: private`, 1 credit/run). Registering the definition ≠ deploying a worker — until a worker runs, its jobs queue forever. |
| PATCH | `/engines/{engineID}` | Update an engine you own. |

#### jobs

| Method | Path | Does |
|---|---|---|
| POST | `/engines/{engineID}/process` | **Submit a job.** Body: `{"params": {...}, "input_files": {...}}`. Validates against the engine's schema, returns `202` + `job_id`. Nothing has run yet. |
| GET | `/jobs/{jobID}/status` | **Live status.** Poll this, not `/jobs/{jobID}`, for current state. |
| GET | `/jobs/{jobID}` | Last *persisted* row, no live runtime query. Use for history, not polling. |
| GET | `/jobs/{jobID}/result` | Completed job's outputs: one entry per output slot with a presigned `url`, or the inline `result` JSON. `409` if not finished, `410` if aged out. |
| GET | `/jobs` | List your jobs, newest first, cursor pagination. |

#### assets

| Method | Path | Does |
|---|---|---|
| POST | `/assets` | Register an upload; returns a presigned `upload.url` + `upload.headers`. |
| POST | `/assets/{assetID}/complete` | Finalize after the PUT. Asset becomes `uploaded` and usable in a job. |
| GET | `/assets/{assetID}/download` | Presigned `download_url`, no auth needed to fetch it. |
| GET | `/assets` | List your assets (`?kind=upload|output`), cursor pagination. |
| DELETE | `/assets/{assetID}` | Remove the object + record. Doesn't affect the job that produced it. |
| GET | `/me/storage` | Storage usage vs quota (upload quota + total quota). |

#### Not relevant to a weekend hackathon build

`keys` (mint/revoke API keys — do this once in the dashboard, not from code),
`showcases` (link a deployed app in the platform gallery), `organizations` and
`permissions` (team/multi-user access control — we're solo).



---

## 3. Engine catalog

20 public engines as of 2026-09-25. Full detail for each is in the sub-sections below —
this table is for picking which ones matter to our project at a glance.

| Slug | Name | Shape | Credits/run | Relevant to our plan |
|---|---|---|---|---|
| `telablur-v1` | Quantum Teleblur | Image → Image | 1 | **Yes — core of the recursive chain (Beginner 01, Int. 01/03)** |
| `blur-v1` | Quantum Blur | Image → Image | 1 | Yes — daisy chain, alt. to Telablur |
| `blur-core-v1` | Quantum Blur Core | JSON (N-D grid) → JSON | 1 | Maybe — generic blur on arrays, not images |
| `blur-midi-v1` | Blur Jazz | Audio (MIDI) → Audio | 1 | No — MIDI only, we're using WAV/recordings |
| `deep-fryer-v1` | Deep Fryer | Image → Image | 1 | Maybe — fun daisy-chain filler |
| `entanglement-shader-v1` | Entanglement Shader | JSON → File (ZIP) | 1 | **Yes — dodecahedron material (Beginner 03)** — outputs shader code, not a texture, see §5 |
| `tessa-image-v1` | Tessa Image | Image → Image | 1 | Yes — named in build plan's daisy chain |
| `coin-toss-v1` | Coin Toss | JSON → JSON (inline) | 2 | Yes — overnight fallback pool, daisy chain filler |
| `qrc-audio-v1` | QRC Audio | Audio → Audio | 5 | **Yes — audio engine (Beginner 02)**, expensive |
| `otoc-echo-v1` | Quantum Echo | JSON → JSON | 1 | Yes — the "Quantum Echo" named in our plan |
| `retrocausal-echo-v1` | Retrocausal Echo | Audio → Audio | 2 | Maybe — possibly what "Quantum Echo" actually refers to; see §5 |
| `qpixl-v1` | Qpixl | JSON → JSON | 1 | Yes — named in build plan's daisy chain |
| `qdrive-api-v1` | QDrive | Text → Text | 1 | No — circuit-by-expectation-values, not our use case |
| `graph-v1` | Quantum Graph Engine | JSON → JSON | 5 | No — graph state sampling, not used in our plan |
| `labyrinth-v1` | Quantum Labyrinth Engine | JSON → JSON | 5 | No — maze generation for games (used by `coccoon`) |
| `qrc-midi-v1` | QRC MIDI | Audio (MIDI) → Audio | 5 | No — MIDI |
| `qrc-train-v2` | QRC Train | JSON → JSON | 5 | No — two-stage QRC generation, not needed |
| `qrc-gen-v2` | QRC Generate | File → JSON | 1 | No — pairs with qrc-train-v2 |
| `tomography-api-v2` | Tomography Api | JSON → JSON | 1 | No — circuit analysis tool |
| `tamagotchi-v1` | Tamagotchi | JSON → JSON | 0 (free) | No — joke engine, but free if we want a 9th daisy-chain credit for nothing |


### Quantum Teleblur — `telablur-v1`

POST https://api.mothquantum.com/api/v1/engines/telablur-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>telablur-v1</code></dd></div>

  <div><dt>Publisher</dt><dd>Moth</dd></div>
  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 9, 2026</dd></div>
</dl>

Quantum Teleblur — morphs one image into another through qubit rotations.

#### Request

`POST /api/v1/engines/telablur-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "direction": "full",
    "downscale": true,
    "mask_bin_size": 4,
    "mask_min_region": 16,
    "size": 1024,
    "strength": 0.5
  },
  "input_files": {
    "image1": "9f8e7d6c-5b4a-4d21-8abc-def012345678",
    "image2": "9f8e7d6c-5b4a-4d21-8abc-def012345678"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `direction` | string | no | `"full"` | Which qubits receive the blur rotation, controlling the spatial direction of the blur effect:  - `full` — all pixel qubits are rotated, producing blur in both directions (default). - `vertical` — only the y-encoding qubits are rotated; the blur spreads vertically. - `horizontal` — only the x-encoding qubits are rotated; the blur spreads horizontally. (one of `full`, `vertical`, `horizontal`) |
| `downscale` | boolean | no | `true` | If True, oversized regions are downscaled before teleport and upscaled back. If False, oversized regions are tiled into adjacent sub-images. |
| `mask_bin_size` | number \| null | no | `4` | Mask quantisation step as a percentage of 255 (0–100). Pixel values below this threshold are treated as background, preventing near-zero JPEG/WebP compression artifacts from being detected as separate mask regions. Default 4 (~10/255). |
| `mask_min_region` | integer \| null | no | `16` | Minimum mask region size in pixels. Connected components smaller than this are discarded after quantisation, removing residual compression artifacts that survive the binning step. Default 16. |
| `size` | integer | no | `1024` | Pixel budget per teleblur pass: a region up to `size × size` pixels is teleported in a single pass. Must be between 8 and 1024. Default 1024. (min 8, max 1024) |
| `strength` | number | no | `0.5` | Strength of the teleportation effect, between 0.0 and 1.0 (min 0, max 1) |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `image1` | `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp` | yes | The source image. The teleblur effect morphs this image toward image2 through quantum rotation gates. Supported formats: PNG, JPEG, WebP, TIFF, BMP. |
| `image2` | `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp` | yes | The target image. The teleblur effect morphs image1 toward this image. If the dimensions differ from image1, image2 is resized to match before processing. |
| `mask` | `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp` | no | Optional mask controlling where the effect is applied, on a per-pixel basis. Must match the size of `image1`. Each output pixel is a soft blend `C = m · C_teleblurred + (1 - m) · C_image1`, where `m` is the normalised mask intensity at that pixel: black keeps image1, white takes the fully teleblurred result, and grey values blend smoothly between the two. Single-channel masks are used directly; RGB masks are converted to luminance.  **Alpha-channel fallback**  If no mask is provided, the alpha channel of `image1` is used instead (transparent pixels keep image1, opaque pixels are teleblurred). For RGB input with no alpha channel, the whole image is teleblurred.  |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "telablur-v1-1b9d6bcd-result.png",
      "content_type": "image/png",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 18000 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp` | yes | The processed image. |

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_image1` | The first image file could not be decoded. |
| `invalid_image2` | The second image file could not be decoded. |
| `mask_size_mismatch` | Mask dimensions do not match image1 dimensions. |
| `no_mask_region` | The provided mask has no non-zero pixels — nothing to teleblur. |
| `invalid_params` | One or more params fields failed Pydantic validation. |
| `processing_failed` | The quantum teleport circuit failed during processing. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Upload the input as an asset (slot "image1": image/png, image/jpeg, image/webp, image/tiff, image/bmp)
#    Optional slots not shown: mask
path = Path("input.png"); data = path.read_bytes()
asset = requests.post(f"{API}/assets", headers=H,
    json={"filename": path.name, "content_type": "image/png", "size_bytes": len(data)}).json()
requests.put(asset["upload"]["url"], data=data, headers=asset["upload"]["headers"]).raise_for_status()
requests.post(f"{API}/assets/{asset['asset_id']}/complete", headers=H).raise_for_status()
asset_id = asset["asset_id"]

# 2. Submit to telablur-v1
job = requests.post(f"{API}/engines/telablur-v1/process", headers=H,
    json={
        "params": {
            "direction": "full",
            "downscale": True,
            "mask_bin_size": 4,
            "mask_min_region": 16,
            "size": 1024,
            "strength": 0.5
        },
        "input_files": {
            "image1": asset_id,
            "image2": asset_id
        }
    }).json()

# 3. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 4. Fetch the result — output slots: result
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
# Upload first — see the Assets guide; put the returned asset_id in input_files.
curl -s -X POST https://api.mothquantum.com/api/v1/engines/telablur-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "direction": "full",
    "downscale": true,
    "mask_bin_size": 4,
    "mask_min_region": 16,
    "size": 1024,
    "strength": 0.5
  },
  "input_files": {
    "image1": "$ASSET_ID",
    "image2": "$ASSET_ID"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Both images are placed into a shared quantum state on n+1 qubits, where n
encodes the image pixels and one extra selector qubit identifies each image.
Rotating the selector qubit interpolates between the two images at the
amplitude level.

##### Notes

- An optional `mask` selects where the effect is applied. If omitted,
  image1's alpha channel is used (RGBA) or the full image (RGB).
- The two images must share the same dimensions; mismatched sizes are
  rejected.
- Disjoint mask regions are processed independently from their bounding
  boxes.
- The simulator caps each region at `2 ** max_qubits` pixels. When a region
  exceeds that, `downscale=True` does downscale → teleport → upscale;
  `downscale=False` tiles the region. Output always matches input dimensions.
- The output is the composition (1-mask)·image1 + mask·teleblurred, where the
  teleblurred alpha is alpha1·(1-strength) + alpha2·strength.

#### Related engines

- [Quantum Blur](/docs/engines/blur-v1) — `blur-v1`, Image → Image
- [Tessa Image](/docs/engines/tessa-image-v1) — `tessa-image-v1`, Image → Image
- [Deep Fryer](/docs/engines/deep-fryer-v1) — `deep-fryer-v1`, Image → Image
- [Blur Jazz](/docs/engines/blur-midi-v1) — `blur-midi-v1`, Audio → Audio


---

### Quantum Blur — `blur-v1`

POST https://api.mothquantum.com/api/v1/engines/blur-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>blur-v1</code></dd></div>
  <div><dt>Version</dt><dd>v1.1.9</dd></div>

  <div><dt>Publisher</dt><dd>Moth</dd></div>
  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 10, 2026</dd></div>
</dl>

Blur an image with a quantum rotation and get back an image of the same size and format, optionally only inside a masked region.

#### Request

`POST /api/v1/engines/blur-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "downscale": true,
    "mask_bin_size": 4,
    "mask_min_region": 16,
    "reach": 0,
    "size": 1024,
    "strength": 0.5,
    "style": "rx"
  },
  "input_files": {
    "image": "9f8e7d6c-5b4a-4d21-8abc-def012345678"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `downscale` | boolean | no | `true` | Strategy used when a mask region is larger than the maximum number of qubits allows:  - `true` — the region is downscaled to fit, blurred, and upscaled back. - `false` — the region is split into adjacent tiles that are blurred independently. |
| `mask_bin_size` | number \| null | no | `4` | Mask quantisation step as a percentage of 255 (0–100). Pixel values below this threshold are treated as background, preventing near-zero JPEG/WebP compression artifacts from being detected as separate mask regions. Default 4 (~10/255). |
| `mask_min_region` | integer \| null | no | `16` | Minimum mask region size in pixels. Connected components smaller than this are discarded after quantisation, removing residual compression artifacts that survive the binning step. Default 16. |
| `reach` | number | no | `0` | Controls how far from its original position a pixel can be affected by the blur:  - `0` — fully local: only nearby pixels are affected (default). - `1` — fully non-local: pixels anywhere on the canvas can be affected equally. (min 0, max 1) |
| `size` | integer | no | `1024` | Pixel budget per blur pass: a region up to `size × size` pixels is blurred in a single pass. Internally converted to a qubit budget via `ceil(log2(size)) * 2`. Must be between 8 and 1024. Default 1024. (min 8, max 1024) |
| `strength` | number | no | `0.5` | Strength of the effect, which controls the rotation applied to each qubit:  - `0` — the image is left unchanged. - `1` — maximum blur. (min 0, max 1) |
| `style` | string | no | `"rx"` | Quantum gate used to apply the effect:  - `rx` — rotation around the x-axis of the Bloch sphere. - `ry` — rotation around the y-axis of the Bloch sphere. (one of `rx`, `ry`) |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `image` | `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp` | yes | The image of your choice. The blur effect is applied RGB pixel values only, not the alpha channel. It means that if you submitted a PNG with transparent background, the background from the output will also be transparent. |
| `mask` | `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp` | no | Optional mask controlling where the effect is applied, on a per-pixel basis. Must match the size of `image`. Each output pixel is a soft blend `C = m · C_blurred + (1 - m) · C_original`, where `m` is the normalised mask intensity at that pixel: black keeps the original, white takes the fully blurred version, and grey values blend smoothly between the two. Single-channel masks are used directly; RGB masks are converted to luminance.  **Alpha-channel fallback**  If no mask is provided, the alpha channel of `image` is used instead (transparent pixels keep the original, opaque pixels are blurred). For RGB input with no alpha channel, the whole image is blurred.  |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "blur-v1-1b9d6bcd-result.png",
      "content_type": "image/png",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 300 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp` | yes | The processed image. |

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `mask_size_mismatch` | Mask dimensions do not match the image dimensions. |
| `no_mask_region` | The provided mask has no non-zero pixels — nothing to blur. |
| `invalid_params` | One or more params fields failed Pydantic validation. |
| `invalid_image` | The image or mask file could not be decoded. |
| `blur_failed` | The quantum blur circuit failed on a mask region. |
| `region_extraction_failed` | A mask region could not be extracted from the image (e.g. an invalid bounding box). |
| `compose_failed` | A blurred region could not be blended back into the output image. |
| `encoding_failed` | The output image could not be encoded in the input's format. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Upload the input as an asset (slot "image": image/png, image/jpeg, image/webp, image/tiff, image/bmp)
#    Optional slots not shown: mask
path = Path("input.png"); data = path.read_bytes()
asset = requests.post(f"{API}/assets", headers=H,
    json={"filename": path.name, "content_type": "image/png", "size_bytes": len(data)}).json()
requests.put(asset["upload"]["url"], data=data, headers=asset["upload"]["headers"]).raise_for_status()
requests.post(f"{API}/assets/{asset['asset_id']}/complete", headers=H).raise_for_status()
asset_id = asset["asset_id"]

# 2. Submit to blur-v1
job = requests.post(f"{API}/engines/blur-v1/process", headers=H,
    json={
        "params": {
            "downscale": True,
            "mask_bin_size": 4,
            "mask_min_region": 16,
            "reach": 0,
            "size": 1024,
            "strength": 0.5,
            "style": "rx"
        },
        "input_files": {
            "image": asset_id
        }
    }).json()

# 3. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 4. Fetch the result — output slots: result
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
# Upload first — see the Assets guide; put the returned asset_id in input_files.
curl -s -X POST https://api.mothquantum.com/api/v1/engines/blur-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "downscale": true,
    "mask_bin_size": 4,
    "mask_min_region": 16,
    "reach": 0,
    "size": 1024,
    "strength": 0.5,
    "style": "rx"
  },
  "input_files": {
    "image": "$ASSET_ID"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Each pixel's brightness is encoded into a quantum state, one rotation gate is
applied per qubit, and the state is read back into pixels. Because a single gate
moves weight across many pixels at once, the blur spreads as interference echoes
rather than a soft focus: shapes reappear faintly elsewhere on the canvas.
Colour images are processed one channel at a time; the alpha channel is untouched.

##### How it works

1. Reads `image` and, if given, `mask`. Without a mask the alpha channel selects
   the region; RGB input with no alpha is blurred everywhere.
2. Splits the mask into connected regions and, for each, encodes the pixels into
   a statevector, applies the `style` rotation at the given `strength`, and reads
   the result back. Regions larger than `size` are downscaled or tiled per
   `downscale`.
3. Blends each blurred region with the original by mask intensity and writes the
   image in the input's format and dimensions.

##### Output

One file in slot `result`: same format, dimensions and alpha channel as `image`.

##### Limits

- Runs on a classical statevector simulator, not a QPU. Memory and time grow with
  region size; a 1024 x 1024 region uses 20 qubits.
- `strength` above 1 (with `reach` 0) starts to reverse the effect.
- `ry` on smooth gradients can collapse to a mostly dark image; prefer `rx` there.

##### Further reading

- [QuantumBlur library](https://github.com/qiskit-community/QuantumBlur): the
  encoding and rotation this engine wraps.
- [ILA, Recurse](https://infinite.mothquantum.com): the album produced with this
  colour-channel technique.

#### Related engines

- [Quantum Teleblur](/docs/engines/telablur-v1) — `telablur-v1`, Image → Image
- [Tessa Image](/docs/engines/tessa-image-v1) — `tessa-image-v1`, Image → Image
- [Deep Fryer](/docs/engines/deep-fryer-v1) — `deep-fryer-v1`, Image → Image
- [Blur Jazz](/docs/engines/blur-midi-v1) — `blur-midi-v1`, Audio → Audio


---

### Quantum Blur Core — `blur-core-v1`

POST https://api.mothquantum.com/api/v1/engines/blur-core-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>blur-core-v1</code></dd></div>

  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 8, 2026</dd></div>
</dl>

A unitary, information-preserving blur driven by quantum interference —
applied to an arbitrary N-dimensional grid of numbers, not to image files.

#### Request

`POST /api/v1/engines/blur-core-v1/process` with a JSON body:

```json
{
  "params": {
    "max_qubits": 20,
    "reach": 0,
    "strength": 0.5,
    "style": "x"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `axes` | array \| null | no | `null` | Which axes of `values` to blur along. `null` (default) blurs every axis. E.g. for a 2-D grid, `[0]` blurs only along axis 0, leaving axis 1 untouched. Negative indices count from the end, as in numpy. |
| `max_qubits` | integer | no | `20` | Safety cap on the total number of qubits `values`'s shape is allowed to require. A 1024x1024 2-D grid costs 20 qubits; a flat 1D list of up to 2**20 numbers also costs 20. Default 20, max 24. (min 1, max 24) |
| `reach` | number | no | `0` | Controls how far from its original position a value can be affected by the blur:  - `0` — fully local: only neighbouring grid points are affected (default). - `1` — fully non-local: any point on the grid can be affected equally. (min 0, max 1) |
| `shots` | integer \| null | no | `null` | If given, the grid is recovered from this many simulated projective measurements, introducing shot noise. If omitted (default), the exact (infinite-shot) probabilities are used. |
| `strength` | number \| array | no | `0.5` | Strength of the effect, which controls the rotation applied to each qubit:  - `0` — the values are left unchanged. - `1` — maximum blur.  A single number applies to every axis identically. A list applies per axis instead — one entry per axis in `axes` (or, if `axes` is omitted, one per axis of `values`) — so e.g. one axis can be left at `0` (untouched) while another is fully blurred. |
| `style` | string | no | `"x"` | Quantum gate(s) used to apply the effect: any non-empty combination of the letters `x`, `y`, each selecting a rotation around that axis of the Bloch sphere (Rx/Ry). Every qubit gets the gates in `style` applied in order, left to right, all using the same angle for that qubit — e.g. `"xy"` applies Rx then Ry to each qubit, both by the same amount. `style` picks which gates run; `strength` (below) picks how hard, per axis. (pattern `^[xy]+$`) |
| `values` | array | no |  | An arbitrarily nested list of non-negative numbers. The nesting depth is the grid's dimensionality: a flat list is 1-D, a list of lists is 2-D, etc. Must be rectangular (non-ragged). |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": null,
  "result": "<engine-specific JSON — fields below>"
}
```

Returns a JSON list, nested to the same shape as the input `values`, with
each entry rescaled relative to the input's maximum (an exact round-trip
when `strength` is `0`).

A run still going after 300 s is cancelled and the job ends `failed`.

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_params` | One or more params fields failed Pydantic validation. |
| `invalid_values` | `values` was not a rectangular nested list of non-negative numbers (ragged nesting, non-numeric entries, or a negative value). |
| `too_many_qubits` | The shape of `values` requires more qubits than `max_qubits` allows. |
| `invalid_axes` | One or more entries in `axes` is out of range for the dimensionality of `values`. |
| `invalid_strength` | `strength` was given as a list whose length doesn't match the number of targeted axes (the length of `axes`, or the dimensionality of `values` if `axes` is omitted). |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to blur-core-v1
job = requests.post(f"{API}/engines/blur-core-v1/process", headers=H,
    json={
        "params": {
            "max_qubits": 20,
            "reach": 0,
            "strength": 0.5,
            "style": "x"
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — inline JSON
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
print(res["result"])
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/blur-core-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "max_qubits": 20,
    "reach": 0,
    "strength": 0.5,
    "style": "x"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Every value in the input is amplitude-encoded onto a Gray-coded qubit grid
(see `gray_encoding.py` for the encoding itself, which is intentionally kept
independent of this engine/Archaeo scaffolding so it can be lifted out into
its own library later), a single-qubit rotation is applied to each qubit,
and the grid is measured back out. Because adjacent grid points always
differ by exactly one bit in the encoding, the rotations scatter each
value's weight onto its neighbours — a blur, not noise.

##### How to use

Invoke the engine through the platform with a JSON params payload:

- `values` — required. An arbitrarily nested list of non-negative numbers.
  The nesting depth *is* the grid's dimensionality: a flat list is treated
  as 1-D, a list of lists as 2-D, a list of lists of lists as 3-D, and so
  on. The list must be rectangular (every sibling sub-list the same length).

Optionally, the params object may also include:

- `strength` — strength of the blur. Default `0.5`. Either a single number
  (applied to every targeted axis identically) or a list with one entry per
  targeted axis, letting different axes be blurred by different amounts
  (including `0`, i.e. left untouched).
- `style` — quantum gate(s) used to apply the blur. Default `"x"`.
- `reach` — how far from its original position a value can be affected by
  the blur. `0` is fully local (default); `1` is maximally non-local.
  Default `0.0`.
- `axes` — which axes of `values` to blur along. `null`/omitted (default)
  blurs every axis; e.g. for a 2-D grid, `[0]` blurs only "vertically"
  (along axis 0), leaving axis 1 untouched. Negative indices count from the
  end, as in numpy.
- `shots` — if given, the grid is recovered from a finite number of
  simulated projective measurements (introducing sampling noise), instead
  of the default exact (infinite-shot) probabilities.
- `max_qubits` — safety cap on the total number of qubits the input's shape
  is allowed to require. Default `20` (a 1024x1024 2-D grid costs 20).

##### Output

Returns a JSON list, nested to the same shape as the input `values`, with
each entry rescaled relative to the input's maximum (an exact round-trip
when `strength` is `0`).

#### Related engines

- [Coin Toss](/docs/engines/coin-toss-v1) — `coin-toss-v1`, JSON → JSON
- [Qpixl](/docs/engines/qpixl-v1) — `qpixl-v1`, JSON → JSON
- [Quantum Echo](/docs/engines/otoc-echo-v1) — `otoc-echo-v1`, JSON → JSON
- [Quantum Graph Engine](/docs/engines/graph-v1) — `graph-v1`, JSON → JSON


---

### Entanglement Shader — `entanglement-shader-v1`

POST https://api.mothquantum.com/api/v1/engines/entanglement-shader-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>entanglement-shader-v1</code></dd></div>

  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Aug 27, 2026</dd></div>
</dl>

Entanglement Shader

#### Request

`POST /api/v1/engines/entanglement-shader-v1/process` with a JSON body:

```json
{
  "params": {
    "absorption": 0.95,
    "incoming_rays": 8,
    "interaction": 1,
    "layers": 2,
    "reflectance": 0.2,
    "resolution": 60,
    "style": "peaked"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `absorption` | number | no | `0.95` | Fraction of the maximum absorption achievable at the given reflectance.  - `0` — no absorption. - `1` — maximum absorption and minimum transmission.  (min 0, max 1) |
| `incoming_rays` | integer | no | `8` | Number of light rays entering the stack simultaneously.  - Must be `>= layers` so that at least one ray is transmitted. - Maximum enforced by the 21-qubit budget at validation time.  (min 1) |
| `interaction` | number | no | `1` | Strength of the nonlinear quantum interaction terms.  - `0` — interaction disabled; only reflectance and absorption shape the output. - Positive vs. negative values of the same magnitude produce distinct colour patterns.  |
| `layers` | integer | no | `2` | Number of conducting sheets in the stack.  - Maximum enforced by the 21-qubit budget at validation time.  (min 1) |
| `reflectance` | number | no | `0.2` | Fraction of reflected power of a single ray and layer at normal incidence.  - `0` — perfect transmittance and no absorption. - `1` — perfect mirror, no transmission or absorption.  (min 0, max 1) |
| `resolution` | integer \| null | no | `60` | Density of the angle–phase lookup table baked into the shader.  - Higher values reduce banding on close-up or oblique surfaces.  |
| `style` | string | no | `"peaked"` | Selects which nonlinear interaction channels are active.  - `peaked` — reflection and transmission peak at the same angle for large number of layers. - `frustrated` — competing interaction channels produce a non-monotone colour pattern. - `3-body` — three-body interactions only; subtle, low-contrast effect. - `constrained` — higher ray counts suppress transmission, deepening shadows.  (one of `peaked`, `frustrated`, `3-body`, `constrained`) |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "entanglement-shader-v1-1b9d6bcd-result.bin",
      "content_type": "application/zip",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 18000 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `application/zip` | yes | ZIP archive containing all shader formats (OSL, Marmoset .frag, GLSL, HLSL, MaterialX) and the shared R/T lookup tables (EXR, HDR). |

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `max_qubits_exceeded` | Configuration requires more qubits than the maximum allowed. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to entanglement-shader-v1
job = requests.post(f"{API}/engines/entanglement-shader-v1/process", headers=H,
    json={
        "params": {
            "absorption": 0.95,
            "incoming_rays": 8,
            "interaction": 1,
            "layers": 2,
            "reflectance": 0.2,
            "resolution": 60,
            "style": "peaked"
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — output slots: result
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/entanglement-shader-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "absorption": 0.95,
    "incoming_rays": 8,
    "interaction": 1,
    "layers": 2,
    "reflectance": 0.2,
    "resolution": 60,
    "style": "peaked"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Generates an iridescent surface material driven by quantum entanglement.
Stacking ultra-thin conducting layers causes light to bounce and interfere,
producing angle-dependent colour shifts that no classical shader can replicate.

How to use
----------
Invoke this endpoint with a POST request.

The request body must be ``application/json``.

The body of the request must include:

- ``reflectance``
- ``absorption``
- ``layers``
- ``incoming_rays``

The body of the request may also include:

- ``resolution``
- ``interaction``
- ``style``

For more details about these parameters see the request schema below.

Output
------
Returns a ZIP archive containing all shader formats and shared textures:

- ``entanglement_texture.osl``  — Open Shading Language (Blender, Maya, Houdini, RenderMan).
- ``entanglement_texture.frag`` — Marmoset Toolbag 4 custom shader.
- ``entanglement_texture.glsl`` — Standalone GLSL fragment shader (OpenGL 3.3+).
- ``entanglement_texture.hlsl`` — HLSL pixel shader (Direct3D 11 / SM 5.0).
- ``entanglement_texture.mtlx`` — MaterialX material definition.
- ``R_lut.exr`` / ``R_lut.hdr`` — Float32 reflectance lookup table.
- ``T_lut.exr`` / ``T_lut.hdr`` — Float32 transmittance lookup table.

No quantum hardware is required at render time.

#### Related engines

- [Blur Jazz](/docs/engines/blur-midi-v1) — `blur-midi-v1`, Audio → Audio
- [QRC Train](/docs/engines/qrc-train-v2) — `qrc-train-v2`, JSON → JSON
- [Quantum Blur](/docs/engines/blur-v1) — `blur-v1`, Image → Image
- [Quantum Teleblur](/docs/engines/telablur-v1) — `telablur-v1`, Image → Image


---

### Tessa Image — `tessa-image-v1`

POST https://api.mothquantum.com/api/v1/engines/tessa-image-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>tessa-image-v1</code></dd></div>

  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 15, 2026</dd></div>
</dl>

Encode an image onto a quantum device using Tessa (the `iqpixl` library).

#### Request

`POST /api/v1/engines/tessa-image-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "distortion": 0,
    "fixed_palette": false,
    "gate_pauli": "XZ",
    "machine": "aer",
    "range_correction": false,
    "separate_rgb": true,
    "shots": 4096
  },
  "input_files": {
    "image": "9f8e7d6c-5b4a-4d21-8abc-def012345678"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `distortion` | number | no | `0` | Alpha for the exp(i*alpha/2*(P⊗Q)) gate applied between adjacent data qubits in transform_channels, where (P, Q) is `gate_pauli`. |
| `fixed_palette` | boolean | no | `false` | Import the image through a palette of its own colours (capped at 256) and run only the resulting per-pixel palette index through the device -- as exact, losslessly-quantized levels -- instead of decomposing it into the continuous colour-sphere coordinates. Good for flat-color/graphic-style images. |
| `gate_pauli` | string | no | `"XZ"` | Which two-qubit Pauli pair (P, Q) to use for the exp(i*distortion/2*(P⊗Q)) gate applied between adjacent data qubits in transform_channels, e.g. 'XY', 'ZZ'. (pattern `^[IXYZ]{2}$`) |
| `machine` | string | no | `"aer"` | Where to run the circuit. 'aer' is a noiseless local simulator. 'fake_&lt;chip>' options (e.g. 'fake_fez', 'fake_sherbrooke', 'fake_torino') are local simulators calibrated to a real current IBM chip's noise. 'ibm_&lt;chip>' options (e.g. 'ibm_fez', 'ibm_miami', 'ibm_marrakesh') submit to that real IBM Quantum hardware; 'least_busy' submits to whichever operational device currently has the shortest queue. (one of `aer`, `ibm_fez`, `ibm_miami`, `ibm_marrakesh`, `least_busy`, `fake_fez`, `fake_marrakesh`, `fake_torino`, `fake_brisbane`, `fake_kyiv`, `fake_sherbrooke`, `fake_kyoto`, `fake_osaka`, `fake_quebec`, `fake_cusco`, `fake_strasbourg`, `fake_brussels`) |
| `range_correction` | boolean | no | `false` | Stretch each decoded field back over its original dynamic range. Off by default -- the raw decoded values are used as-is, with no correction. |
| `separate_rgb` | boolean | no | `true` | Give each of the three colour coordinates its own circuit. Turn this off to put the two angles on one circuit instead: a qubit is cos(theta/2)\|0> + e^(i phi)\|1>, so the sphere's polar angle can ride in the rotation and hue in the phase of the same cell, turning three circuits into two at the cost of a second measurement setting and a noisier reconstruction. Ignored when fixed_palette is set. |
| `shots` | integer | no | `4096` | Number of measurement shots to sample, per processed field. |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `image` | `image/png`, `image/jpeg`, `image/webp`, `image/tiff`, `image/bmp` | yes | The image to encode. By default every pixel becomes a point on the colour sphere -- a radius and two angles, the same coordinates that describe a qubit's own state -- and each of those three goes through the quantum encode/measure/decode round trip, any that doesn't vary passed through unencoded, before the image is recomposed. With fixed_palette the image is instead quantized to a palette of its own colours (capped at 256) and only the per-pixel palette index makes the trip. The alpha channel, if any, passes through unchanged. |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "tessa-image-v1-1b9d6bcd-result.png",
      "content_type": "image/png",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 18000 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `image/png` | yes | The recomposed image after the quantum round trip. |

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_image` | The image file could not be decoded. |
| `distortion_without_hardware` | distortion is greater than 0 on a machine that reads out per-group (every machine except real IBM hardware) -- the cross-cell gate it adds is silently dropped there, so it would have no effect. |
| `too_many_values` | the image's pixel count exceeds the largest supported simulated lattice (64x64). |
| `insufficient_qubits` | the image still exceeds the selected machine's data-qubit capacity after being downsampled to fit it -- a degenerate-case fallback, not the normal outcome for an oversized image. |
| `unsupported_machine` | the requested machine name isn't recognized. |
| `ibm_connection_failed` | Could not authenticate/connect to IBM Quantum with the given token/instance. |
| `submission_failed` | The transpiled circuit was rejected or the sampling job failed to submit. |
| `encoding_failed` | The output image could not be encoded. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Upload the input as an asset (slot "image": image/png, image/jpeg, image/webp, image/tiff, image/bmp)
path = Path("input.png"); data = path.read_bytes()
asset = requests.post(f"{API}/assets", headers=H,
    json={"filename": path.name, "content_type": "image/png", "size_bytes": len(data)}).json()
requests.put(asset["upload"]["url"], data=data, headers=asset["upload"]["headers"]).raise_for_status()
requests.post(f"{API}/assets/{asset['asset_id']}/complete", headers=H).raise_for_status()
asset_id = asset["asset_id"]

# 2. Submit to tessa-image-v1
job = requests.post(f"{API}/engines/tessa-image-v1/process", headers=H,
    json={
        "params": {
            "distortion": 0,
            "fixed_palette": False,
            "gate_pauli": "XZ",
            "machine": "aer",
            "range_correction": False,
            "separate_rgb": True,
            "shots": 4096
        },
        "input_files": {
            "image": asset_id
        }
    }).json()

# 3. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 4. Fetch the result — output slots: result
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
# Upload first — see the Assets guide; put the returned asset_id in input_files.
curl -s -X POST https://api.mothquantum.com/api/v1/engines/tessa-image-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "distortion": 0,
    "fixed_palette": false,
    "gate_pauli": "XZ",
    "machine": "aer",
    "range_correction": false,
    "separate_rgb": true,
    "shots": 4096
  },
  "input_files": {
    "image": "$ASSET_ID"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

The pipeline is three steps, and `run` is those three calls:

    image  ->  circuits  ->  circuits  ->  image
            encode_    transform_   decode_
            channels    channels     channels

`encode_channels` splits the image into fields and writes each onto its own
circuit. `transform_channels` is the seam -- the image is on the circuits and
nothing has run yet, so gates appended there change the picture, computed on
the device rather than on the array. `decode_channels` measures what comes out
and turns it back into fields. Only the middle step is optional; it is the
identity today.

**The colour sphere.** Every pixel is a point on it
(`media_utils.image.rgb_to_sphere`): 50% grey at the centre, the white pole at
``theta = 0``, the black pole at ``theta = pi``, maximum brightness and
saturation around the equator, and hue as the azimuth ``phi``. A colour is
therefore ``(r, theta, phi)`` -- a radius and the two angles of a direction --
which is the same shape as a qubit's own state,
``cos(theta/2)|0> + e^\{i phi} sin(theta/2)|1>``. That is what makes gates in the
middle step mean something: a rotation on a cell is a rotation of a colour.
``theta`` is bent toward the equator on the way in and bent back on the way out
(`_EQUATOR_PULL`), which is exactly reversible and gives the saturated colours
more of the encoded range than the near-white and near-black caps.

**What lands on a channel** is chosen by two flags:

* `Params.separate_rgb` (default) puts ``r``, ``theta`` and ``phi`` on three
  circuits. Turn it off and ``theta``/``phi`` share one cell -- see
  `_encode_angle_pair`.
* `Params.fixed_palette` replaces the sphere entirely: the image is quantized
  to a palette of its own colours (capped at 256, see `_read_as_palette`) and
  only the per-pixel palette *index* -- one discrete
  channel -- makes the trip, encoded losslessly via iqpixl's codebook
  quantization. Good for flat-colour/graphic-style images where the
  discreteness itself should survive the round trip.

**How a channel is read back** is `decode`'s ``per_group`` flag:

* ``per_group=True`` -- one tiny (&lt;= 4-qubit) sub-circuit per data qubit. This
  is what makes noisy whole-chip *simulation* cheap (`machine="aer"` /
  `"fake_&lt;chip>"`): a 156-qubit noise model would be infeasible to simulate
  jointly, but each data qubit's own local sub-circuit is exactly its reduced
  state by the bipartite construction, independent of every other group. It
  also means a gate spanning two cells is dropped -- see `transform_channels`.
* ``per_group=False`` -- the whole circuit read out in one joint measurement.
  This is what you want on *real hardware* (`machine="ibm_fez"` / `"ibm_miami"`
  / `"least_busy"`): one job beats one job per data qubit.

`Params.sampler` is the `SamplerV2`-like primitive built automatically from
`Params.machine` -- see `topology.build_sampler`. `Params.shots` defaults to
4096 and must be positive -- there's no exact/noiseless mode for a sampled run.

Every field is encoded, including one that turns out to be constant (hue on a
grayscale image, all three on a flat-colour one). That costs a circuit it can't
learn anything from, but it costs nothing in accuracy: a constant field
normalises to a single angle, and on a noiseless machine the device reproduces
that angle deterministically. The one caveat is shot starvation -- the shots
are split across each cell's ``2**degree`` address configurations, and a
configuration that draws none at all has no counts to invert, so at very low
`Params.shots` a pixel here or there can still come back wrong.

#### Related engines

- [Quantum Blur](/docs/engines/blur-v1) — `blur-v1`, Image → Image
- [Quantum Teleblur](/docs/engines/telablur-v1) — `telablur-v1`, Image → Image
- [Deep Fryer](/docs/engines/deep-fryer-v1) — `deep-fryer-v1`, Image → Image
- [Blur Jazz](/docs/engines/blur-midi-v1) — `blur-midi-v1`, Audio → Audio


---

### Coin Toss — `coin-toss-v1`

POST https://api.mothquantum.com/api/v1/engines/coin-toss-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>coin-toss-v1</code></dd></div>
  <div><dt>Version</dt><dd>v1.0.15</dd></div>

  <div><dt>Publisher</dt><dd>Moth</dd></div>
  <div><dt>Usage</dt><dd>2 credits / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 10, 2026</dd></div>
</dl>

Flip a quantum coin a number of times and get back the heads and tails counts.

#### Request

`POST /api/v1/engines/coin-toss-v1/process` with a JSON body:

```json
{
  "params": {
    "mode": "emu",
    "shots": 10
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `backend_name` | string \| null | no | `null` | IBM Quantum backend to run on when mode is qpu, e.g. ibm_brisbane. Leave blank to let the platform choose the least busy one. |
| `mode` | string | no | `"emu"` | Where the circuit runs. emu uses the platform's simulator and returns in seconds; qpu submits to real IBM Quantum hardware and can queue for minutes. (one of `emu`, `qpu`) |
| `qpu_instance` | string \| null | no | `null` | IBM Quantum instance (hub/group/project) that pairs with qpu_token. Leave blank together with qpu_token to use Moth's account. |
| `qpu_token` | string \| null | no | `null` | Your own IBM Quantum API token for mode qpu. Recommended to leave blank: runs then use Moth's own IBM account through the platform backend. |
| `shots` | integer | no | `10` | Number of coin tosses to run. More shots bring the heads/tails split closer to 50/50. |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": null,
  "result": "<engine-specific JSON — fields below>"
}
```

Inline JSON in `result`:

- `output`: `"heads"` or `"tails"`, whichever had more counts.
- `heads`, `tails`: integer counts.
- `shots`: the number of measurements taken.

A run still going after 300 s is cancelled and the job ends `failed`.

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `coin_toss_failed` | The quantum circuit failed to execute. |
| `missing_credentials` | No IBM Quantum token available for a QPU run. |
| `unknown_backend` | The requested backend does not exist. |
| `circuit_too_large` | The circuit does not fit the selected backend. |
| `ibm_submission_failed` | mothbackend could not submit the circuit to IBM. |
| `ibm_collection_failed` | The QPU job did not complete successfully. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to coin-toss-v1
job = requests.post(f"{API}/engines/coin-toss-v1/process", headers=H,
    json={
        "params": {
            "mode": "emu",
            "shots": 10
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — inline JSON
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
print(res["result"])
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/coin-toss-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "mode": "emu",
    "shots": 10
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

A single qubit is put into equal superposition with a Hadamard gate and measured
`shots` times. Each measurement lands on heads or tails with 50/50 probability, so
the counts converge towards an even split as `shots` grows. Runs on an emulator
by default, or on an IBM Quantum device when `mode` is `qpu`.

##### How it works

1. Builds a one-qubit circuit: Hadamard gate, then measurement.
2. Runs it for `shots` measurements on the emulator, or submits it to the chosen
   IBM Quantum backend and waits for the device to finish.
3. Counts the outcomes and reports the majority as the result.

##### Output

Inline JSON in `result`:

- `output`: `"heads"` or `"tails"`, whichever had more counts.
- `heads`, `tails`: integer counts.
- `shots`: the number of measurements taken.

##### Limits

- `mode: "qpu"` needs an IBM Quantum token, either supplied per request or
  configured on the platform; device queue times can be minutes to hours.
- The circuit is one qubit; results are a probability sample, not a random-number
  service with guarantees.

##### Further reading

- [Hadamard gate](https://en.wikipedia.org/wiki/Quantum_logic_gate#Hadamard_gate):
  the single operation this engine uses.

#### Related engines

- [Qpixl](/docs/engines/qpixl-v1) — `qpixl-v1`, JSON → JSON
- [Quantum Blur Core](/docs/engines/blur-core-v1) — `blur-core-v1`, JSON → JSON
- [Quantum Echo](/docs/engines/otoc-echo-v1) — `otoc-echo-v1`, JSON → JSON
- [Quantum Graph Engine](/docs/engines/graph-v1) — `graph-v1`, JSON → JSON


---

### QRC Audio — `qrc-audio-v1`

POST https://api.mothquantum.com/api/v1/engines/qrc-audio-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>qrc-audio-v1</code></dd></div>

  <div><dt>Usage</dt><dd>5 credits / run</dd></div>
  <div><dt>Updated</dt><dd>Aug 25, 2026</dd></div>
</dl>

qrc-audio-v1 — sequence audio with a quantum reservoir.

#### Request

`POST /api/v1/engines/qrc-audio-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "chunk_seconds": 1,
    "crossfade": 0,
    "length": 10,
    "loop": true,
    "quality": "moderate",
    "variation": 1
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `chunk_seconds` | number | no | `1` | Length of each chunk in seconds when splitting the `audio` file. Ignored when `chunks` is given. |
| `crossfade` | integer | no | `0` | Milliseconds of crossfade between chunks (0 = hard cuts). (min 0, max 1000) |
| `length` | integer | no | `10` | How many chunks to string together in the output (max 500) |
| `loop` | boolean | no | `true` | Treat the audio as looping material — the end flows back into the start. Learning only. |
| `quality` | string | no | `"moderate"` | How hard to train when learning a fresh piece (no `model`): instant skips training for a quick untrained shuffle; fast is quick and rough; complete is slow and tight. (one of `instant`, `fast`, `moderate`, `complete`) |
| `seed` | integer \| null | no | `null` | Change for a different result, keep fixed to reproduce one. On a fresh piece it also fixes the learned reservoir; when reusing a `model` it just varies the take, so you can fan out independent takes by changing it. |
| `training_sequence` | array \| null | no | `null` | Advanced — chunk filenames in a specific order to learn. Omit to learn the chunks' natural order. Ignored when a `model` is given. |
| `variation` | number | no | `1` | How freely the result departs from the learned order: low = tight and repetitive, high = loose and surprising. |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `audio` | `audio/wav`, `audio/x-wav`, `audio/mpeg`, `audio/ogg`, `audio/flac` | no |  |
| `chunks` | `application/zip` | no |  |
| `model` | `application/json` | no |  |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "qrc-audio-v1-1b9d6bcd-result.wav",
      "content_type": "audio/wav",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    },
    {
      "slot": "state",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345671",
      "filename": "qrc-audio-v1-1b9d6bcd-state.json",
      "content_type": "application/json",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/state?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    },
    {
      "slot": "vocabulary",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345672",
      "filename": "qrc-audio-v1-1b9d6bcd-vocabulary.bin",
      "content_type": "application/zip",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/vocabulary?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    },
    {
      "slot": "model",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345673",
      "filename": "qrc-audio-v1-1b9d6bcd-model.json",
      "content_type": "application/json",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/model?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 3600 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `audio/wav` | yes | The generated remix WAV. |
| `state` | `application/json` | yes | Advanced reservoir state; reuse on a later call as job:&lt;id>/state. |
| `vocabulary` | `application/zip` | yes | Zip of chunk WAVs (filenames are tokens); reuse as job:&lt;id>/vocabulary. |
| `model` | `application/json` | no | Pristine trained model for fan-out; reuse as job:&lt;id>/model. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to qrc-audio-v1
job = requests.post(f"{API}/engines/qrc-audio-v1/process", headers=H,
    json={
        "params": {
            "chunk_seconds": 1,
            "crossfade": 0,
            "length": 10,
            "loop": True,
            "quality": "moderate",
            "variation": 1
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — output slots: result, state, vocabulary, model
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/qrc-audio-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "chunk_seconds": 1,
    "crossfade": 0,
    "length": 10,
    "loop": true,
    "quality": "moderate",
    "variation": 1
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

A self-contained hybrid engine: one call trains a reservoir over a vocabulary of audio *chunks*,
generates a new ordering of them, and concatenates the chosen chunks back into one WAV. Each chunk's
filename is a token — the reservoir work is delegated to `qrc_core` (train/generate/state); this
engine only owns the audio codec (split/merge) and the audio-friendly parameter surface.

The chunk vocabulary comes from EITHER:
  - `audio`  — a raw file the engine splits into fixed-length chunks (via media-utils), or
  - `chunks` — a pre-split zip of WAV chunks (filenames are the tokens).

`quality: "instant"` skips training entirely (a quick untrained shuffle); the other levels train.

Three seed paths, chosen by which inputs arrive (no mode flag):
  - no `model`, quality != instant -> TRAIN, then generate. Emits a pristine `files.model` (reusable
    for fan-out) plus the advanced `files.state`.
  - no `model`, quality == instant -> untrained shuffle, emits `files.state` only.
  - `model` given -> reuse it: a pristine model (`job:&lt;id>/model`) fans out an INDEPENDENT take (vary
    `seed`); an advanced state (`job:&lt;id>/state`) CONTINUES that trajectory.

`files.vocabulary` (the chunk zip) rides alongside — reference it as `job:&lt;id>/vocabulary` on later calls.

Reservoir tuning (qubits, shots, epochs, windowing) lives in reservoir_tuning.py — a self-contained
"don't touch" file. Everything here is audio: the chunk codec and the request/response flow.

#### Related engines

- [QRC Generate](/docs/engines/qrc-gen-v2) — `qrc-gen-v2`, File → JSON
- [QRC MIDI](/docs/engines/qrc-midi-v1) — `qrc-midi-v1`, Audio → Audio
- [Retrocausal Echo](/docs/engines/retrocausal-echo-v1) — `retrocausal-echo-v1`, Audio → Audio
- [QDrive](/docs/engines/qdrive-api-v1) — `qdrive-api-v1`, Text → Text


---

### Retrocausal Echo — `retrocausal-echo-v1`

POST https://api.mothquantum.com/api/v1/engines/retrocausal-echo-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>retrocausal-echo-v1</code></dd></div>
  <div><dt>Version</dt><dd>v0.1.2</dd></div>

  <div><dt>Usage</dt><dd>2 credits / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 15, 2026</dd></div>
</dl>

retrocausal-echo-v1 — Retrocausal Echo. A **media** engine.

#### Request

`POST /api/v1/engines/retrocausal-echo-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "allow_high_shots": false,
    "decay": 0.9,
    "depth": 8,
    "diffusion_ms": 0,
    "disorder": 0,
    "division": 0.25,
    "emit": "audio",
    "exact": true,
    "feedback": 0,
    "feedback_source": "kick",
    "fractional_gates": true,
    "grain_ms": 120,
    "include_tap_map": true,
    "ir_seconds": 3,
    "kick": "Z",
    "lattice": "chain",
    "machine": "aer",
    "master_ms": 640,
    "max_regen": 24,
    "min_level": 0.05,
    "mix": 0.6,
    "n_sites": 8,
    "negative_mode": "invert",
    "output_format": "pcm_16",
    "shots": 4096,
    "sr": 44100,
    "stereo_width": 1,
    "theta_x": 0.9424777960769379,
    "theta_z": 0,
    "theta_zz": 1.0995574287564276,
    "twirls": 1,
    "via": "direct"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `allow_high_shots` | boolean | no | `false` | Permit shots above 8192. |
| `bpm` | number \| null | no | `null` | Tempo. When set, one depth step = `division` of a bar instead of master_ms/depth. |
| `decay` | number | no | `0.9` | Extra level roll-off per depth step, on top of \|F\|. 1.0 = none. (max 1) |
| `depth` | integer | no | `8` | Echo depths t = 1..depth — the tap time slots. (min 1, max 32) |
| `diffusion_ms` | number | no | `0` | Square lattice only: y spreads taps by up to ±diffusion_ms/2 inside their depth slot. (min 0, max 500) |
| `disorder` | number | no | `0` | Additive per-gate angle jitter, std in radians. Localises the echo; the only lever that makes `seed` audible. (min 0, max 1) |
| `division` | number | no | `0.25` | Step as a fraction of a beat when bpm is set. 0.25 sixteenth · 0.5 eighth · 0.75 dotted eighth · 0.3333 eighth-triplet · 1.0 quarter. (max 4) |
| `emit` | string | no | `"audio"` | `audio` renders a WAV — your input processed, or the effect's own impulse response when no audio is supplied. `map` skips rendering entirely and returns only the time-mapped tap list, which is what a sequencer or a DAW plugin wants: same tap map, no audio work, no WAV to download. (one of `audio`, `map`) |
| `exact` | boolean | no | `true` | aer only: exact expectation values instead of sampling. |
| `feedback` | number | no | `0` | Regeneration loop gain. The bus of selected taps is normalised first, so this is the fraction of signal that comes back round — always convergent, and 0.6 sounds like 0.6 on a rack unit rather than diverging. (min 0) |
| `feedback_source` | string | no | `"kick"` | Which taps regenerate. `kick`: only the kick site's column (the classic single regeneration tap). `all`: every tap. (one of `kick`, `all`) |
| `fractional_gates` | boolean | no | `true` | Use native rzz/rx where available. |
| `grain_ms` | number | no | `120` | Grain length for `reverse` mode. Short → stuttered; long → whole phrases backwards. (max 2000) |
| `height` | integer \| null | no | `null` | Square lattice height. Required for `square`. |
| `include_tap_map` | boolean | no | `true` | Also emit the rendered tap map inline in the result (it is always written to taps.json). |
| `ir_seconds` | number | no | `3` | With no `audio` input, render the effect's own stereo impulse response for this long. (max 30) |
| `kick` | string | no | `"Z"` | Perturbation Pauli applied to the kick site between U and U†. (one of `Z`, `Y`, `X`) |
| `kick_site` | integer \| null | no | `null` | Regeneration source: the site that receives the impulse. Default: centre. |
| `lattice` | string | no | `"chain"` | Delay-line topology. `chain`: site → pan. `square` (Nighthawk-native): x → pan, y → diffusion. (one of `chain`, `square`) |
| `machine` | string | no | `"aer"` | Backend for the measurement: 'aer' (local, noiseless) or an IBM backend name such as 'ibm_phoenix'. |
| `master_ms` | number | no | `640` | Length of the master delay line in ms. One depth step = master_ms / depth. Ignored when bpm is set. (max 8000) |
| `max_regen` | integer | no | `24` | Cap on regeneration iterations. (min 1, max 64) |
| `min_level` | number | no | `0.05` | \|F\| threshold below which a tap is dropped. (min 0, max 1) |
| `mix` | number | no | `0.6` | Dry/wet. 0 = dry, 1 = wet only. (min 0, max 1) |
| `n_sites` | integer | no | `8` | Chain length in qubits (= pan positions). Ignored for `square`. (min 2, max 156) |
| `negative_mode` | string | no | `"invert"` | What a negative F does. `invert`: flip polarity (phase-cancelling echo). `reverse`: play that tap's grains backwards. `phase`: rotate by arg(F) via a Hilbert transform — the only mode that uses F_im, so pair it with theta_z > 0. (one of `invert`, `reverse`, `phase`) |
| `output_format` | string | no | `"pcm_16"` | WAV sample format. (one of `pcm_16`, `pcm_32`, `float_32`) |
| `qpu_instance` | string \| null | no | `null` | IBM Quantum instance CRN. As with the token: required for `via: direct`, optional BYOK for `via: mothbackend`. (format password) |
| `qpu_token` | string \| null | no | `null` | IBM Quantum API token when machine is an IBM backend; falls back to QISKIT_IBM_TOKEN. (format password) |
| `ref_floor` | number \| null | no | `null` | \|c_ref\| below which a tap is dropped as unnormalisable. Default: 4/sqrt(shots), ~0 for exact simulation. Raise it to prune taps the noise floor cannot support. |
| `seed` | integer \| null | no | `null` | RNG seed for the disorder realisation. Only audible when disorder > 0. Drawn as a 31-bit integer and returned in provenance if omitted. Capped at 2**53-1: above that, moth-api (Go) and any browser client re-spell the integer as a float64 and it stops matching the seed you sent. |
| `shots` | integer | no | `4096` | Shots per circuit. Ignored when machine='aer' and exact=true. Above 8192 requires allow_high_shots. (min 1) |
| `sr` | integer | no | `44100` | Sample rate. Ignored when an `audio` file is supplied — that file's own rate is used. (min 8000, max 192000) |
| `stereo_width` | number | no | `1` | Scales the site → pan spread. 0 = mono. (min 0, max 1) |
| `tail_ms` | number \| null | no | `null` | Silence appended to the input so the last tap and its regenerations fit. Default: computed from the tap map. |
| `theta_x` | number | no | `0.9424777960769379` | Transverse kick per layer (RX, rad) — the 'how quantum' dial. Low → loud regular taps; high → inverted, attenuated, erased. (min 0, max 3.141592653589793) |
| `theta_z` | number | no | `0` | Phase layer (RZ, rad). 0 → real, two-signed taps. >0 → complex F, which `negative_mode: phase` renders as rotation. (min 0, max 3.141592653589793) |
| `theta_zz` | number | no | `1.0995574287564276` | Coupling per layer (RZZ, rad). Non-monotonic: ≈0.25π is the sparse setting. π is a Clifford (no scrambling). θ and π−θ coincide only when theta_x = 0, not at the default drive, so the upper half of the range is its own territory. The sign is invisible unless theta_z > 0. (max 3.141592653589793) |
| `twirls` | integer | no | `1` | ZZ-commutant Pauli twirls per circuit, averaged. Only useful on hardware: it randomises off-axis coherent error in the couplings. Multiplies the circuit count, so it multiplies QPU time. (min 1, max 32) |
| `via` | string | no | `"direct"` | How to reach the machine. `direct`: this engine drives qiskit-ibm-runtime itself (analytic emulation, native fractional gates, one batched QPU session). `mothbackend`: route through Moth's execution service, which holds the credentials — sampled only, so no analytic mode, no fractional gates, and one submission per circuit. (one of `direct`, `mothbackend`) |
| `width` | integer \| null | no | `null` | Square lattice width. Required for `square`. |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `audio` | `audio/wav`, `audio/x-wav`, `audio/wave`, `audio/mpeg`, `audio/ogg`, `audio/flac` | no | Mono or stereo audio to process — WAV, MP3, OGG or FLAC. Stereo is summed to mono first, since the taps place their own stereo image. The file's own sample rate wins over the `sr` param. |
| `ir` | `application/json` | no | A previously measured impulse response — an otoc-echo `trajectory` envelope. Supply it to re-render without paying for the measurement again, and every echo param is ignored. Pass the asset id of a previous retrocausal-echo job's own `ir` output (output assets carry `slot` and `job_id`, so they chain straight into `input_files`), or upload the JSON yourself. `job:&lt;id>/ir` is the documented alias for the same thing but may not resolve — prefer the asset id. |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "retrocausal-echo-v1-1b9d6bcd-result.wav",
      "content_type": "audio/wav",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    },
    {
      "slot": "ir",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345671",
      "filename": "retrocausal-echo-v1-1b9d6bcd-ir.json",
      "content_type": "application/json",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/ir?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    },
    {
      "slot": "taps",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345672",
      "filename": "retrocausal-echo-v1-1b9d6bcd-taps.json",
      "content_type": "application/json",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/taps?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 7200 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `audio/wav`, `application/json` | yes | The primary output. With `emit: audio` (the default) this is the rendered stereo WAV. With `emit: map` no audio is rendered at all and this is the tap map as JSON — the same envelope the `taps` slot carries — so a sequencer or plugin can place the events itself without downloading audio. |
| `ir` | `application/json` | yes | The impulse response actually used, as an otoc-echo `trajectory` envelope. Its output asset chains straight into another job's `input_files.ir` — one measurement, many mixes. |
| `taps` | `application/json` | yes | The full `media` result envelope: provenance, the audio's shape, the echo summary, the spec, and the rendered tap map (time_ms, level, pan, F, polarity per tap). This is where a caller reads the numbers; a DAW or plugin can load it directly. |

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_params` | params fail Params' own field validation (type/range) or a cross-field check (square lattice without width/height, kick_site outside the line, shots over the cap without allow_high_shots). |
| `invalid_ir` | the `ir` input is not UTF-8 JSON, or not an otoc-echo `trajectory` envelope. A bare envelope, a handler return wrapped in `output`, and a whole job result wrapped in `result` are all accepted. |
| `invalid_audio` | the `audio` input could not be decoded as a PCM or float WAV, is over the size cap, or decoded to zero samples. |
| `audio_too_long` | the input, or the input plus its computed tail, exceeds the render length cap. Set tail_ms explicitly or send a shorter file. |
| `no_taps` | no tap survived min_level — the echo was fully erased at this theta_x, or min_level is too high. The echo summary is in the message. |
| `too_many_taps` | the tap map is larger than the render cap. Raise min_level or lower depth. |
| `too_many_qubits` | the delay line needs more qubits than the machine allows — 24 for aer, the device's own width for an IBM backend. Supplying a measured `ir` sidesteps this entirely. |
| `invalid_machine` | machine is neither 'aer' nor an IBM backend name the runtime knows. |
| `backend_unavailable` | the requested execution route could not be reached — for `via: direct`, qiskit-ibm-runtime is missing or no credentials were supplied (qpu_token param / QISKIT_IBM_TOKEN); for `via: mothbackend`, the mothbackend package is absent or the service returned a transport error. Retryable. |
| `execution_failed` | the estimator returned an error while running the echo circuits. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to retrocausal-echo-v1
job = requests.post(f"{API}/engines/retrocausal-echo-v1/process", headers=H,
    json={
        "params": {
            "allow_high_shots": False,
            "decay": 0.9,
            "depth": 8,
            "diffusion_ms": 0,
            "disorder": 0,
            "division": 0.25,
            "emit": "audio",
            "exact": True,
            "feedback": 0,
            "feedback_source": "kick",
            "fractional_gates": True,
            "grain_ms": 120,
            "include_tap_map": True,
            "ir_seconds": 3,
            "kick": "Z",
            "lattice": "chain",
            "machine": "aer",
            "master_ms": 640,
            "max_regen": 24,
            "min_level": 0.05,
            "mix": 0.6,
            "n_sites": 8,
            "negative_mode": "invert",
            "output_format": "pcm_16",
            "shots": 4096,
            "sr": 44100,
            "stereo_width": 1,
            "theta_x": 0.9424777960769379,
            "theta_z": 0,
            "theta_zz": 1.0995574287564276,
            "twirls": 1,
            "via": "direct"
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — output slots: result, ir, taps
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/retrocausal-echo-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "allow_high_shots": false,
    "decay": 0.9,
    "depth": 8,
    "diffusion_ms": 0,
    "disorder": 0,
    "division": 0.25,
    "emit": "audio",
    "exact": true,
    "feedback": 0,
    "feedback_source": "kick",
    "fractional_gates": true,
    "grain_ms": 120,
    "include_tap_map": true,
    "ir_seconds": 3,
    "kick": "Z",
    "lattice": "chain",
    "machine": "aer",
    "master_ms": 640,
    "max_regen": 24,
    "min_level": 0.05,
    "mix": 0.6,
    "n_sites": 8,
    "negative_mode": "invert",
    "output_format": "pcm_16",
    "shots": 4096,
    "sr": 44100,
    "stereo_width": 1,
    "theta_x": 0.9424777960769379,
    "theta_z": 0,
    "theta_zz": 1.0995574287564276,
    "twirls": 1,
    "via": "direct"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

The other half of the split. `otoc-echo-v1` is the *core* engine: it measures a
quantum impulse response and returns it as a typed `trajectory`. This engine is a
*media* engine: it turns an impulse response into audio. Both depend on the same
`quantum-echo` library, so the measurement exists in exactly one place.

    core   : params -> EchoSpec -> measure_ir -> EchoIR.to_trajectory()
    media  : (EchoIR from a library call | a prior job's ir.json) -> MultiTapDelay -> WAV

Two ways in, one renderer:

  * no `ir` file  -> this engine calls `quantum_echo.measure_ir` in-process. One
    job, one price, audio out. The QPU work is identical to the core engine's.
  * an `ir` file  -> `EchoIR.from_trajectory`. Re-render a measured response with
    different audio, tempo, polarity behaviour or feedback without paying for the
    measurement again. The slot is `by_reference: true`, so it takes either an
    upload or `job:&lt;id>/ir` off a previous retrocausal-echo job.

Nothing here builds a circuit and nothing in `render.py` knows what a qubit is.

#### Related engines

- [QRC Audio](/docs/engines/qrc-audio-v1) — `qrc-audio-v1`, Audio → Audio
- [QRC Generate](/docs/engines/qrc-gen-v2) — `qrc-gen-v2`, File → JSON
- [QRC MIDI](/docs/engines/qrc-midi-v1) — `qrc-midi-v1`, Audio → Audio
- [QDrive](/docs/engines/qdrive-api-v1) — `qdrive-api-v1`, Text → Text


---

### Quantum Echo — `otoc-echo-v1`

POST https://api.mothquantum.com/api/v1/engines/otoc-echo-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>otoc-echo-v1</code></dd></div>
  <div><dt>Version</dt><dd>v0.1.2</dd></div>

  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 15, 2026</dd></div>
</dl>

otoc-echo-v1 — Quantum Echo. A **core** engine.

#### Request

`POST /api/v1/engines/otoc-echo-v1/process` with a JSON body:

```json
{
  "params": {
    "allow_high_shots": false,
    "depth": 8,
    "disorder": 0,
    "exact": true,
    "fractional_gates": true,
    "include_taps": true,
    "include_z": false,
    "kick": "Z",
    "lattice": "chain",
    "machine": "aer",
    "min_tap_level": 0.02,
    "n_sites": 8,
    "shots": 4096,
    "theta_x": 0.9424777960769379,
    "theta_z": 0,
    "theta_zz": 1.0995574287564276,
    "twirls": 1,
    "via": "direct"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `allow_high_shots` | boolean | no | `false` | Permit shots above 8192 (QPU time scales linearly). |
| `depth` | integer | no | `8` | Echo depths t = 1..depth — the tap time slots. Each circuit has 2·depth layers. (min 1, max 32) |
| `disorder` | number | no | `0` | Additive per-gate angle jitter, std in radians. 0 = clean Floquet. Localises the echo; the only lever that makes `seed` matter. (min 0, max 1) |
| `exact` | boolean | no | `true` | aer only: exact (infinite-shot) expectation values instead of sampling. |
| `fractional_gates` | boolean | no | `true` | Use native rzz/rx on hardware where available. Halves the forward half's two-qubit count; disables gate twirling. |
| `height` | integer \| null | no | `null` | Square lattice height. Required for `square`. |
| `include_taps` | boolean | no | `true` | Also emit a flattened tap list (site, depth, F_re, F_im, level, polarity) in extras. |
| `include_z` | boolean | no | `false` | Also measure &lt;Z_i>, completing each site's Bloch vector. Free on aer; a third measurement basis (1.5x shots) on hardware. |
| `kick` | string | no | `"Z"` | Perturbation Pauli applied to the kick site between U and U†. (one of `Z`, `Y`, `X`) |
| `kick_site` | integer \| null | no | `null` | Regeneration source: the site that receives the impulse. Default: centre. |
| `lattice` | string | no | `"chain"` | Topology of the delay line. `chain`: site → pan. `square` (Nighthawk-native): x → pan, y → diffusion. (one of `chain`, `square`) |
| `machine` | string | no | `"aer"` | Backend: 'aer' (local, noiseless) or an IBM backend name such as 'ibm_phoenix'. |
| `min_tap_level` | number | no | `0.02` | \|F\| threshold for the emitted tap list. (min 0, max 1) |
| `n_sites` | integer | no | `8` | Chain length in qubits (= pan positions). Ignored for `square`. (min 2, max 156) |
| `qpu_instance` | string \| null | no | `null` | IBM Quantum instance CRN. As with the token: required for `via: direct`, optional BYOK for `via: mothbackend`. (format password) |
| `qpu_token` | string \| null | no | `null` | IBM Quantum API token. Required for `via: direct` on an IBM machine (or the QISKIT_IBM_TOKEN env var); optional BYOK for `via: mothbackend`, which otherwise uses Moth's own credentials. (format password) |
| `ref_floor` | number \| null | no | `null` | \|c_ref\| below which F is null. Default: 4/sqrt(shots), ~0 for exact simulation. |
| `seed` | integer \| null | no | `null` | RNG seed for the disorder realisation. Only audible when disorder > 0. Drawn as a 31-bit integer and returned in provenance if omitted. Capped at 2**53-1: above that, moth-api (Go) and any browser client re-spell the integer as a float64 and it stops matching the seed you sent. |
| `shots` | integer | no | `4096` | Shots per circuit. Ignored when machine='aer' and exact=true. Above 8192 requires allow_high_shots. (min 1) |
| `theta_x` | number | no | `0.9424777960769379` | Transverse kick per layer (RX angle, rad). The 'how quantum' dial: low → loud regular taps; high → inverted, attenuated, erased. (min 0, max 3.141592653589793) |
| `theta_z` | number | no | `0` | Phase layer (RZ angle, rad). 0 → real, two-signed F. >0 → complex F: taps acquire a phase. (min 0, max 3.141592653589793) |
| `theta_zz` | number | no | `1.0995574287564276` | Coupling per layer (RZZ, rad). Non-monotonic: ≈0.25π is the sparse setting. π is a Clifford (no scrambling). θ and π−θ coincide only when theta_x = 0, not at the default drive, so the upper half of the range is its own territory. The sign is invisible unless theta_z > 0. (max 3.141592653589793) |
| `twirls` | integer | no | `1` | ZZ-commutant Pauli twirls per circuit, averaged. Randomises off-axis coherent rzz error (not angle miscalibration, which the reference run absorbs). Multiplies circuit count. (min 1, max 32) |
| `via` | string | no | `"direct"` | How to reach the machine. `direct`: this engine drives qiskit-ibm-runtime itself (analytic emulation, native fractional gates, one batched QPU session). `mothbackend`: route through Moth's execution service, which holds the credentials — sampled only, so no analytic mode, no fractional gates, and one submission per circuit. (one of `direct`, `mothbackend`) |
| `width` | integer \| null | no | `null` | Square lattice width. Required for `square`. |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": null,
  "result": "<engine-specific JSON — fields below>"
}
```

`result` holds this engine's JSON inline. _The engine author has not documented its fields yet._

A run still going after 7200 s is cancelled and the job ends `failed`.

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_params` | params fail Params' own field validation (type/range) or a cross-field check (square lattice without width/height, kick_site outside the line, shots over the cap without allow_high_shots). |
| `too_many_qubits` | the delay line needs more qubits than the machine allows — 24 for aer, the device's own width for an IBM backend. |
| `invalid_machine` | machine is neither 'aer' nor an IBM backend name the runtime knows. |
| `backend_unavailable` | the requested execution route could not be reached — for `via: direct`, qiskit-ibm-runtime is missing or no credentials were supplied (qpu_token param / QISKIT_IBM_TOKEN); for `via: mothbackend`, the mothbackend package is absent or the service returned a transport error. Retryable. |
| `execution_failed` | the estimator returned an error while running the echo circuits. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to otoc-echo-v1
job = requests.post(f"{API}/engines/otoc-echo-v1/process", headers=H,
    json={
        "params": {
            "allow_high_shots": False,
            "depth": 8,
            "disorder": 0,
            "exact": True,
            "fractional_gates": True,
            "include_taps": True,
            "include_z": False,
            "kick": "Z",
            "lattice": "chain",
            "machine": "aer",
            "min_tap_level": 0.02,
            "n_sites": 8,
            "shots": 4096,
            "theta_x": 0.9424777960769379,
            "theta_z": 0,
            "theta_zz": 1.0995574287564276,
            "twirls": 1,
            "via": "direct"
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — inline JSON
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
print(res["result"])
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/otoc-echo-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "allow_high_shots": false,
    "depth": 8,
    "disorder": 0,
    "exact": true,
    "fractional_gates": true,
    "include_taps": true,
    "include_z": false,
    "kick": "Z",
    "lattice": "chain",
    "machine": "aer",
    "min_tap_level": 0.02,
    "n_sites": 8,
    "shots": 4096,
    "theta_x": 0.9424777960769379,
    "theta_z": 0,
    "theta_zz": 1.0995574287564276,
    "twirls": 1,
    "via": "direct"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Thin wrapper over the `quantum-echo` library: this file owns the platform contract
(params schema, validation, credits, estimate, the typed result envelope) and the
library owns the physics. Same relationship qdrive-api has with QDrive.

    params -> EchoSpec -> quantum_echo.measure_ir -> EchoIR.to_trajectory()

Media engines (retrocausal-echo-v1 and friends) depend on the same library and either
call `measure_ir` in-process or rebuild an IR from this engine's result with
`EchoIR.from_trajectory`. Neither path reimplements the measurement.

#### Related engines

- [Coin Toss](/docs/engines/coin-toss-v1) — `coin-toss-v1`, JSON → JSON
- [Qpixl](/docs/engines/qpixl-v1) — `qpixl-v1`, JSON → JSON
- [Quantum Blur Core](/docs/engines/blur-core-v1) — `blur-core-v1`, JSON → JSON
- [Quantum Graph Engine](/docs/engines/graph-v1) — `graph-v1`, JSON → JSON


---

### Qpixl — `qpixl-v1`

POST https://api.mothquantum.com/api/v1/engines/qpixl-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>qpixl-v1</code></dd></div>

  <div><dt>Publisher</dt><dd>Moth</dd></div>
  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 9, 2026</dd></div>
</dl>

Encode an array of floats onto a quantum device using Interwoven QPIXL.

#### Request

`POST /api/v1/engines/qpixl-v1/process` with a JSON body:

```json
{
  "params": {
    "allow_high_shots": false,
    "discretize": 0,
    "dynamic_range": "none",
    "machine": "aer",
    "mode": "emu",
    "shots": 4096,
    "values": [
      0.05,
      0.2,
      0.4,
      0.6,
      0.8,
      0.95
    ]
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `allow_high_shots` | boolean | no | `false` | Permit `shots` above 8192. Real hardware time scales linearly with shots, and emulated runs multiply shots by the number of data-qubit groups, so raising this can be expensive. Off by default. |
| `backend_name` | string \| null | no | `null` | IBM device to target when mode='qpu', e.g. 'ibm_fez'. Required in that mode -- there is no least-busy auto-select. Ignored when mode='emu'. |
| `discretize` | integer | no | `0` | Number of discrete levels to quantize `values` to. 0 encodes them continuously. (min 0) |
| `dynamic_range` | string | no | `"none"` | Rescale the reconstruction to match a summary statistic of the original `values`, to counteract shot noise/decoherence shrinking its spread toward the middle of the range. 'none' leaves the reconstruction unchanged. 'min_max' rescales so its min and max match the input's. 'percentile' does the same using the 2nd/98th percentiles instead, less sensitive to outliers. 'mean_std' matches mean and standard deviation. 'abs_max' rescales by the single largest absolute value. 'min_avg_max' matches min, mean, and max all three at once. (one of `none`, `min_max`, `percentile`, `mean_std`, `abs_max`, `min_avg_max`) |
| `machine` | string | no | `"aer"` | Which emulator to use when mode='emu' (ignored when mode='qpu'). 'aer' is noiseless. 'fake_&lt;chip>' options (e.g. 'fake_fez', 'fake_sherbrooke', 'fake_torino') are each calibrated to a real current IBM chip's noise. (one of `aer`, `fake_fez`, `fake_marrakesh`, `fake_torino`, `fake_brisbane`, `fake_kyiv`, `fake_sherbrooke`, `fake_kyoto`, `fake_osaka`, `fake_quebec`, `fake_cusco`, `fake_strasbourg`, `fake_brussels`) |
| `mode` | string | no | `"emu"` | 'emu' simulates the circuit (see `machine` for noiseless vs. noisy); 'qpu' submits to real IBM hardware (see `backend_name`). Both run server-side on mothbackend. (one of `emu`, `qpu`) |
| `shots` | integer | no | `4096` | Number of measurement shots to sample. Capped at 8192 unless `allow_high_shots` is set; the hard ceiling is 32768. Note this is shots PER data-qubit group when mode='emu', not per run. (max 32768) |
| `values` | string \| array \| array | no | `[0.05,0.2,0.4,0.6,0.8,0.95]` | Array of floating-point values to encode. Either a flat list, a nested list of groups (one sublist per data-qubit group, in the exact order `list_groups(values, machine)` returns them), or that same shape written as a single string wrapped in [..] or (..), e.g. "[0.1,0.2,0.3]" for a flat list or "[[0.1,0.2],[0.3,0.4]]" / "([0.1,0.2],[0.3,0.4])" for groups. A group with more values than its capacity is rejected; a group with fewer is padded with zeros. (min length 1) |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": null,
  "result": "<engine-specific JSON — fields below>"
}
```

`result` holds this engine's JSON inline. _The engine author has not documented its fields yet._

A run still going after 18000 s is cancelled and the job ends `failed`.

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `unparseable_values` | a string values input isn't a valid comma-separated (optionally [..]/(..) grouped) number list. |
| `too_few_values` | values must contain at least 2 numbers. |
| `non_finite_values` | values must contain only finite numbers (no NaN/Infinity). |
| `too_many_values` | values exceeds the largest supported simulated lattice (64x64). |
| `insufficient_qubits` | values exceeds the selected machine's data-qubit capacity. |
| `group_count_mismatch` | a nested (grouped) values input has a different number of groups than the machine's lattice. |
| `group_overflow` | one group in a nested (grouped) values input has more values than that group's data qubit can hold. |
| `unsupported_machine` | the requested machine name isn't recognized. |
| `ibm_connection_failed` | Could not authenticate/connect to IBM Quantum with the given token/instance. |
| `submission_failed` | The transpiled circuit was rejected or the sampling job failed to submit. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to qpixl-v1
job = requests.post(f"{API}/engines/qpixl-v1/process", headers=H,
    json={
        "params": {
            "allow_high_shots": False,
            "discretize": 0,
            "dynamic_range": "none",
            "machine": "aer",
            "mode": "emu",
            "shots": 4096,
            "values": [
                0.05,
                0.2,
                0.4,
                0.6,
                0.8,
                0.95
            ]
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — inline JSON
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
print(res["result"])
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/qpixl-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "allow_high_shots": false,
    "discretize": 0,
    "dynamic_range": "none",
    "machine": "aer",
    "mode": "emu",
    "shots": 4096,
    "values": [
      0.05,
      0.2,
      0.4,
      0.6,
      0.8,
      0.95
    ]
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Execution is delegated to mothbackend (`mothbackend.client`): the engine builds
circuits locally, decomposes them to a QASM2-safe basis, and submits QASM.
mothbackend takes a single backend name and derives its own mode from it
("aer" -> sim, "fake_&lt;chip>" -> emu, anything else -> qpu), so the public
`mode`/`machine`/`backend_name` triple is collapsed into that one name by
`topology.resolve_backend()` before anything is submitted.

* ``mode="emu"``, ``machine="aer"`` -- mothbackend's noiseless simulator. The
  encoding graph is still an auto-sized checkerboard lattice built engine-side
  (`topology.py`) -- a bare simulator imposes no topology of its own.
  Reconstructed one data-qubit group at a time via `_run_by_groups`, same as
  the ``fake_*`` machines below -- there's no joint statevector limit to worry
  about since each group runs as its own tiny circuit.
* ``mode="qpu"``, ``backend_name="ibm_fez"`` -- real IBM hardware via
  mothbackend's qpu mode. Runs the whole circuit as one joint measurement via
  `_run_joint` -- submitting one job per data-qubit group to real hardware
  would be far slower and more expensive than a single combined job. `machine`
  is ignored in this mode. `backend_name` is required here: mothbackend
  exposes no `least_busy` selector, so there's no auto-select to fall back on.

Credentials are never handled engine-side. mothbackend resolves IBM
credentials itself from its own secret store; the engine holds no token, is
passed none, and returns none. There is deliberately no BYOK parameter on
`Params` -- adding one would put a user-supplied secret in the job payload,
the job record, and any error text quoting it.
* ``mode="emu"``, ``machine="fake_&lt;chip>"`` (e.g. ``"fake_fez"``,
  ``"fake_sherbrooke"``, ``"fake_torino"`` -- see `topology.FAKE_MACHINES` for
  the full list) -- that real IBM chip's noisy stand-in, simulated server-side
  by mothbackend's emu mode. A full chip-scale statevector can't be simulated
  jointly, so
  `_run_by_groups` reconstructs one data-qubit group at a time: each group's
  tiny sub-circuit is submitted with `initial_layout` pinning it onto its own
  real physical qubits -- cheap regardless of how many qubits the chip actually
  has, because different data-qubit groups' encoding gates commute (address
  qubits are only ever controls, never targets), so each group's own marginal
  statistics don't depend on any other group.

Bitstring convention: mothbackend reports counts qubit-0-LEFTMOST
(`bit_order: "qubit0_left"`), while `iqpixl.decode_counts` consumes Qiskit's
native qubit-0-rightmost bitstrings -- `_run_counts` reverses each key exactly
once at the boundary. Nothing else in the pipeline reverses anything.

`Params.shots` defaults to 4096 and must be positive -- there's no exact/
noiseless mode for a sampled run.

#### Related engines

- [Coin Toss](/docs/engines/coin-toss-v1) — `coin-toss-v1`, JSON → JSON
- [Quantum Blur Core](/docs/engines/blur-core-v1) — `blur-core-v1`, JSON → JSON
- [Quantum Echo](/docs/engines/otoc-echo-v1) — `otoc-echo-v1`, JSON → JSON
- [Quantum Graph Engine](/docs/engines/graph-v1) — `graph-v1`, JSON → JSON


---

### Deep Fryer — `deep-fryer-v1`

POST https://api.mothquantum.com/api/v1/engines/deep-fryer-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>deep-fryer-v1</code></dd></div>

  <div><dt>Publisher</dt><dd>Moth</dd></div>
  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 9, 2026</dd></div>
</dl>

Deep Fryer: a quantum kernel that gives images that blown-out, deep-fried meme look.

#### Request

`POST /api/v1/engines/deep-fryer-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "gates": [
      [
        "rx",
        0.5
      ]
    ],
    "mask_bin_size": 4,
    "mask_min_region": 16,
    "tile_size": 4
  },
  "input_files": {
    "image": "9f8e7d6c-5b4a-4d21-8abc-def012345678"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `gates` | array | no | `[["rx",0.5]]` | Sequence of (gate_name, intensity) pairs applied to each tile's qubit lattice, in order. |
| `mask_bin_size` | number | no | `4` | Mask quantisation step as a percentage of 255 (0-100). Pixel values below this threshold are treated as background, preventing near-zero JPEG/WebP compression artifacts from being detected as separate mask regions. Default 4 (~10/255). (min 0, max 100) |
| `mask_min_region` | integer | no | `16` | Minimum mask region size in pixels. Connected components smaller than this are discarded after quantisation, removing residual compression artifacts that survive the binning step. Default 16. (min 1) |
| `tile_size` | integer | no | `4` | Side length of the square qubit lattice used as the per-tile processing kernel. (min 2, max 4) |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `image` | `image/png`, `image/jpeg`, `image/webp`, `image/bmp`, `image/tiff` | yes |  |
| `mask` | `image/png`, `image/jpeg`, `image/webp`, `image/bmp`, `image/tiff` | no | Optional mask controlling where the effect is applied, on a per-pixel basis. Resized (Lanczos) to match `image` if it isn't already the same size. Brighter mask pixels take more of the quantum-processed color, darker pixels keep more of the original. The mask is split into disjoint connected regions and each is processed independently, scoped to its own bounding box. If omitted, the alpha channel of `image` is used instead (transparent pixels stay original, opaque pixels are processed); for RGB input with no alpha channel, the whole image is processed. |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "deep-fryer-v1-1b9d6bcd-result.png",
      "content_type": "image/png",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 30000 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `image/png`, `image/jpeg`, `image/webp`, `image/bmp`, `image/tiff` | yes | The processed image. |

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_image` | The image or mask file could not be decoded. |
| `no_mask_region` | The provided mask has no non-zero regions after quantisation — nothing to process. |
| `invalid_params` | One or more params fields failed Pydantic validation. |
| `tile_too_large` | tile_size ** 2 exceeds the MAX_QUBITS simulation budget. |
| `unsupported_gate` | A gate name in `gates` is not in the supported gate registry. |
| `kernel_failed` | The quantum color kernel failed on a tile. |
| `encoding_failed` | The output image could not be encoded in the input's format. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Upload the input as an asset (slot "image": image/png, image/jpeg, image/webp, image/bmp, image/tiff)
#    Optional slots not shown: mask
path = Path("input.png"); data = path.read_bytes()
asset = requests.post(f"{API}/assets", headers=H,
    json={"filename": path.name, "content_type": "image/png", "size_bytes": len(data)}).json()
requests.put(asset["upload"]["url"], data=data, headers=asset["upload"]["headers"]).raise_for_status()
requests.post(f"{API}/assets/{asset['asset_id']}/complete", headers=H).raise_for_status()
asset_id = asset["asset_id"]

# 2. Submit to deep-fryer-v1
job = requests.post(f"{API}/engines/deep-fryer-v1/process", headers=H,
    json={
        "params": {
            "gates": [
                [
                    "rx",
                    0.5
                ]
            ],
            "mask_bin_size": 4,
            "mask_min_region": 16,
            "tile_size": 4
        },
        "input_files": {
            "image": asset_id
        }
    }).json()

# 3. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 4. Fetch the result — output slots: result
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
# Upload first — see the Assets guide; put the returned asset_id in input_files.
curl -s -X POST https://api.mothquantum.com/api/v1/engines/deep-fryer-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "gates": [
      [
        "rx",
        0.5
      ]
    ],
    "mask_bin_size": 4,
    "mask_min_region": 16,
    "tile_size": 4
  },
  "input_files": {
    "image": "$ASSET_ID"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

A classic deep-fry filter gets there by cranking saturation, contrast, and
sharpening. This engine reaches for the same chaotic, crunchy color result
through genuine quantum interference instead, one tile at a time.

Each tile becomes a square lattice of qubits, one per pixel. A pixel's hue and
lightness place its qubit on the Bloch sphere (hue as the azimuthal phase,
lightness as the polar angle, like a compass bearing and a latitude fixing a
point on a globe). Saturation stays out of the circuit and is reattached
afterwards, so the amount of color in a pixel never changes, only which color
and how bright. The requested gates are then applied across the tile: single-
qubit gates touch every pixel, two-qubit gates couple neighbors on the
lattice, so color genuinely mixes through interference and entanglement
rather than an average. Reading each qubit's Bloch vector back out gives the
tile its new, deep-fried hue and lightness.

##### How to use

Invoke the engine through the platform with a JSON params payload and one or
two image files attached:

- `image` — required. The source image. Supported formats: PNG, JPEG, WebP,
  BMP, TIFF.
- `mask` — optional. A single-channel (or RGB) image the same size as `image`,
  where brighter pixels receive more of the effect and darker pixels keep the
  original color. If omitted, the alpha channel of `image` is used as the
  mask; for RGB input with no alpha, the whole image is processed. The mask
  is split into disjoint connected regions, each processed as its own tiled
  sub-image scoped to that region's bounding box, so a few small scattered
  selections on an otherwise-empty mask don't tile the entire canvas.

Optionally, the params object may also include:

- `gates` — a list of `[gate_name, intensity]` pairs, applied to the tile's
  qubit lattice in order. `intensity` is normalized to `[0, 1]`: for
  parametric gates (`rx`, `ry`, `rz`, `p`, `rxx`, `ryy`, `rzz`, `rzx`, `crx`,
  `cry`, `crz`, `cp`) it scales the rotation angle up to `pi`; for
  non-parametric gates (`h`, `x`, `y`, `z`, `s`, `sdg`, `t`, `tdg`, `sx`, `cx`,
  `cy`, `cz`, `ch`, `swap`, `iswap`) it raises the gate to that fractional
  power, so `0` is the identity and `1` is the full gate. Default
  `[["rx", 0.5]]`.
- `tile_size` — side length of the square qubit lattice used as the
  processing kernel. A tile near a mask region's edge is simulated at its
  true, smaller size rather than padded. Must keep `tile_size ** 2` within
  `MAX_QUBITS`, since the whole lattice is simulated as one statevector.
  Default `4`.
- `mask_bin_size` — mask quantisation step as a percentage of 255. Pixel
  values below this threshold collapse into the background, suppressing
  JPEG/WebP compression artifacts from being treated as separate mask
  regions. Default `4.0`.
- `mask_min_region` — minimum connected-component size in pixels after
  quantisation. Smaller components are discarded. Default `16`.

##### Output

Returns an image the same size and format as the input, deep-fried by having
its hue and lightness reshaped by the circuit while saturation is preserved
exactly. The original alpha channel, if any, is preserved unchanged.

#### Related engines

- [Quantum Blur](/docs/engines/blur-v1) — `blur-v1`, Image → Image
- [Quantum Teleblur](/docs/engines/telablur-v1) — `telablur-v1`, Image → Image
- [Tessa Image](/docs/engines/tessa-image-v1) — `tessa-image-v1`, Image → Image
- [Blur Jazz](/docs/engines/blur-midi-v1) — `blur-midi-v1`, Audio → Audio


---

### Blur Jazz — `blur-midi-v1`

POST https://api.mothquantum.com/api/v1/engines/blur-midi-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>blur-midi-v1</code></dd></div>

  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Aug 28, 2026</dd></div>
</dl>

A unitary, information-preserving blur applied to MIDI piano rolls.

#### Request

`POST /api/v1/engines/blur-midi-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "margin": 0.15,
    "qubits": 20,
    "reach": 0,
    "resolution": 0,
    "strength": 0.5,
    "threshold": 0.1
  },
  "input_files": {
    "midi": "9f8e7d6c-5b4a-4d21-8abc-def012345678"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `margin` | number \| null | no | `0.15` | Fraction of the active pitch span to pad above and below before blurring, giving the blur room to spread into adjacent pitches. `0` — no padding; blur is hard-clipped at the boundary notes. Default 0.15. |
| `mask` | array \| null | no | `null` | List of regions to blur, each as [track_index, start_seconds, end_seconds]. When omitted every note track is blurred in full. Tracks and time ranges not covered by the mask pass through unchanged. Example: [[1, 0.5, 2.0], [2, 1.0, 3.5]]. |
| `qubits` | integer | no | `20` | Qubit budget per blur pass (4–20). Determines the largest piano-roll tile the quantum simulator handles in one shot; larger values avoid tiling but require more simulation memory. Default 20. (min 4, max 20) |
| `reach` | number | no | `0` | Non-locality of the blur:  - `0` — fully local: only neighbouring pitches/times mix. - `1` — fully non-local: any pitch can mix with any other. (min 0, max 1) |
| `resolution` | integer | no | `0` | Number of MIDI ticks per piano-roll step (integer ≥ 0). `0` (default) — auto: uses the 5th-percentile note duration, robust to sequencer-artefact grace notes. Any positive value sets the step size directly; larger values produce a coarser grid and faster blur. (min 0) |
| `strength` | number | no | `0.5` | Blur strength (0 = unchanged, 1 = maximum). (min 0, max 1) |
| `threshold` | number | no | `0.1` | Relative noise gate: a velocity delta must exceed threshold × max_velocity_in_roll to emit a note. Scales with the loudest note so it suppresses artefacts proportionally regardless of the overall dynamic level. Default 0.1. (min 0, max 1) |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `midi` | `audio/midi`, `audio/mid` | yes | The MIDI file to process. Supported formats: MIDI 0, 1, and 2. Output is returned in the same format and tick resolution as the input. |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "blur-midi-v1-1b9d6bcd-result.mid",
      "content_type": "audio/midi",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 18000 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `audio/midi` | yes | The blurred MIDI file, in the same SMF type and tick resolution as the input. |

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_midi` | The MIDI file could not be parsed (corrupt, truncated, or not a valid SMF file). |
| `no_notes` | The MIDI file contains no note_on events — nothing to blur. |
| `invalid_params` | One or more params fields failed Pydantic validation. |
| `blur_failed` | The quantum blur circuit failed on a piano-roll tile. |
| `encoding_failed` | The blurred piano roll could not be re-encoded as a MIDI file. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Upload the input as an asset (slot "midi": audio/midi, audio/mid)
path = Path("input.png"); data = path.read_bytes()
asset = requests.post(f"{API}/assets", headers=H,
    json={"filename": path.name, "content_type": "audio/midi", "size_bytes": len(data)}).json()
requests.put(asset["upload"]["url"], data=data, headers=asset["upload"]["headers"]).raise_for_status()
requests.post(f"{API}/assets/{asset['asset_id']}/complete", headers=H).raise_for_status()
asset_id = asset["asset_id"]

# 2. Submit to blur-midi-v1
job = requests.post(f"{API}/engines/blur-midi-v1/process", headers=H,
    json={
        "params": {
            "margin": 0.15,
            "qubits": 20,
            "reach": 0,
            "resolution": 0,
            "strength": 0.5,
            "threshold": 0.1
        },
        "input_files": {
            "midi": asset_id
        }
    }).json()

# 3. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 4. Fetch the result — output slots: result
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
# Upload first — see the Assets guide; put the returned asset_id in input_files.
curl -s -X POST https://api.mothquantum.com/api/v1/engines/blur-midi-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "margin": 0.15,
    "qubits": 20,
    "reach": 0,
    "resolution": 0,
    "strength": 0.5,
    "threshold": 0.1
  },
  "input_files": {
    "midi": "$ASSET_ID"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Instead of shifting notes by a fixed interval or time offset, Quantum Blur
scatters every note across every other note at once. The result sounds like a
quantum echo — pitches and rhythmic patterns from one moment and register
reappear, rearranged and faintly, throughout the rest of the piece.

The effect works by representing each MIDI track as a list of multi-stack piano
rolls (note × time), blurring each stack as though it were a height map, then
reconstructing MIDI note events from the blurred stacks.

##### How to use

Invoke the engine with a JSON params payload and one MIDI file attached:

- `midi` — required. Standard MIDI file (.mid/.midi), SMF type 0, 1, or 2.

Optional params:

- `strength` — blur strength (0 = unchanged, 1 = maximum). Default `0.5`.
- `reach` — non-locality of the blur: `0` is fully local (only neighbouring
  pitches/times mix); `1` is maximally non-local. Default `0.0`.
- `qubits` — qubit budget per blur pass (4–20); determines the largest piano-roll
  tile handled in one quantum simulation. Default `20`.
- `threshold` — relative noise gate: a velocity delta must exceed
  `threshold × max_velocity_in_roll` to emit a note event. Suppresses
  low-energy blur artefacts proportionally to the loudest note. Default `0.1`.
- `resolution` — number of MIDI ticks per piano-roll step. `0` (default) =
  auto-detect as the 5th-percentile note duration (robust to grace-note
  artefacts). Any positive integer sets the step size directly, e.g. `120`
  groups 120 ticks per step. Default `0`.
- `margin` — fraction of the active pitch span to pad above and below before
  blurring, giving the blur room to spread into adjacent pitches. Default `0.15`.
- `mask` — list of `[track_index, start_seconds, end_seconds]` entries that
  define which regions to blur. When omitted every note track is blurred in
  full. Tracks and time ranges not in the mask pass through unchanged.

##### Output

Returns the processed MIDI in the same SMF type and tick resolution as the
input (`audio/midi`). SMF types 0, 1, and 2 are all preserved.
Note: only SMF (MIDI 1.0 file format) is supported — MIDI 2.0 is not.

#### Related engines

- [QRC MIDI](/docs/engines/qrc-midi-v1) — `qrc-midi-v1`, Audio → Audio
- [Entanglement Shader](/docs/engines/entanglement-shader-v1) — `entanglement-shader-v1`, JSON → File
- [QRC Train](/docs/engines/qrc-train-v2) — `qrc-train-v2`, JSON → JSON
- [Quantum Blur](/docs/engines/blur-v1) — `blur-v1`, Image → Image


---

### QDrive — `qdrive-api-v1`

POST https://api.mothquantum.com/api/v1/engines/qdrive-api-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>qdrive-api-v1</code></dd></div>

  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 1, 2026</dd></div>
</dl>

QDrive engine

#### Request

`POST /api/v1/engines/qdrive-api-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "machine": "aer",
    "sample": false,
    "shots": 1024,
    "tomography": 0,
    "update_method": "spectral"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `ansatz` | object \| string \| null | no | `null` | QASM3 ansatz circuits keyed by the number of qubits they act on. |
| `coupling_map` | array \| string \| null | no | `null` | Optional coupling map edges, e.g. [[0, 1], [1, 2]]. |
| `machine` | string | no | `"aer"` | Backend to run on; see backend.MACHINES |
| `n_qubits` | integer \| null | no | `null` | Number of qubits in the circuit; required unless the initial_circuit file input is given |
| `sample` | boolean | no | `false` | Also run a shot-based sampler on the final circuit |
| `seed` | integer \| null | no | `null` | RNG seed; a random one is drawn if omitted |
| `shots` | integer | no | `1024` | Shot count used by both the estimator and the sampler |
| `targets` | array \| array \| string | no |  | Ordered QDrive.target() calls; an empty/null entry calls update() instead. An expvals value may be a number, [value, certainty], or a measured[...]-style expression [[word, qubits, coefficient], ...] (optionally [terms, certainty]). |
| `tomography` | integer | no | `0` | 0: none, 1: single-qubit tomography, 2: two-qubit tomography (min 0, max 2) |
| `update_method` | string | no | `"spectral"` | QDrive.update() fitting method: one of ('spectral', 'direct', 'constrained') |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `initial_circuit` | `text/plain` | no |  |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "circuit",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "qdrive-api-v1-1b9d6bcd-circuit.bin",
      "content_type": "text/plain",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/circuit?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 120 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `circuit` | `text/plain` | yes | The final circuit (QASM3), also chainable into a later job's initial_circuit via job:&lt;id>/circuit. |

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_params` | params fail Params' own field validation (type/range). |
| `invalid_initial_circuit` | initial_circuit bytes aren't parseable QASM3. |
| `n_qubits_mismatch` | n_qubits disagrees with initial_circuit's own qubit count. |
| `invalid_coupling_map` | coupling_map isn't a list of 2-qubit edges. |
| `coupling_map_out_of_range` | coupling_map references more qubits than n_qubits. |
| `invalid_ansatz` | an ansatz key isn't an integer qubit count. |
| `invalid_ansatz_qasm` | an ansatz value isn't parseable QASM3. |
| `ansatz_width_mismatch` | an ansatz circuit's qubit count doesn't match its key. |
| `unsupported_target_ansatz` | a target dict carries its own 'ansatz' key, which isn't supported — use the top-level ansatz parameter. |
| `invalid_target` | a target is missing 'qubits', has duplicate/out-of-range qubits, or a non-mapping 'expvals'. |
| `invalid_update_method` | update_method isn't one of spectral, direct, or constrained. |
| `invalid_machine` | machine isn't a backend.get_backend() knows about. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to qdrive-api-v1
job = requests.post(f"{API}/engines/qdrive-api-v1/process", headers=H,
    json={
        "params": {
            "machine": "aer",
            "sample": False,
            "shots": 1024,
            "tomography": 0,
            "update_method": "spectral"
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — output slots: circuit
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/qdrive-api-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "machine": "aer",
    "sample": false,
    "shots": 1024,
    "tomography": 0,
    "update_method": "spectral"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

_No further details provided by the engine author._

#### Related engines

- [QRC Audio](/docs/engines/qrc-audio-v1) — `qrc-audio-v1`, Audio → Audio
- [QRC Generate](/docs/engines/qrc-gen-v2) — `qrc-gen-v2`, File → JSON
- [QRC MIDI](/docs/engines/qrc-midi-v1) — `qrc-midi-v1`, Audio → Audio
- [Retrocausal Echo](/docs/engines/retrocausal-echo-v1) — `retrocausal-echo-v1`, Audio → Audio


---

### Quantum Graph Engine — `graph-v1`

POST https://api.mothquantum.com/api/v1/engines/graph-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>graph-v1</code></dd></div>

  <div><dt>Publisher</dt><dd>Moth</dd></div>
  <div><dt>Usage</dt><dd>5 credits / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 9, 2026</dd></div>
</dl>

Quantum Graph Engine — prepare a quantum graph state and sample it.

#### Request

`POST /api/v1/engines/graph-v1/process` with a JSON body:

```json
{
  "params": {
    "mode": "emu",
    "num_qubits": 4,
    "shots": 1024
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `backend_name` | string \| null | no | `null` | IBM backend to target; omit to auto-select the least busy device. Ignored when mode='emu'. |
| `coupling_map` | array \| null | no | `null` | Graph edges as qubit pairs; omit for a fully connected graph (QuantumGraph's default). |
| `mode` | string | no | `"emu"` | 'emu' runs on a local Aer simulator; 'qpu' submits to IBM hardware. (one of `emu`, `qpu`) |
| `num_qubits` | integer | no | `4` | Number of qubits (graph nodes), 2-20. (min 2, max 20) |
| `operations` | array \| null | no | `null` | State-preparation targets applied in order: 'bloch' sets single-qubit Pauli targets, 'relationship' sets two-qubit targets on a coupled pair. Omit for a random state drawn from 'seed'. |
| `qpu_instance` | string \| null | no | `null` | IBM Quantum instance CRN; required when mode='qpu'. |
| `qpu_token` | string \| null | no | `null` | IBM Quantum API token; required when mode='qpu'. |
| `seed` | integer \| null | no | `null` | Seeds the random graph; the same seed always builds the same circuit. Omit for a fresh random graph. |
| `shots` | integer | no | `1024` | Number of measurement shots. |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": null,
  "result": "<engine-specific JSON — fields below>"
}
```

`result` holds this engine's JSON inline. _The engine author has not documented its fields yet._

A run still going after 300 s is cancelled and the job ends `failed`.

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `graph_init_failed` | QuantumGraph initialization failed. |
| `prep_failed` | State-preparation operations failed — an operation could not be applied to the graph. |
| `simulation_failed` | Aer simulation failed. |
| `ibm_auth_failed` | IBM authentication failed — IBM_QUANTUM_TOKEN missing or invalid. |
| `ibm_submission_failed` | Circuit submission to the IBM QPU failed. |
| `ibm_collection_failed` | Could not retrieve QPU result — job may have been cancelled or backend errored. |
| `invalid_params` | Parameter validation failed. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to graph-v1
job = requests.post(f"{API}/engines/graph-v1/process", headers=H,
    json={
        "params": {
            "mode": "emu",
            "num_qubits": 4,
            "shots": 1024
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — inline JSON
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
print(res["result"])
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/graph-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "mode": "emu",
    "num_qubits": 4,
    "shots": 1024
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

You describe a graph: which qubits are coupled (`coupling_map`, defaulting to
fully connected) and what state to prepare on it (`operations` — single-qubit
Bloch targets and two-qubit Pauli correlations, applied in order). The engine
prepares that state, returns its exact tomography (per-qubit Bloch vectors and
per-edge two-qubit expectation values), samples it (locally or on IBM
hardware), and scores the dominant outcome against the graph's edges. Omit
graph and operations and it demos itself with a random (seedable) state.

Built on [QuantumGraph](https://github.com/moth-quantum/QuantumGraph).

##### What you send

`application/json`:

```json
{
  "num_qubits": 4,
  "coupling_map": [[0, 1], [1, 2], [2, 3]],
  "operations": [
    {"type": "bloch", "qubit": 0, "paulis": {"X": 1.0}},
    {"type": "relationship", "qubits": [0, 1], "paulis": {"ZZ": 1.0}}
  ],
  "shots": 1024,
  "mode": "emu"
}
```

- **`coupling_map`** *(optional)* — the graph edges as qubit pairs. Omit for a
  fully connected graph.
- **`operations`** *(optional)* — state-preparation targets, applied in order.
  `"bloch"` sets single-qubit Pauli expectation targets on one qubit;
  `"relationship"` sets two-qubit targets (e.g. `ZZ`) on a coupled pair, which
  must be a `coupling_map` edge. Each operation's `update` flag (default true)
  refreshes the tracked state so later operations account for earlier ones;
  set it false for a faster, blind application. Omit `operations` entirely for
  a random state — every qubit gets a random Bloch vector and every edge a
  random ±1 ZZ correlation.
- **`seed`** — fixes the random state when `operations` is omitted: the same
  seed always builds the same circuit, so you can compare `emu` and `qpu` runs
  on identical states.
- **`mode`** — `"emu"` (local simulator, noiseless, seconds) or `"qpu"`
  (IBM hardware, real noise, queue can be minutes–hours; requires
  `qpu_token` and `qpu_instance`).

Remaining parameters (`num_qubits`, `shots`, `backend_name`) are documented in
the request schema below.

##### What you get back

- **`output.tomography`** — the exact prepared state, before any sampling:
  `bloch` (per-qubit `\{X, Y, Z}` expectation values) and `relationships`
  (per-edge two-qubit Pauli expectation values, keyed `"a,b"`). Computed
  classically at build time, so it is noise-free even on QPU runs — compare it
  against the sampled counts to see what the hardware did.
- **`output.measurements`** — the top 20 bitstrings with count and
  probability — plus `dominant_bitstring` and `edge_agreement_score`: the
  fraction of graph edges whose two bits agree in the dominant bitstring.
- The resolved `coupling_map` is echoed back so both are interpretable
  without the request.

---

##### Pipeline (internal)

  build   → graph from coupling_map (default fully connected) → operations or
             random (seeded) targets → capture exact tomography → QASM bytes
  submit  → EMU: run Aer locally → counts │ QPU: transpile + submit to IBM → job_id
  collect → EMU: passthrough │ QPU: poll IBM until done → counts
  format  → rank bitstrings, score edge agreement → final output

Bitstring convention: submit/collect reverse Qiskit's qubit-0-rightmost counts
to qubit-0-LEFTMOST before returning — index i of a bitstring addresses
qubit i directly.

#### Related engines

- [Coin Toss](/docs/engines/coin-toss-v1) — `coin-toss-v1`, JSON → JSON
- [Qpixl](/docs/engines/qpixl-v1) — `qpixl-v1`, JSON → JSON
- [Quantum Blur Core](/docs/engines/blur-core-v1) — `blur-core-v1`, JSON → JSON
- [Quantum Echo](/docs/engines/otoc-echo-v1) — `otoc-echo-v1`, JSON → JSON


---

### Quantum Labyrinth Engine — `labyrinth-v1`

POST https://api.mothquantum.com/api/v1/engines/labyrinth-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>labyrinth-v1</code></dd></div>

  <div><dt>Publisher</dt><dd>Moth</dd></div>
  <div><dt>Usage</dt><dd>5 credits / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 10, 2026</dd></div>
</dl>

Quantum Labyrinth Engine — turn a level blueprint into a quantum-generated maze.

#### Request

`POST /api/v1/engines/labyrinth-v1/process` with a JSON body:

```json
{
  "params": {
    "fraction": 0.3333333333333333,
    "k": 3,
    "mode": "emu",
    "shots": 4096,
    "steps": 3,
    "top_n": 16
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `backend_name` | string \| null | no | `null` | IBM backend to target; omit to auto-select the least busy device. Ignored when mode='emu'. |
| `fraction` | number | no | `0.3333333333333333` | Strength of each ZZ prep step, as a fraction of a full rotation. (max 1) |
| `k` | integer | no | `3` | Tomography correlation length: expectation values tracked over paths of k connected qubits; higher is more faithful but costlier (max 4). (min 1, max 4) |
| `level_data` | object | no |  | Level definition: grid size, qubit count, coupling map, and initial states. |
| `mode` | string | no | `"emu"` | 'emu' runs on a local Aer simulator; 'qpu' submits to IBM hardware. (one of `emu`, `qpu`) |
| `qpu_instance` | string \| null | no | `null` | IBM Quantum instance CRN; falls back to IBM_QUANTUM_INSTANCE env var. |
| `qpu_token` | string \| null | no | `null` | IBM Quantum API token; falls back to IBM_QUANTUM_TOKEN env var. |
| `shots` | integer | no | `4096` | Number of measurement shots (max 10,000). (max 10000) |
| `steps` | integer | no | `3` | Number of ZZ prep sweeps over the lattice (max 5). (min 1, max 5) |
| `top_n` | integer | no | `16` | Most-probable measurements kept in the output; -1 keeps all. (min -1) |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": null,
  "result": "<engine-specific JSON — fields below>"
}
```

`result` holds this engine's JSON inline. _The engine author has not documented its fields yet._

A run still going after 300 s is cancelled and the job ends `failed`.

##### Engine error codes

Returned as `422` (validation) or as `error.type` on a failed job. Generic errors: [Errors & rate limits](/docs/errors).

| Code | Meaning |
|---|---|
| `invalid_level` | level_data validation failed — missing grid_size, num_qubits, or coupling_map. |
| `graph_init_failed` | QuantumGraph initialization failed. |
| `prep_failed` | ZZ state preparation loop failed. |
| `emu_cap_exceeded` | num_qubits exceeds the local-simulation cap; use mode="qpu" for larger lattices. |
| `simulation_failed` | Aer simulation failed. |
| `ibm_auth_failed` | IBM authentication failed — IBM_QUANTUM_TOKEN missing or invalid. |
| `backend_too_small` | level_data requires more qubits than the selected IBM backend provides. |
| `ibm_submission_failed` | Circuit submission to the IBM QPU failed. |
| `ibm_collection_failed` | Could not retrieve QPU result — job may have been cancelled or backend errored. |
| `invalid_params` | Parameter validation failed. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to labyrinth-v1
job = requests.post(f"{API}/engines/labyrinth-v1/process", headers=H,
    json={
        "params": {
            "fraction": 0.3333333333333333,
            "k": 3,
            "mode": "emu",
            "shots": 4096,
            "steps": 3,
            "top_n": 16
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — inline JSON
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
print(res["result"])
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/labyrinth-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "fraction": 0.3333333333333333,
    "k": 3,
    "mode": "emu",
    "shots": 4096,
    "steps": 3,
    "top_n": 16
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

You describe a maze as a grid of rooms and say which neighbouring rooms connect.
The engine turns each connection into a two-qubit correlation, prepares that
quantum state, samples it (locally or on IBM hardware), and returns level data
your game can render directly.

##### What you send

`application/json`:

```json
{
  "level_data": {
    "grid_size": {"rows": 4, "cols": 4},
    "num_qubits": 16,
    "coupling_map": [[0, 4], [1, 5], [4, 5], [5, 9]]
  },
  "shots": 4096,
  "mode": "emu"
}
```

- **`level_data.grid_size`** — `rows` × `cols`; one room per cell.
- **`level_data.num_qubits`** — must equal `rows * cols` (one qubit per room).
- **`level_data.coupling_map`** — the adjacent room pairs that should be **open
  corridors**. Any grid-adjacent pair *not* listed becomes a **wall**. Rooms are
  numbered row-major (room `r*cols + c`); only horizontal/vertical neighbours are
  valid edges — a diagonal or non-adjacent pair is rejected.
- **`level_data.initial_states`** *(optional)* — game metadata keyed by room
  number. Only the `radiating` flag is used and copied verbatim into the output;
  any `X`/`Y`/`Z` here are ignored (prep always starts from `|+⟩^N`).
- **`mode`** — `"emu"` (local simulator, ≤20 qubits, noiseless, seconds) or
  `"qpu"` (IBM hardware, uncapped, real noise, queue can be minutes–hours).

Remaining parameters (`shots`, `steps`, `fraction`, `k`, `top_n`,
`backend_name`) are documented in the request schema below.

---

##### Pipeline (internal)

  build   → level_data → ZZ-prep QuantumGraph (classical tomography) → QASM bytes
  submit  → EMU: run Aer locally → counts │ QPU: transpile + submit to IBM → job_id
  collect → EMU: passthrough │ QPU: poll IBM until done → counts
  format  → assemble the game JSON contract → final output

Bitstring convention: submit/collect reverse Qiskit's qubit-0-rightmost counts to
qubit-0-LEFTMOST before returning. The labyrinth room helpers and the per-edge
ZZ-from-counts math expect qubit-0 at string index 0, so format_result consumes
the leftmost strings DIRECTLY with no further reversal.

#### Related engines

- [Coin Toss](/docs/engines/coin-toss-v1) — `coin-toss-v1`, JSON → JSON
- [Qpixl](/docs/engines/qpixl-v1) — `qpixl-v1`, JSON → JSON
- [Quantum Blur Core](/docs/engines/blur-core-v1) — `blur-core-v1`, JSON → JSON
- [Quantum Echo](/docs/engines/otoc-echo-v1) — `otoc-echo-v1`, JSON → JSON


---

### QRC MIDI — `qrc-midi-v1`

POST https://api.mothquantum.com/api/v1/engines/qrc-midi-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>qrc-midi-v1</code></dd></div>

  <div><dt>Usage</dt><dd>5 credits / run</dd></div>
  <div><dt>Updated</dt><dd>Aug 25, 2026</dd></div>
</dl>

qrc-midi-v1 — sequence MIDI notes with a quantum reservoir.

#### Request

`POST /api/v1/engines/qrc-midi-v1/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "bpm": 120,
    "length": 10,
    "loop": true,
    "quality": "moderate",
    "variation": 1,
    "velocity": 100
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `bpm` | number | no | `120` | Tempo of the generated file in beats per minute. Note durations are preserved either way — this only sets the beat grid a DAW sees. |
| `length` | integer | no | `10` | How many notes to generate (max 500) |
| `loop` | boolean | no | `true` | Treat the melody as looping material — the end flows back into the start. Learning only. |
| `quality` | string | no | `"moderate"` | How hard to train when learning a fresh file (no `model`): instant skips training for a quick untrained shuffle; fast is quick and rough; complete is slow and tight. (one of `instant`, `fast`, `moderate`, `complete`) |
| `seed` | integer \| null | no | `null` | Change for a different result, keep fixed to reproduce one. On a fresh file it also fixes the learned reservoir; when reusing a `model` it just varies the take, so you can fan out independent takes by changing it. |
| `variation` | number | no | `1` | How freely the result departs from the learned order: low = tight and repetitive, high = loose and surprising. |
| `velocity` | integer | no | `100` | How hard every generated note is struck (1–127). One value for the whole file. (min 1, max 127) |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `midi` | `audio/midi`, `audio/x-midi` | no |  |
| `model` | `application/json` | no |  |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "result",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "qrc-midi-v1-1b9d6bcd-result.mid",
      "content_type": "audio/midi",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/result?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    },
    {
      "slot": "state",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345671",
      "filename": "qrc-midi-v1-1b9d6bcd-state.json",
      "content_type": "application/json",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/state?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    },
    {
      "slot": "model",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345672",
      "filename": "qrc-midi-v1-1b9d6bcd-model.json",
      "content_type": "application/json",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/model?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 3600 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `result` | `audio/midi` | yes | The generated MIDI. |
| `state` | `application/json` | yes | Advanced reservoir state; reuse on a later call as job:&lt;id>/state. |
| `model` | `application/json` | no | Pristine trained model for fan-out; reuse as job:&lt;id>/model. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to qrc-midi-v1
job = requests.post(f"{API}/engines/qrc-midi-v1/process", headers=H,
    json={
        "params": {
            "bpm": 120,
            "length": 10,
            "loop": True,
            "quality": "moderate",
            "variation": 1,
            "velocity": 100
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — output slots: result, state, model
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/qrc-midi-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "bpm": 120,
    "length": 10,
    "loop": true,
    "quality": "moderate",
    "variation": 1,
    "velocity": 100
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

A self-contained hybrid engine: one call trains a reservoir over the notes of a MIDI file, generates
a new ordering of them, and writes it back out as a `.mid`. Each note is a `pitch_duration` token
(e.g. "67_1.5") — the reservoir work is delegated to `qrc_core` (train/generate/state); this engine
only owns the MIDI codec (decode/encode) and the friendly parameter surface.

`quality: "instant"` skips training entirely (a quick untrained shuffle); the other levels train.

Three seed paths, chosen by which inputs arrive (no mode flag):
  - no `model`, quality != instant -> TRAIN on the file's notes, then generate. Emits a pristine
    `files.model` (reusable for fan-out) plus the advanced `files.state`.
  - no `model`, quality == instant -> untrained shuffle, emits `files.state` only.
  - `model` given -> reuse it (no `midi` needed): a pristine model (`job:&lt;id>/model`) fans out an
    INDEPENDENT take (vary `seed`); an advanced state (`job:&lt;id>/state`) CONTINUES that trajectory.
    The note vocabulary rides inside the artifact — nothing to re-upload.

Reservoir tuning (qubits, shots, epochs, windowing) lives in reservoir_tuning.py — a self-contained
"don't touch" file. Everything here is MIDI: the note codec and the request/response flow.

#### Related engines

- [QRC Audio](/docs/engines/qrc-audio-v1) — `qrc-audio-v1`, Audio → Audio
- [QRC Generate](/docs/engines/qrc-gen-v2) — `qrc-gen-v2`, File → JSON
- [Retrocausal Echo](/docs/engines/retrocausal-echo-v1) — `retrocausal-echo-v1`, Audio → Audio
- [Blur Jazz](/docs/engines/blur-midi-v1) — `blur-midi-v1`, Audio → Audio


---

### QRC Train — `qrc-train-v2`

POST https://api.mothquantum.com/api/v1/engines/qrc-train-v2/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>qrc-train-v2</code></dd></div>

  <div><dt>Usage</dt><dd>5 credits / run</dd></div>
  <div><dt>Updated</dt><dd>Aug 25, 2026</dd></div>
</dl>

qrc-train-v1 — train a quantum reservoir on a token sequence, emit a reusable model artifact.

#### Request

`POST /api/v1/engines/qrc-train-v2/process` with a JSON body:

```json
{
  "params": {
    "epochs": 50,
    "mixing": 0.7,
    "mode": "order",
    "num_qubits": 5,
    "num_random_gates": 10,
    "periodic": true,
    "sample_fraction": 1,
    "sample_length": 15,
    "sequence": [
      1,
      2,
      3,
      2,
      1,
      1,
      2,
      3,
      2,
      1,
      1,
      2,
      3,
      2,
      1,
      1,
      2,
      3,
      2,
      1
    ],
    "shots": 3000,
    "washout": 5
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `epochs` | integer | no | `50` | Readout training epochs (readout.epoch) (min 1, max 500) |
| `mixing` | number | no | `0.7` | How much each reservoir step replaces its memory (reservoir.mixing); 1 = fully replaced (max 1) |
| `mode` | string | no | `"order"` | Window-sampling mode (handler.mode) (one of `random`, `order`, `stride`) |
| `num_qubits` | integer | no | `5` | Reservoir qubits (reservoir.num_qubits) (min 2, max 12) |
| `num_random_gates` | integer | no | `10` | Random gates mixed into each reservoir step (reservoir.num_random_gates) (min 0, max 100) |
| `periodic` | boolean | no | `true` | Allow windows to wrap past the end of the sequence (handler.periodic) |
| `sample_fraction` | number | no | `1` | Fraction of the candidate windows `mode` can produce that are kept, via quasi-random subsampling (handler.sample_fraction) (max 1) |
| `sample_length` | integer | no | `15` | Window length (handler.sample_length) (min 1, max 256) |
| `seed` | integer \| null | no | `null` | Top-level RNG seed shared by every component that doesn't set its own (config.seed). None = pick a random seed for this run; it's recorded in the returned model's state, so the exact run can be reproduced later by passing it back explicitly. |
| `sequence` | array | no | `[1,2,3,2,1,1,2,3,2,1,1,2,3,2,1,1,2,3,2,1]` | Tokens to train on — any hashable values (ints, strings, ...) forming a unique set |
| `shots` | integer | no | `3000` | Measurement shots (backend.shots) (min 1, max 8192) |
| `vocabulary` | array \| null | no | `null` | Fixed vocabulary covering the full input space (e.g. all MIDI pitches, all ascii chars). None = derive the vocabulary from the sequence's own distinct tokens, in the order they first appear (default). |
| `washout` | integer | no | `5` | Washout period; must be &lt; sample_length (readout.washout). (max 255) |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "state",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "qrc-train-v2-1b9d6bcd-state.json",
      "content_type": "application/json",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/state?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 3600 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `state` | `application/json` | yes | Trained reservoir state; reuse in qrc-gen-v2 via input_files.state (train once, generate many). |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to qrc-train-v2
job = requests.post(f"{API}/engines/qrc-train-v2/process", headers=H,
    json={
        "params": {
            "epochs": 50,
            "mixing": 0.7,
            "mode": "order",
            "num_qubits": 5,
            "num_random_gates": 10,
            "periodic": True,
            "sample_fraction": 1,
            "sample_length": 15,
            "sequence": [
                1,
                2,
                3,
                2,
                1,
                1,
                2,
                3,
                2,
                1,
                1,
                2,
                3,
                2,
                1,
                1,
                2,
                3,
                2,
                1
            ],
            "shots": 3000,
            "washout": 5
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — output slots: state
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/qrc-train-v2/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "epochs": 50,
    "mixing": 0.7,
    "mode": "order",
    "num_qubits": 5,
    "num_random_gates": 10,
    "periodic": true,
    "sample_fraction": 1,
    "sample_length": 15,
    "sequence": [
      1,
      2,
      3,
      2,
      1,
      1,
      2,
      3,
      2,
      1,
      1,
      2,
      3,
      2,
      1,
      1,
      2,
      3,
      2,
      1
    ],
    "shots": 3000,
    "washout": 5
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Trains via qrc.generator.QRCGenerator (Qiskit Aer backend). The event &lt;-> index vocabulary
(a SequenceMapping) is fixed up front from the request's tokens, since the new library sizes
the readout from it and does not refit one during learn(). Returns the training loss inline as
`output`, and the trained state (vocabulary, training params, readout weights + reservoir
memory — everything qrc-gen-v1 needs to rebuild an identical generator and load it, `version`
included) as the named binary output `state` (archaeo-sdk's named-binary-output + JSON envelope,
see features-0.6.md) — pass it straight through as qrc-gen-v1's own `state` input.

#### Related engines

- [Blur Jazz](/docs/engines/blur-midi-v1) — `blur-midi-v1`, Audio → Audio
- [Entanglement Shader](/docs/engines/entanglement-shader-v1) — `entanglement-shader-v1`, JSON → File
- [Quantum Blur](/docs/engines/blur-v1) — `blur-v1`, Image → Image
- [Quantum Teleblur](/docs/engines/telablur-v1) — `telablur-v1`, Image → Image


---

### QRC Generate — `qrc-gen-v2`

POST https://api.mothquantum.com/api/v1/engines/qrc-gen-v2/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>qrc-gen-v2</code></dd></div>

  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Aug 25, 2026</dd></div>
</dl>

qrc-gen-v1 — generate a sequence from a trained QRC model.

#### Request

`POST /api/v1/engines/qrc-gen-v2/process` with a JSON body — upload files as assets first and pass their ids under the slot names:

```json
{
  "params": {
    "length": 10,
    "variation": 1
  },
  "input_files": {
    "state": "9f8e7d6c-5b4a-4d21-8abc-def012345678"
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `initial_events` | array \| null | no | `null` | Warm up the reservoir on these events before generating, instead of the whole vocabulary (the default for a fresh model). Tokens must belong to the model's vocabulary. Ignored when continuing from a `state` that is itself a prior qrc-gen-v1 output, unless given explicitly to deliberately re-seed the trajectory. |
| `length` | integer | no | `10` | Number of tokens to generate |
| `random_seed` | integer \| null | no | `null` | RNG seed for this call's own generation randomness (softmax sampling) — applied after the model is loaded, not the seed the QRC was trained with (that one is always reused exactly, to reconstruct the reservoir faithfully). None = keep whatever RNG state the model already has (deterministic given the same inputs); give a value to force a specific, reproducible sampling trajectory. |
| `shots` | integer \| null | no | `null` | Measurement shots during generation (backend.shots). None = keep whatever shots the model was trained (or last generated) with. |
| `variation` | number | no | `1` | Sampling temperature: low = deterministic/repetitive, high = random |
| `vocabulary` | array \| null | no | `null` | Relabel the model's output space: the trained reservoir/readout only depend on vocabulary *size*, not identity, so any vocabulary with the same number of distinct tokens as the model's own can be swapped in — generation then emits from this vocabulary instead. A different size raises `incompatible_model` (readout shape mismatch). |

##### Input files

Upload each file as an asset first ([Assets](/docs/assets)), then pass its id under the slot name.

| Slot | Accepts | Required | Description |
|---|---|---|---|
| `state` | `application/json` | yes |  |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": [
    {
      "slot": "state",
      "output_asset_id": "9f8e7d6c-5b4a-4d21-8abc-def012345670",
      "filename": "qrc-gen-v2-1b9d6bcd-state.json",
      "content_type": "application/json",
      "size_bytes": 524288,
      "url": "https://storage.example.com/jobs/1b9d6bcd/state?X-Amz-Signature=…",
      "expires_at": "2026-09-08T14:43:18Z"
    }
  ],
  "result": null
}
```

Each `url` is presigned: fetch it with no auth header before `expires_at`. Every output is also an asset you own (`output_asset_id`), downloadable again later.

A run still going after 3600 s is cancelled and the job ends `failed`.

Output slots:

| Slot | Content types | Required | Description |
|---|---|---|---|
| `state` | `application/json` | yes | Updated reservoir state; chain into a further qrc-gen-v2 call via input_files.state. |

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Upload the input as an asset (slot "state": application/json)
path = Path("input.png"); data = path.read_bytes()
asset = requests.post(f"{API}/assets", headers=H,
    json={"filename": path.name, "content_type": "application/json", "size_bytes": len(data)}).json()
requests.put(asset["upload"]["url"], data=data, headers=asset["upload"]["headers"]).raise_for_status()
requests.post(f"{API}/assets/{asset['asset_id']}/complete", headers=H).raise_for_status()
asset_id = asset["asset_id"]

# 2. Submit to qrc-gen-v2
job = requests.post(f"{API}/engines/qrc-gen-v2/process", headers=H,
    json={
        "params": {
            "length": 10,
            "variation": 1
        },
        "input_files": {
            "state": asset_id
        }
    }).json()

# 3. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 4. Fetch the result — output slots: state
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
for out in res["outputs"]:
    Path(out["slot"]).write_bytes(requests.get(out["url"]).content)
```

#### curl

```bash
# Upload first — see the Assets guide; put the returned asset_id in input_files.
curl -s -X POST https://api.mothquantum.com/api/v1/engines/qrc-gen-v2/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "length": 10,
    "variation": 1
  },
  "input_files": {
    "state": "$ASSET_ID"
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

The `state` input is qrc-train-v1's named binary output (or a prior qrc-gen-v1 call's own
`state` output) — a plain dict of JSON-safe values (see `_to_native`) carrying `version`, the
vocabulary, the training parameters, and the trained readout/reservoir weights. Accepted either
already as that dict (composing engines directly in Python, e.g. in a notebook) or as
JSON-encoded bytes/str (a file upload or `job:&lt;id>/state` named-output reference — see
features-0.6.md). Rebuilds the QRCGenerator the same way qrc-train-v1 does: load this engine's
own copy of config.yaml and apply the state's training parameters over it — then restores the
trained readout and reservoir memory, and generates a new sequence.

#### Related engines

- [QRC Audio](/docs/engines/qrc-audio-v1) — `qrc-audio-v1`, Audio → Audio
- [QRC MIDI](/docs/engines/qrc-midi-v1) — `qrc-midi-v1`, Audio → Audio
- [Retrocausal Echo](/docs/engines/retrocausal-echo-v1) — `retrocausal-echo-v1`, Audio → Audio
- [QDrive](/docs/engines/qdrive-api-v1) — `qdrive-api-v1`, Text → Text


---

### Tomography Api — `tomography-api-v2`

POST https://api.mothquantum.com/api/v1/engines/tomography-api-v2/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>tomography-api-v2</code></dd></div>
  <div><dt>Version</dt><dd>v0.2.0</dd></div>

  <div><dt>Usage</dt><dd>1 credit / run</dd></div>
  <div><dt>Updated</dt><dd>Sep 23, 2026</dd></div>
</dl>

Simple core engine to compute relevant quantities of a quantum circuit

#### Request

`POST /api/v1/engines/tomography-api-v2/process` with a JSON body:

```json
{
  "params": {
    "backend_name": "automatic",
    "circuit_qasm": "…",
    "classical_mutual_information": true,
    "double_tomography": true,
    "mutual_information": true,
    "provider_name": "aer",
    "shots": 4096,
    "single_tomography": true
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `backend_name` | string | no | `"automatic"` | mothprovider backend/method within provider_name |
| `circuit_qasm` | string | yes |  | OpenQASM 2 source of the circuit to analyze |
| `classical_mutual_information` | boolean | no | `true` | Whether to compute classical (Shannon) mutual information between each pair's measurement outcomes, separately for the X, Y, and Z basis |
| `double_tomography` | boolean | no | `true` | Whether to perform double tomography |
| `mutual_information` | boolean | no | `true` | Whether to compute quantum mutual information (von Neumann entropies) |
| `provider_name` | string | no | `"aer"` | mothprovider provider used to execute the circuits |
| `qubit_list` | array | no |  | List of qubits to measure |
| `qubit_pair_list` | array | no |  | List of qubit pairs to measure |
| `shots` | integer | no | `4096` | Shots per executed measurement circuit |
| `single_tomography` | boolean | no | `true` | Whether to perform single tomography |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": null,
  "result": "<engine-specific JSON — fields below>"
}
```

`result` holds this engine's JSON inline. _The engine author has not documented its fields yet._

A run still going after 10800 s is cancelled and the job ends `failed`.

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to tomography-api-v2
job = requests.post(f"{API}/engines/tomography-api-v2/process", headers=H,
    json={
        "params": {
            "backend_name": "automatic",
            "circuit_qasm": "…",
            "classical_mutual_information": True,
            "double_tomography": True,
            "mutual_information": True,
            "provider_name": "aer",
            "shots": 4096,
            "single_tomography": True
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — inline JSON
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
print(res["result"])
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/tomography-api-v2/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "backend_name": "automatic",
    "circuit_qasm": "…",
    "classical_mutual_information": true,
    "double_tomography": true,
    "mutual_information": true,
    "provider_name": "aer",
    "shots": 4096,
    "single_tomography": true
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

_No further details provided by the engine author._

#### Related engines

- [Coin Toss](/docs/engines/coin-toss-v1) — `coin-toss-v1`, JSON → JSON
- [Qpixl](/docs/engines/qpixl-v1) — `qpixl-v1`, JSON → JSON
- [Quantum Blur Core](/docs/engines/blur-core-v1) — `blur-core-v1`, JSON → JSON
- [Quantum Echo](/docs/engines/otoc-echo-v1) — `otoc-echo-v1`, JSON → JSON


---

### Tamagotchi — `tamagotchi-v1`

POST https://api.mothquantum.com/api/v1/engines/tamagotchi-v1/process

<div className="engine-header">
</div>

<dl className="engine-facts">
  <div><dt>Engine</dt><dd><code>tamagotchi-v1</code></dd></div>

  <div><dt>Usage</dt><dd>0 credits / run</dd></div>
  <div><dt>Updated</dt><dd>Aug 27, 2026</dd></div>
</dl>

Qiskit QEC engine.

#### Request

`POST /api/v1/engines/tamagotchi-v1/process` with a JSON body:

```json
{
  "params": {
    "code": "steane",
    "method": "stabilizer",
    "n_logical": 1,
    "shots": 1024
  }
}
```

Values shown are the defaults. Validation rules: [Submitting jobs](/docs/submitting-jobs).

##### params

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `actions` | array | no |  | list of [gate, target] over logical qubits; gates: I,X,Z,H,S,CX,SE |
| `code` | string | no | `"steane"` | CSS code key (see CODE_REGISTRY) |
| `expected` | array \| null | no | `null` | optional expected per-logical outcome; auto-computed if omitted |
| `method` | string | no | `"stabilizer"` | Aer simulation method |
| `n_logical` | integer | no | `1` | number of logical qubits |
| `noise` | object | no |  |  |
| `seed` | integer \| null | no | `null` | simulator seed for reproducibility |
| `shots` | integer | no | `1024` | number of measurement shots |

#### Response

Submitting returns `202 Accepted`:

```json
{
  "job_id": "1b9d6bcd-2e3f-4a5b-8c7d-9e0f1a2b3c4d",
  "status": "queued",
  "submitted_at": "2026-09-08T14:40:02Z"
}
```

Poll [job status](/docs/endpoints#jobs) until `completed`, then `GET /api/v1/jobs/{job_id}/result` returns:

```json
{
  "outputs": null,
  "result": "<engine-specific JSON — fields below>"
}
```

`result` holds this engine's JSON inline. _The engine author has not documented its fields yet._

A run still going after 30000 s is cancelled and the job ends `failed`.

#### Python

```python
from pathlib import Path

API = "https://api.mothquantum.com/api/v1"
H = {"Authorization": f"Bearer {os.environ['MOTH_API_KEY']}"}

# 1. Submit to tamagotchi-v1
job = requests.post(f"{API}/engines/tamagotchi-v1/process", headers=H,
    json={
        "params": {
            "code": "steane",
            "method": "stabilizer",
            "n_logical": 1,
            "shots": 1024
        }
    }).json()

# 2. Poll until terminal
while True:
    st = requests.get(f"{API}/jobs/{job['job_id']}/status", headers=H).json()
    if st["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(2)
if st["status"] != "completed":
    raise RuntimeError(f"job {st['status']}: {st['error']}")

# 3. Fetch the result — inline JSON
res = requests.get(f"{API}/jobs/{job['job_id']}/result", headers=H).json()
print(res["result"])
```

#### curl

```bash
curl -s -X POST https://api.mothquantum.com/api/v1/engines/tamagotchi-v1/process \
  -H "Authorization: Bearer $MOTH_API_KEY" -H "Content-Type: application/json" \
  -d '{
  "params": {
    "code": "steane",
    "method": "stabilizer",
    "n_logical": 1,
    "shots": 1024
  }
}'
# → 202 {"job_id": "...", "status": "queued"}
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/status -H "Authorization: Bearer $MOTH_API_KEY"
curl -s https://api.mothquantum.com/api/v1/jobs/$JOB_ID/result -H "Authorization: Bearer $MOTH_API_KEY"
```

Example outputs and interactive runs: [browse showcases in the dashboard](https://platform.mothquantum.com/engines).

#### Details

Turns a declarative list of *logical* actions into a physical qiskit circuit on a
CSS quantum-error-correcting code, runs it under a noise model on the Aer
``stabilizer`` simulator, and reports how often the logical qubits end up in the
expected computational-basis state.

Actions are ``(gate, target)`` tuples over *logical* qubit indices, e.g.::

    [("X", 0), ("CX", (0, 1)), ("SE", [0, 1])]

Single-qubit gates (``X``/``Z``/``H``/``S``) and ``CX`` are applied transversally.
``SE`` is a syndrome-extraction round: ancillas measure the stabilizers and the
error is corrected *in-circuit* using classically-controlled gates (qiskit's
``switch`` conditions on the full syndrome-register integer, so the nonlinear
Hamming lookup — which qubit to flip — is expressible directly).

The engine exposes the platform contract ``run(params) -> dict`` plus a separate
``validate(params) -> None`` pre-flight check.

#### Related engines

- [Coin Toss](/docs/engines/coin-toss-v1) — `coin-toss-v1`, JSON → JSON
- [Qpixl](/docs/engines/qpixl-v1) — `qpixl-v1`, JSON → JSON
- [Quantum Blur Core](/docs/engines/blur-core-v1) — `blur-core-v1`, JSON → JSON
- [Quantum Echo](/docs/engines/otoc-echo-v1) — `otoc-echo-v1`, JSON → JSON


---

## 4. What's in the moth-quantum GitHub org

Checked github.com/moth-quantum (29 repos). No official Python/JS SDK or CLI wrapper
for the Atlas REST API exists as a public repo — build our own client from the docs
above. What is there, and matters:

### `coccoon` — the one genuinely useful reference

A Godot 4 "quantum game engine" built by Moth for the hackathon. Its **Quantum
Caverns** game (`games/quantum_caverns/quantum_caverns.gd`) calls the live Atlas API
(`blur-core-v1`) from real, shipped, working code, and its README says the source
"doubles as a tutorial for calling the Moth API from a coccoon game." Confirms, in
production GDScript rather than a doc example:

- Base URL `https://api.mothquantum.com`, `Authorization: Bearer <raw key>` — no extra encoding.
- Submit → `202` + `job_id` → poll → fetch, exactly as documented.
- **It polls `GET /api/v1/jobs/{job_id}` directly** (not the `/status` suffix the docs
  recommend) and treats `"completed"`, `"succeeded"`, `"done"` all as success —
  defensive coding against status-string drift. Worth matching in our own client:
  accept more than the one documented string.
- Poll interval 0.5s, 60-attempt ceiling (30s) for a small `blur-core-v1` job. Not a
  latency figure for `telablur-v1` on a full-size image — still need our own `probe.py`
  for that.
- Fire-and-forget prefetch pattern (start the next job while the player is still on
  the current one) is exactly the mechanism our plan's "viewer fires next state in
  background" needs — worth reading in full before writing `app.py`.
- Local fallback via `QuantumBlur.height2circuit` / `rx(π·0.125)` / `circuit2height`
  when no API key is set — not needed for us, we always have a key, but shows the
  `strength=0.25` ↔ `rx(π/8)` mapping if we ever want to sanity-check a blur locally.

Also in this repo: **Quantum Caverns' maze generation** uses `blur-core-v1`
(N-dimensional grid blur), not `blur-v1` (image blur) — a different engine from the
one we use for the dodecahedron/photos. And **Celeste (Quantum Remix)** reports its
sprites were "modified via Moth's TESSA tool" — a second, independent confirmation
that `tessa-image-v1` is a real, exercised engine.

### `MicroMoth`

The lightweight statevector simulator (`MicroQiskit` fork) that powers `coccoon`'s
local fallback and `hello-qubits`. Background only — we call the real API, we don't
need a local simulator.

### `quantum-audio` (PyPI: `quantumaudio`)

Moth's own open-source Python package for encoding/decoding digital audio as quantum
circuits (`quantumaudio.encode(audio)` / `.decode(circuit)`). This is very likely the
theory underpinning `qrc-audio-v1` and the echo engines, but it's a research library,
not the Atlas API client — not something we install, just useful if we want to explain
*why* QRC Audio sounds the way it does in a pitch caption.

### `brdf`

A fork of Disney's open-source **BRDF Explorer** (C++, `README-DISNEY` present).
Generic third-party material-preview tool — potentially useful for actually looking
at what `entanglement-shader-v1` produces (it outputs `.osl`/`.glsl`/`.hlsl`/`.mtlx`
shader source, not an image — see §5) before committing to a 3D pipeline, but it's a
desktop C++ app we'd need to build, not a quick win. Low priority.

### `QuantumBlur` (C#) and `Hello-Quantum` (Next.js)

`QuantumBlur` is the original Wootton algorithm ported to C# for Godot/Unity —
background/lineage only. `Hello-Quantum` is a client-only Next.js puzzle-game port
(`lib/quantum-logic.ts`) with no server, no Atlas calls — unrelated to our build
despite the name.

---

## 5. What this changes for our build plan

Corrections against `moth-hack-build-plan-25-09-2026-1832.md` and the earlier
research brief, now that we have the real engine schemas:

1. **Telablur takes two images, not one image + an angle.** Confirmed slug
   `telablur-v1`. Params are `direction` (full/vertical/horizontal), `downscale`,
   `mask_bin_size`, `mask_min_region`, `size` (8–1024), `strength` (0.0–1.0). Input
   slots are `image1`, `image2`, optional `mask`. The plan's recursive step ("state N
   built from 12 images plus the song plus state N-1") needs restating as: **image1 =
   previous state, image2 = one of the 12 source photos** (or a blend), with `strength`
   controlling how much of the new photo bleeds in. The "20% previous state" weighting
   in the plan's degradation mitigation (§7) maps directly to a low `strength` value —
   worth testing `strength≈0.2` first, not 0.5 default.

2. **Entanglement Shader does not output an image.** It outputs a **ZIP** containing
   shader *source* in five formats (OSL, Marmoset `.frag`, GLSL, HLSL, MaterialX) plus
   EXR/HDR reflectance/transmittance lookup tables — "no quantum hardware required at
   render time." For the dodecahedron (Beginner 03) we need an actual renderer that
   consumes one of these (Blender/GLSL in Three.js are the realistic options for a
   browser or exhibition build) rather than treating the output as a texture PNG we
   can just apply. This is a real scope item to plan for, not a one-line texture swap.

3. **"Quantum Echo" (as in the plan's "QRC Audio or Quantum Echo") is the wrong
   engine for making something audible.** `otoc-echo-v1` ("Quantum Echo") takes no
   audio file and produces no audio — it's a pure physics simulation returning a
   trajectory JSON (a tap map: site, depth, real/imaginary amplitude, level, polarity).
   The audio-producing sibling engine is **`retrocausal-echo-v1`** ("Retrocausal
   Echo"), which takes an optional `audio` file, applies the tap map as a quantum
   multi-tap delay, and renders a WAV — this is the one to use for Beginner 02 /
   the "audio through two engines" checklist item. It can also reuse a previously
   measured tap map (`ir` input, chained from a prior job's `ir` output) to re-render
   without re-measuring, which is a real credit-saving trick for iterating on sound.

4. **Credit costs are not uniform.** `qrc-audio-v1`, `qrc-midi-v1`, `qrc-train-v2`,
   `graph-v1`, `labyrinth-v1` cost **5 credits/run**; `retrocausal-echo-v1` and
   `coin-toss-v1` cost **2**; most image/effect engines cost **1**; `tamagotchi-v1` is
   **free**. QRC Audio for the recursive/audio work is the single most expensive
   engine in our plan — budget for that explicitly rather than assuming flat cost
   per job as the plan's §7 credit-ceiling language implies.

5. **Job timeouts differ by engine, and they're long.** `telablur-v1`,
   `entanglement-shader-v1`: 18000s (5h) each. `otoc-echo-v1`: 7200s (2h). These are
   upper bounds before a stuck job is auto-cancelled as `failed`, not typical run
   times — still no published typical latency, so `probe.py` is still the very next
   action regardless of everything else in this document.

6. **Real rate limit and auth details, previously "likely," are now certain:** 300
   req/min per key, `Authorization: Bearer moth_...`, ownership violations return
   `404` never `403`, and a `422` always lists every validation problem at once (fix
   them all in one round trip rather than one-at-a-time).

7. **Confirmed usable for the daisy chain (Intermediate 03):** `telablur-v1`,
   `blur-v1`, `tessa-image-v1`, `deep-fryer-v1`, `entanglement-shader-v1`,
   `qrc-audio-v1`, `retrocausal-echo-v1`, `coin-toss-v1`, `qpixl-v1` — nine real,
   scoped engines, one more than the plan's original eight-engine list, with
   `blur-midi-v1` as a tenth if we ever touch MIDI.

**Still nothing published:** per-engine typical latency (only the timeout ceiling is
documented), and no engine-authoring guide was found in the org's public repos despite
`working-with-engines.md` pointing to one — ask in Discord/the Saturday talks if we
end up wanting to register our own engine rather than just calling public ones.
