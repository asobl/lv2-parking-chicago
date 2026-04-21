# LV2 Park -- Product Code

**Hosting: GitHub Pages (GitHub Actions deploy)**

The web code lives in `product/web/`. GitHub Pages is configured to deploy via GitHub Actions (not branch root). The deploy job is in `.github/workflows/update.yml` -- it runs after every data update that produces a commit.

The Cloudflare Workers (`lv2park-worker`, `lv2park-email`) handle the email subscribe form only. They live in `product/workers/`.

## Structure

| Folder / File | What it is |
|---|---|
| `web/index.html` | Main site |
| `web/style.css` | All styles |
| `web/app.js` | Frontend JS |
| `web/scripts/` | Python scripts -- data fetch, recap generation |
| `web/data/` | JSON data files -- updated by GitHub Actions |
| `web/game-recaps/` | Generated recap pages |
| `web/blog/` | Blog pages |
| `workers/lv2park-worker/` | Main Cloudflare Worker |
| `workers/lv2park-email/` | Email subscribe Cloudflare Worker |

## GitHub Actions

Three cron jobs in `.github/workflows/`:

| Workflow | Schedule | What it does |
|---|---|---|
| `update.yml` | 4x daily | Fetch data, send digest, generate recaps, deploy to Pages |
| `ticker.yml` | Every 30 min (5-10 PM CT, game days only) | Live ticket scan |
| `monthly-audit.yml` | 1st of each month | Health check email via Resend |

## GitHub Pages Setup

Repo Settings > Pages > Source must be set to **"GitHub Actions"** (not "Deploy from a branch"). The deploy job in `update.yml` uploads `product/web/` as the Pages artifact.

## Live at

lv2park.com via GitHub Pages. Auto-updates 4x daily. Full architecture: `docs/SYSTEM.md`
