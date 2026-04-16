# lv2park Cloudflare Worker

Handles address search logging and email signups for lv2park.com.
Writes directly to Google Sheets via service account auth.

## Endpoints

| Method | Path | Body | Effect |
|--------|------|------|--------|
| POST | /log-search | `{ address, result, lat, lon, page, timestamp }` | Appends row to "Searches" tab |
| POST | /subscribe | `{ email, page }` | Appends row to "Subscribers" tab |

## Google Sheet

`https://docs.google.com/spreadsheets/d/1-P5kFhUvi9JieiHoU9odhRa_HiekjkinnaAqPK27Fik`

Sheet must have two tabs:
- **Searches** — columns: Timestamp, Address, Result, Lat, Lon, Page
- **Subscribers** — columns: Timestamp, Email, Page

Shared with: `lv2park@ew-playground.iam.gserviceaccount.com` (Editor)

## Deploy

### 1. Install Wrangler
```bash
npm install -g wrangler
```

### 2. Login
```bash
wrangler login
```

### 3. Set the service account secret
```bash
wrangler secret put GOOGLE_SA_JSON
```
When prompted, paste the full contents of `ew-playground-42e0ee163a0d.json` and press Enter.

### 4. Deploy
```bash
wrangler deploy
```

Worker will be live at `email.lv2park.com` once DNS is pointed to Cloudflare.

## Local dev (optional)
Create `.dev.vars` (gitignored):
```
GOOGLE_SA_JSON={"type":"service_account",...full JSON...}
```
Then run:
```bash
wrangler dev
```

## Credentials
- Service account: `lv2park@ew-playground.iam.gserviceaccount.com`
- Key file: stored locally at `~/Downloads/ew-playground-42e0ee163a0d.json`
- NEVER commit the key file. It is in `.gitignore`.
