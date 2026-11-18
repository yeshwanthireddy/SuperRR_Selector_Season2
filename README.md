# THE PRESSURE ROOM — Selector Edition

Streamlit dashboard for SupeRR Selector Season 2. Historical V4 pressure rankings plus phase batting strike rates and bowling economy. Rankings are provisional and do not establish auction eligibility.

## Local launch (from this extracted folder)

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository (public for Community Cloud) and upload **the contents of this folder** to its root, including `app.py`, `requirements.txt`, `.streamlit/config.toml`, and `results/`. Do not upload the original large ball-by-ball dataset; the app uses the included aggregated CSVs.
2. Go to https://share.streamlit.io/ and choose **Create app** (or **New app**) from your GitHub repository.
3. Choose the repository, branch `main`, and main file path `app.py`. Deploy.
4. Test Leaderboard, Player Profiles, The Duel, Selection Board and Methodology in IPL, T20I, and All supplied matches.
5. Copy the public `*.streamlit.app` URL into the competition submission's dashboard-link field.

## Notes

- The `results/` folder must remain next to `app.py` on GitHub.
- The phase statistics are derived from supplied deliveries and have not been independently reconciled to official scorecards.
- IPL-only ranking and all-format phase evidence are distinct measures; do not describe all-format phase diagnostics as IPL-only.
- The bootstrap lower score is a conservative stability diagnostic, not a probability of winning.
- Historical pressure ranking is not the same as auction availability or price.
