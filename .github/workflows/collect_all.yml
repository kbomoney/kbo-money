name: Collect All KBO Players

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  collect:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install requests beautifulsoup4

      - name: Run Collector
        run: python collect_all.py

      - name: Commit and Push changes
        if: always()
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add data/players_all.json
          if git diff --cached --quiet; then
            echo "변경사항 없음"
            exit 0
          fi
          git commit -m "Collect all KBO players ($(date -u '+%Y-%m-%d %H:%M UTC'))"
          git pull --rebase --autostash origin main
          git push origin main
