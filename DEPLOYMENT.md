# Dashboard Deployment and GitHub Workflow

This guide keeps the current dashboard structure and current processed data, then leaves room to refresh the final spread window later.

## 1. Run Locally

```bash
cd orderly-hyperliquid-case
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/process_data.py
streamlit run dashboard/app.py
```

Open the local URL Streamlit prints, usually:

```text
http://localhost:8501
```

## 2. Collect the Final 72-Hour Spread Window

Target final spread window:

```text
2026-06-05 00:00:00 Asia/Shanghai
to
2026-06-08 00:00:00 Asia/Shanghai
```

Run the fixed-window sampler before the start time and leave it running:

```bash
cd orderly-hyperliquid-case
source .venv/bin/activate
python scripts/collect_spread_window.py
```

Default output:

```text
data/raw/spread_samples_20260605_0000_to_20260608_0000_shanghai.csv
```

For a short dry run before the real window:

```bash
python scripts/collect_spread_window.py \
  --start 2026-06-04T21:30:00 \
  --end 2026-06-04T21:35:00 \
  --output data/raw/spread_samples_dry_run.csv
```

After the final window ends, update `scripts/process_data.py` to read the final raw file or copy the final raw file to the path used by `choose_spread_files()`, then run:

```bash
python scripts/process_data.py
```

Then update:

- `dashboard/app.py` spread window text
- `report/conclusion.md` spread window and spread metrics

## 3. Prepare GitHub Repository

From the project root:

```bash
cd orderly-hyperliquid-case
git init
git add README.md DEPLOYMENT.md requirements.txt dashboard scripts report data/processed
git commit -m "Add Orderly vs Hyperliquid liquidity dashboard"
```

Create a new GitHub repository, then connect and push:

```bash
git remote add origin https://github.com/<your-username>/orderly-hyperliquid-liquidity-dashboard.git
git branch -M main
git push -u origin main
```

Do not commit private keys, local virtual environments, or large temporary sampler files.

## 4. Deploy as a Link

The easiest link-style deployment is Streamlit Community Cloud.

1. Go to Streamlit Community Cloud.
2. Connect your GitHub account.
3. Select the GitHub repository.
4. Set the app file path:

```text
dashboard/app.py
```

5. Deploy.

The public app URL can then be shared as the dashboard link.

## 5. Final Data Refresh Before Submission

After the final Jun 5-8 spread window is collected:

```bash
python scripts/process_data.py
git add data/processed report/conclusion.md dashboard/app.py
git commit -m "Refresh final 72-hour spread window"
git push
```

Streamlit Cloud will redeploy from the latest GitHub commit.
