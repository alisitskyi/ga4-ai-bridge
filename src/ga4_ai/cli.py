#!/usr/bin/env python3
"""
Global Google Analytics 4 (GA4) CLI Tool (ga4)
Enables any AI assistant or developer in VS Code across all projects to:
- Authenticate once globally with multiple account profiles (--profile)
- List all accessible GA4 accounts and properties
- Query custom metrics and dimensions
- Run real-time activity reports
- Run pre-built reports: channels, events, landing pages
- Output in formatted tables, CSV, or JSON for AI processing
"""

import os
import re
import sys
import csv
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/analytics'
]

GA4_DIR = Path.home() / '.ga4'
GA4_CREDS = GA4_DIR / 'credentials.json'
GA4_TOKEN = GA4_DIR / 'token.json'
GDOC_CREDS = Path.home() / '.gdoc' / 'credentials.json'


def find_credentials_file() -> Path:
    """Find credentials.json in ~/.ga4 or fallback to ~/.gdoc or local directory."""
    if GA4_CREDS.exists():
        return GA4_CREDS
    if GDOC_CREDS.exists():
        return GDOC_CREDS
    local_creds = Path.cwd() / '.secrets' / 'credentials.json'
    if local_creds.exists():
        return local_creds
    return GA4_CREDS


def find_token_file(profile: str = "default") -> Path:
    """Find token file for specific profile."""
    if profile and profile != "default":
        return GA4_DIR / f"token_{profile}.json"
    if GA4_TOKEN.exists():
        return GA4_TOKEN
    local_token = Path.cwd() / '.secrets' / 'token.json'
    if local_token.exists():
        return local_token
    return GA4_TOKEN


def find_config_file(profile: str = "default") -> Path:
    """Find config file for specific profile."""
    if profile and profile != "default":
        return GA4_DIR / f"config_{profile}.json"
    return GA4_DIR / "config.json"


