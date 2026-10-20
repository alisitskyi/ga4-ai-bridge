# Claude Code Guide for Google Analytics 4 (GA4)

You have access to a global command-line utility `ga4` to query Google Analytics 4 data and reports directly from the terminal.

## Core Rules
1. **Never ask for passwords or API keys in chat.** Authentication is managed globally via `ga4 auth` (tokens stored in `~/.ga4/`).
2. **Output formats:** Use `--json` when you need to process or filter data programmatically. Use standard output for terminal tables.

## Quick Reference
- **List accessible accounts & Property IDs:**
  ```bash
  ga4 properties
  ```
- **Traffic and Conversions by Channel:**
  ```bash
  ga4 channels --property <PROPERTY_ID> --days 30
  ```
- **Top Events (counts, users, values):**
  ```bash
  ga4 events --property <PROPERTY_ID> --days 14
  ```
- **Top Landing Pages:**
  ```bash
  ga4 landing-pages --property <PROPERTY_ID> --days 30
  ```
- **Real-time activity (active users right now):**
  ```bash
  ga4 realtime --property <PROPERTY_ID>
  ```
- **Custom Report:**
  ```bash
  ga4 query --property <PROPERTY_ID> --metrics "activeUsers,sessions,conversions" --dimensions "sessionDefaultChannelGroup,date" --days 7 --json
  ```
