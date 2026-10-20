# ga4-ai-bridge 📈

> **Universal Google Analytics 4 (GA4) CLI for AI Coding Assistants**  
> Enables Claude Code, Cursor, Cline, Roo Code, and developers to query website analytics, conversion funnels, channels, and real-time data directly from any terminal or project workspace.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![GA4 Data API: Ready](https://img.shields.io/badge/GA4%20Data%20API-v1beta-green.svg)](https://developers.google.com/analytics/devguides/reporting/data/v1)

---

## 💡 Why This Exists

Marketing and product engineers frequently need to cross-reference code changes, tag setups, and campaigns with live analytics. Switching between VS Code and the GA4 web console is slow and cumbersome.

With `ga4-ai-bridge`:
- 🤖 **Empower AI Assistants:** Your coding assistant (Claude, Cursor, Cline) can autonomously query conversion stats, verify that newly deployed GTM events are firing, and detect marketing attribution anomalies.
- ⚡ **Global CLI (`ga4`):** Run reports from any terminal in formatted ASCII tables, CSV, or structured JSON.
- 🔑 **Zero-Friction Authentication:** Reuses your existing Google Cloud credentials from `~/.gdoc/` or standard OAuth 2.0 flow.

---

## 🚀 Quickstart

### 1. Installation

**Windows (PowerShell):**
```powershell
git clone https://github.com/alisitskyi/ga4-ai-bridge.git
cd ga4-ai-bridge
.\install.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/alisitskyi/ga4-ai-bridge.git
cd ga4-ai-bridge
chmod +x install.sh
./install.sh
```

**Or via pip:**
```bash
pip install -e .
```

---

### 2. Enable Google Analytics Data API (1 click)

In your Google Cloud project (e.g. `ai-editor-al`):
1. Open 👉 [Enable Google Analytics Data API](https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com) $\rightarrow$ click **Enable**.
2. Open 👉 [Enable Google Analytics Admin API](https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com) $\rightarrow$ click **Enable**.

---

### 3. Authenticate (One-time)

Run in your terminal:
```powershell
ga4 auth
```
*(Confirms access via browser; token is saved to `~/.ga4/token.json`).*

---

## 📖 CLI Usage Reference

### 1. Discover Accounts and Properties
List all GA4 properties accessible to your account along with their 9-digit Property IDs:
```bash
ga4 properties
```

### 2. Channels Report (Preset)
Breakdown by `sessionDefaultChannelGroup` with Sessions, Active Users, Conversions, and Total Events:
```bash
ga4 channels --property <PROPERTY_ID>
ga4 channels --property <PROPERTY_ID> --days 14
ga4 channels --property <PROPERTY_ID> --json
```

### 3. Events Report (Preset)
Top events by count, active users, and event value:
```bash
ga4 events --property <PROPERTY_ID> --days 7
```

### 4. Top Landing Pages
Inspect the best-performing entry pages:
```bash
ga4 landing-pages --property <PROPERTY_ID> --days 30
```

### 5. Real-Time Activity
See active users right now by country and screen name:
```bash
ga4 realtime --property <PROPERTY_ID>
```

### 6. Custom Reports (`query`)
Query any metrics and dimensions supported by GA4 Data API:
```bash
# Example: Traffic by country and device
ga4 query --property <PROPERTY_ID> \
  --metrics "activeUsers,sessions,conversions" \
  --dimensions "country,deviceCategory" \
  --days 30

# Example: Daily breakdown with custom date range
ga4 query --property <PROPERTY_ID> \
  --metrics "conversions,eventCount" \
  --dimensions "date" \
  --start-date 2026-10-01 \
  --end-date 2026-10-15 \
  --json
```

---

## 🤖 Connecting to AI Assistants

### Claude Code
Add to your project's `.claude/settings.json`:
```json
{
  "allowedTools": [
    "Bash(ga4 *)",
    "PowerShell(ga4 *)"
  ]
}
```

### Cursor IDE
Copy [`templates/.cursorrules`](templates/.cursorrules) to your project root.

### Cline / Roo Code
Copy [`templates/.clinerules`](templates/.clinerules) to your project root.

---

## 📄 License

MIT License. Free to use and distribute. See [LICENSE](LICENSE) for details.