def load_config(profile: str = "default") -> Dict[str, Any]:
    """Load configuration for profile."""
    cfg_file = find_config_file(profile)
    if cfg_file.exists():
        try:
            with open(cfg_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(data: Dict[str, Any], profile: str = "default"):
    """Save configuration for profile."""
    GA4_DIR.mkdir(parents=True, exist_ok=True)
    cfg_file = find_config_file(profile)
    with open(cfg_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def clean_property_id(prop: Optional[str], profile: str = "default", require: bool = True) -> str:
    """Ensure property ID has 'properties/' prefix, falling back to config if omitted."""
    if not prop:
        cfg = load_config(profile)
        prop = cfg.get("property_id")
        if not prop and profile != "default":
            def_cfg = load_config("default")
            prop = def_cfg.get("property_id")

    if not prop:
        if require:
            print("[ERROR] Property ID is required (--property <ID> or set default via 'ga4 config --property <ID>')", file=sys.stderr)
            sys.exit(1)
        return ""

    prop = str(prop).strip()
    if prop.startswith("properties/"):
        return prop
    return f"properties/{prop}"


def get_credentials(profile: str = "default") -> Any:
    """Authenticate via OAuth Desktop App or Service Account."""
    GA4_DIR.mkdir(parents=True, exist_ok=True)
    creds_file = find_credentials_file()
    token_file = find_token_file(profile)

    if not creds_file.exists():
        print(f"\n[ERROR] Credentials file not found!", file=sys.stderr)
        print(f"Please save your downloaded Google Cloud OAuth JSON as:\n  {GA4_CREDS}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(creds_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error parsing {creds_file}: {e}", file=sys.stderr)
        sys.exit(1)

    if data.get('type') == 'service_account':
        return service_account.Credentials.from_service_account_file(
            str(creds_file),
            scopes=SCOPES
        )

    creds = None
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print(f"[*] Refreshing expired token (profile: {profile})...", file=sys.stderr)
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            print(f"[*] Launching browser for Google Analytics login (profile: {profile})...", file=sys.stderr)
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, 'w', encoding='utf-8') as f:
            f.write(creds.to_json())
        print(f"[+] GA4 token for profile '{profile}' saved to {token_file}", file=sys.stderr)

    return creds


def get_services(profile: str = "default"):
    """Return GA4 Data API and Admin API clients."""
    creds = get_credentials(profile)
    data_client = build('analyticsdata', 'v1beta', credentials=creds)
    admin_client = build('analyticsadmin', 'v1beta', credentials=creds)
    return data_client, admin_client


def print_table(headers: List[str], rows: List[List[str]], out_json: bool = False, out_csv: bool = False):
    """Format and print tabular data to stdout."""
    if out_json:
        result = [dict(zip(headers, row)) for row in rows]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if out_csv:
        writer = csv.writer(sys.stdout)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        return

    if not rows:
        print("[!] No data returned for this query.", file=sys.stderr)
        return

    widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            widths[idx] = max(widths[idx], len(str(val)))

    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * widths[i] for i in range(len(headers)))
    print(header_line)
    print(separator)
    for row in rows:
        print(" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row)))


# ==================== GA4 COMMANDS ====================

def cmd_properties(args):
    """List all GA4 accounts and properties accessible to the user."""
    prof = getattr(args, 'profile', 'default')
    _, admin = get_services(prof)
    print(f"Fetching accessible Google Analytics accounts (profile: '{prof}')...", file=sys.stderr)

    try:
        accounts_res = admin.accountSummaries().list().execute()
        summaries = accounts_res.get('accountSummaries', [])
    except Exception as e:
        print(f"[!] Error listing account summaries: {e}", file=sys.stderr)
        return

    rows = []
    for acc in summaries:
        acc_name = acc.get('displayName', 'Unknown Account')
        for prop in acc.get('propertySummaries', []):
            prop_id = prop.get('property', '')
            prop_name = prop.get('displayName', 'Unknown Property')
            rows.append([acc_name, prop_name, prop_id])

    headers = ["Account", "Property Name", "Property ID"]
    print_table(headers, rows, args.json, args.csv)


def cmd_config(args):
    prof = getattr(args, 'profile', 'default')
    cfg = load_config(prof)
    updated = False

    if args.property:
        cfg["property_id"] = clean_property_id(args.property, prof, require=False)
        updated = True

    if updated:
        save_config(cfg, prof)
        print(f"[+] GA4 configuration updated for profile '{prof}'!")

    print(f"=== GA4 Config (Profile: '{prof}') ===")
    print(f"Default Property: {cfg.get('property_id', '<NOT SET>')}")


def cmd_query(args):
    """Run a custom report using Google Analytics Data API."""
    prof = getattr(args, 'profile', 'default')
    data_client, _ = get_services(prof)
    property_id = clean_property_id(args.property, prof)

    metrics = [{'name': m.strip()} for m in args.metrics.split(',') if m.strip()]
    dimensions = [{'name': d.strip()} for d in args.dimensions.split(',') if d.strip()] if args.dimensions else []

    if args.start_date and args.end_date:
        date_ranges = [{'startDate': args.start_date, 'endDate': args.end_date}]
    else:
        days = args.days or 30
        date_ranges = [{'startDate': f'{days}daysAgo', 'endDate': 'today'}]

    body = {
        'dateRanges': date_ranges,
        'metrics': metrics,
        'limit': args.limit or 100
    }
    if dimensions:
        body['dimensions'] = dimensions

    res = data_client.properties().runReport(
        property=property_id,
        body=body
    ).execute()

    headers = [d['name'] for d in res.get('dimensionHeaders', [])] + [m['name'] for m in res.get('metricHeaders', [])]
    rows = []
    for row in res.get('rows', []):
        row_vals = [dv.get('value', '') for dv in row.get('dimensionValues', [])] + \
                   [mv.get('value', '') for mv in row.get('metricValues', [])]
        rows.append(row_vals)

    print_table(headers, rows, args.json, args.csv)


def cmd_realtime(args):
    """Run a real-time activity report."""
    prof = getattr(args, 'profile', 'default')
    data_client, _ = get_services(prof)
    property_id = clean_property_id(args.property, prof)

    body = {
        'metrics': [{'name': 'activeUsers'}],
        'dimensions': [{'name': 'country'}, {'name': 'unifiedScreenName'}],
        'limit': args.limit or 25
    }

    res = data_client.properties().runRealtimeReport(
        property=property_id,
        body=body
    ).execute()

    headers = [d['name'] for d in res.get('dimensionHeaders', [])] + [m['name'] for m in res.get('metricHeaders', [])]
    rows = []
    for row in res.get('rows', []):
        row_vals = [dv.get('value', '') for dv in row.get('dimensionValues', [])] + \
                   [mv.get('value', '') for mv in row.get('metricValues', [])]
        rows.append(row_vals)

    print(f"=== GA4 Real-time Report ({property_id}) [Profile: '{prof}'] ===", file=sys.stderr)
    print_table(headers, rows, args.json, args.csv)


def cmd_channels(args):
    """Preset report: Traffic & Conversions by Channel Grouping."""
    prof = getattr(args, 'profile', 'default')
    data_client, _ = get_services(prof)
    property_id = clean_property_id(args.property, prof)
    days = args.days or 30

    body = {
        'dateRanges': [{'startDate': f'{days}daysAgo', 'endDate': 'today'}],
        'dimensions': [{'name': 'sessionDefaultChannelGroup'}],
        'metrics': [
            {'name': 'sessions'},
            {'name': 'activeUsers'},
            {'name': 'conversions'},
            {'name': 'eventCount'}
        ],
        'limit': 50
    }

    res = data_client.properties().runReport(property=property_id, body=body).execute()
    headers = ["Channel Group", "Sessions", "Active Users", "Conversions", "Total Events"]
    rows = []
    for row in res.get('rows', []):
        dim = row['dimensionValues'][0]['value']
        m = [mv['value'] for mv in row['metricValues']]
        rows.append([dim] + m)

    print(f"=== Channel Report (Last {days} days) - {property_id} [Profile: '{prof}'] ===", file=sys.stderr)
    print_table(headers, rows, args.json, args.csv)


def cmd_events(args):
    """Preset report: Top events by volume and users."""
    prof = getattr(args, 'profile', 'default')
    data_client, _ = get_services(prof)
    property_id = clean_property_id(args.property, prof)
    days = args.days or 30

    body = {
        'dateRanges': [{'startDate': f'{days}daysAgo', 'endDate': 'today'}],
        'dimensions': [{'name': 'eventName'}],
        'metrics': [
            {'name': 'eventCount'},
            {'name': 'totalUsers'},
            {'name': 'eventValue'}
        ],
        'limit': args.limit or 50
    }

    res = data_client.properties().runReport(property=property_id, body=body).execute()
    headers = ["Event Name", "Event Count", "Total Users", "Event Value"]
    rows = []
    for row in res.get('rows', []):
        dim = row['dimensionValues'][0]['value']
        m = [mv['value'] for mv in row['metricValues']]
        rows.append([dim] + m)

    print(f"=== Top Events (Last {days} days) - {property_id} [Profile: '{prof}'] ===", file=sys.stderr)
    print_table(headers, rows, args.json, args.csv)


def cmd_landing_pages(args):
    """Preset report: Top landing pages."""
    prof = getattr(args, 'profile', 'default')
    data_client, _ = get_services(prof)
    property_id = clean_property_id(args.property, prof)
    days = args.days or 30

    body = {
        'dateRanges': [{'startDate': f'{days}daysAgo', 'endDate': 'today'}],
        'dimensions': [{'name': 'landingPage'}],
        'metrics': [
            {'name': 'sessions'},
            {'name': 'activeUsers'},
            {'name': 'conversions'}
        ],
        'limit': args.limit or 50
    }

    res = data_client.properties().runReport(property=property_id, body=body).execute()
    headers = ["Landing Page", "Sessions", "Active Users", "Conversions"]
    rows = []
    for row in res.get('rows', []):
        dim = row['dimensionValues'][0]['value']
        m = [mv['value'] for mv in row['metricValues']]
        rows.append([dim] + m)

    print(f"=== Landing Pages (Last {days} days) - {property_id} [Profile: '{prof}'] ===", file=sys.stderr)
    print_table(headers, rows, args.json, args.csv)


def cmd_status(args):
    """Check credentials and token validity for GA4."""
    prof = getattr(args, 'profile', 'default')
    creds_file = find_credentials_file()
    token_file = find_token_file(prof)
    print(f"=== GA4 CLI Status (Profile: '{prof}') ===")
    print(f"Credentials location: {creds_file} (Exists: {creds_file.exists()})")
    print(f"Token location:       {token_file} (Exists: {token_file.exists()})")

    if not creds_file.exists():
        print("[-] Status: Missing credentials.json. Please put it in ~/.ga4/credentials.json")
    elif not token_file.exists():
        print(f"[!] Status: credentials.json present! Run 'ga4 auth --profile {prof}' to authorize.")
    else:
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            if creds and creds.valid:
                print(f"[+] Status: GA4 Authentication is VALID and READY for profile '{prof}'!")
            elif creds and creds.expired and creds.refresh_token:
                print(f"[*] Status: Token for profile '{prof}' expired, will refresh automatically.")
            else:
                print(f"[!] Status: Token invalid, please run 'ga4 auth --profile {prof}'.")
        except Exception as e:
            print(f"[-] Status: Error verifying token: {e}")


def main():
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--profile", default="default", help="Google account profile (e.g. 'work', 'personal')")

    parser = argparse.ArgumentParser(
        prog="ga4",
        description="Global Google Analytics 4 (GA4) CLI for AI assistants and developers.",
        parents=[common_parser]
    )
    sub = parser.add_subparsers(dest="subcommand", help="Command to run")

    # Common
    sub.add_parser("auth", help="Run one-time OAuth authentication for GA4", parents=[common_parser])
    sub.add_parser("status", help="Check GA4 credentials and token status", parents=[common_parser])
    p_cfg = sub.add_parser("config", help="Set or view default GA4 property configuration", parents=[common_parser])
    p_cfg.add_argument("--property", help="Set default GA4 Property ID (e.g. 171288152)")

    # Properties
    p_props = sub.add_parser("properties", help="List all accessible GA4 accounts and Property IDs", parents=[common_parser])
    p_props.add_argument("--json", action="store_true", help="Output JSON")
    p_props.add_argument("--csv", action="store_true", help="Output CSV")

    # Realtime
    p_rt = sub.add_parser("realtime", help="Run real-time activity report", parents=[common_parser])
    p_rt.add_argument("--property", help="GA4 Property ID (e.g. 123456789)")
    p_rt.add_argument("--limit", type=int, default=25, help="Number of rows")
    p_rt.add_argument("--json", action="store_true", help="Output JSON")
    p_rt.add_argument("--csv", action="store_true", help="Output CSV")

    # Query
    p_q = sub.add_parser("query", help="Run custom report (metrics, dimensions)", parents=[common_parser])
    p_q.add_argument("--property", help="GA4 Property ID")
    p_q.add_argument("--metrics", required=True, help="Comma-separated metrics (e.g. 'activeUsers,sessions,conversions')")
    p_q.add_argument("--dimensions", help="Comma-separated dimensions (e.g. 'sessionDefaultChannelGroup,date')")
    p_q.add_argument("--days", type=int, default=30, help="Days back from today (default: 30)")
    p_q.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    p_q.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    p_q.add_argument("--limit", type=int, default=100, help="Max rows")
    p_q.add_argument("--json", action="store_true", help="Output JSON")
    p_q.add_argument("--csv", action="store_true", help="Output CSV")

    # Presets
    p_chan = sub.add_parser("channels", help="Report by Channel Grouping (Sessions, Users, Conversions)", parents=[common_parser])
    p_chan.add_argument("--property", help="GA4 Property ID")
    p_chan.add_argument("--days", type=int, default=30, help="Days back (default: 30)")
    p_chan.add_argument("--json", action="store_true", help="Output JSON")
    p_chan.add_argument("--csv", action="store_true", help="Output CSV")

    p_ev = sub.add_parser("events", help="Report top events (Counts, Users, Value)", parents=[common_parser])
    p_ev.add_argument("--property", help="GA4 Property ID")
    p_ev.add_argument("--days", type=int, default=30, help="Days back (default: 30)")
    p_ev.add_argument("--limit", type=int, default=50, help="Max rows")
    p_ev.add_argument("--json", action="store_true", help="Output JSON")
    p_ev.add_argument("--csv", action="store_true", help="Output CSV")

    p_lp = sub.add_parser("landing-pages", help="Report top landing pages", parents=[common_parser])
    p_lp.add_argument("--property", help="GA4 Property ID")
    p_lp.add_argument("--days", type=int, default=30, help="Days back (default: 30)")
    p_lp.add_argument("--limit", type=int, default=50, help="Max rows")
    p_lp.add_argument("--json", action="store_true", help="Output JSON")
    p_lp.add_argument("--csv", action="store_true", help="Output CSV")

    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        sys.exit(0)

    try:
        prof = getattr(args, 'profile', 'default')
        if args.subcommand == "auth":
            get_credentials(prof)
            print(f"[+] GA4 Authentication successful for profile '{prof}'!")
        elif args.subcommand == "status":
            cmd_status(args)
        elif args.subcommand == "config":
            cmd_config(args)
        elif args.subcommand == "properties":
            cmd_properties(args)
        elif args.subcommand == "query":
            cmd_query(args)
        elif args.subcommand == "realtime":
            cmd_realtime(args)
        elif args.subcommand == "channels":
            cmd_channels(args)
        elif args.subcommand == "events":
            cmd_events(args)
        elif args.subcommand == "landing-pages":
            cmd_landing_pages(args)
    except HttpError as e:
        print(f"[!] Google API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
