"""
Simple college data enrichment script for the `college_chatbot` project.

Features:
- Load existing `data/colleges.json` if present.
- Accept a small input file with college website URLs to fetch and parse basic metadata (title, description, contact info if available).
- Respect robots.txt (basic check), rate-limit requests, set a polite User-Agent.
- Output enriched JSON and optional CSV.

Usage:
  python scripts/collect_colleges.py --urls urls.txt --out enriched.json --csv enriched.csv

Note: This script is intentionally conservative and meant for small-scale enrichment only. For large-scale collection use proper data sources and follow the websites' terms of service.
"""

import argparse
import json
import csv
import time
import re
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

USER_AGENT = "EduGuideBot/1.0 (+https://example.com)"
HEADERS = {"User-Agent": USER_AGENT}


def can_fetch(url):
    """Basic robots.txt check for the given host. Returns True if allowed or robots not found."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        r = requests.get(robots_url, headers=HEADERS, timeout=6)
        if r.status_code != 200:
            return True
        text = r.text
        # naive check: look for Disallow: / or Disallow: <path>
        # This is not a full robots parser but is conservative.
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        user_agent = None
        disallows = []
        for line in lines:
            if line.lower().startswith('user-agent'):
                user_agent = line.split(':', 1)[1].strip()
            if line.lower().startswith('disallow'):
                path = line.split(':', 1)[1].strip()
                disallows.append(path)
        # If '/' is disallowed for all user agents, block.
        if '/' in disallows:
            return False
    except Exception:
        return True
    return True


def fetch_meta(url):
    """Fetch page and extract title, meta description, and possible contact info."""
    out = {"url": url}
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            out['error'] = f"HTTP {r.status_code}"
            return out
        soup = BeautifulSoup(r.text, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else ''
        desc = ''
        dtag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
        if dtag and dtag.get('content'):
            desc = dtag['content'].strip()
        out.update({'title': title, 'description': desc})

        # try to find obvious contact/email/phone patterns
        text = soup.get_text(separator=' ', strip=True)
        # email
        m = re.search(r'[\w\.-]+@[\w\.-]+\.[A-Za-z]{2,6}', text)
        if m:
            out['email'] = m.group(0)
        # phone: loose pattern for Indian phone numbers
        m2 = re.search(r'\+?\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{6,8}', text)
        if m2:
            out['phone'] = m2.group(0)

        # try to find address-like segments (simple heuristic)
        addr = ''
        address_candidates = soup.select('address')
        if address_candidates:
            addr = ' '.join([a.get_text(' ', strip=True) for a in address_candidates])
            out['address'] = addr

        return out
    except Exception as e:
        out['error'] = str(e)
        return out


def load_existing(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_csv(data, path):
    # flatten basic fields
    keys = ['name', 'city', 'state', 'website', 'email', 'phone']
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(keys)
        for d in data:
            row = [d.get(k, '') for k in keys]
            w.writerow(row)


def enrich(existing, url_file=None, out_json='enriched.json', out_csv=None, delay=1.2, limit=None):
    out = existing.copy()
    urls = []
    if url_file:
        with open(url_file, 'r', encoding='utf-8') as f:
            for line in f:
                u = line.strip()
                if u:
                    urls.append(u)
    # Optionally limit
    if limit:
        urls = urls[:limit]

    for i, url in enumerate(urls, start=1):
        print(f"[{i}/{len(urls)}] Checking {url} ...")
        if not can_fetch(url):
            print(f"  Skipping {url} due to robots.txt")
            continue
        meta = fetch_meta(url)
        # try to merge with existing by website or name
        matched = None
        for e in out:
            if e.get('website') and e.get('website').rstrip('/') == url.rstrip('/'):
                matched = e
                break
        if matched:
            matched.update(meta)
            print(f"  Merged into existing entry: {matched.get('name','(unknown)')}")
        else:
            out.append(meta)
            print("  Added new entry")
        time.sleep(delay)

    save_json(out, out_json)
    if out_csv:
        save_csv(out, out_csv)
    print(f"Saved enriched data to {out_json}{' and '+out_csv if out_csv else ''}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--urls', help='file with one college website URL per line')
    p.add_argument('--existing', default='data/colleges.json', help='existing JSON file to load')
    p.add_argument('--out', default='data/colleges_enriched.json', help='output JSON path')
    p.add_argument('--csv', help='optional CSV output path')
    p.add_argument('--delay', type=float, default=1.2, help='seconds between requests')
    p.add_argument('--limit', type=int, help='limit number of URLs to process')
    args = p.parse_args()

    existing = load_existing(args.existing)
    enrich(existing, url_file=args.urls, out_json=args.out, out_csv=args.csv, delay=args.delay, limit=args.limit)


if __name__ == '__main__':
    main()

https://www.hinducollege.ac.in/
https://www.mirandahouse.ac.in/
https://www.hansrajcollege.ac.in/
