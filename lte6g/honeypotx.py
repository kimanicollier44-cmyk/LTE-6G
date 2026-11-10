"""HoneypotX -- honeyroot-x style LOG ANALYSIS ONLY, for the converter.

Darion's honeyroot-x honeypot (270 pulls on Docker Hub) reached this
lab through his PHP-Vuln-RE implementation: a classifier engine over
recorded trap logs. HoneypotX keeps that engine's shape - class
weights, regex classifiers, burst bonus, bait sessions - and points
it at the doors a converter actually has: probes for the eNodeB /
MME management pages, converter configs, credential files, and
firmware-upload attempts.

There is deliberately NO listener code of any kind in this module:
``listener_open`` is always False, nothing binds, nothing serves,
and bait sessions are recorded but never grant access. IPs are from
TEST-NET-3 (198.51.100.0/24), the documentation-only range, and every
entry is synthetic.

Opening a live honeypot listener is HOLD gate
``live_honeypot_listener``.
"""
from __future__ import annotations

import re
from collections import Counter

_CLASS_WEIGHT = {"sqli_probe": 70, "lfi_probe": 75, "env_harvest": 60,
                 "upload_attempt": 90, "scanner": 35}

# Synthetic recorded trap log: time is minutes into the capture window.
LOG_ENTRIES = [
    {"ip": "198.51.100.23", "minute": 1, "method": "GET", "path": "/enb-login", "query": "", "agent": "Mozilla/5.0"},
    {"ip": "198.51.100.23", "minute": 2, "method": "GET", "path": "/.env", "query": "", "agent": "curl/8"},
    {"ip": "198.51.100.23", "minute": 3, "method": "GET", "path": "/.git/config", "query": "", "agent": "curl/8"},
    {"ip": "198.51.100.23", "minute": 4, "method": "GET", "path": "/mme/config.php", "query": "", "agent": "curl/8"},
    {"ip": "198.51.100.23", "minute": 5, "method": "POST", "path": "/firmware/upload.php", "query": "", "agent": "python-requests", "filename": "radio.bin"},
    {"ip": "198.51.100.41", "minute": 6, "method": "GET", "path": "/convert", "query": "file=../../../../etc/passwd", "agent": "Nikto"},
    {"ip": "198.51.100.41", "minute": 7, "method": "GET", "path": "/status", "query": "id=1 UNION SELECT username,password FROM users", "agent": "sqlmap"},
    {"ip": "198.51.100.41", "minute": 8, "method": "GET", "path": "/status", "query": "id=1' OR 1=1--", "agent": "sqlmap"},
    {"ip": "198.51.100.57", "minute": 9, "method": "GET", "path": "/phpmyadmin/", "query": "", "agent": "Mozilla/5.0"},
    {"ip": "198.51.100.57", "minute": 10, "method": "GET", "path": "/admin/", "query": "", "agent": "zgrab"},
    {"ip": "198.51.100.57", "minute": 11, "method": "GET", "path": "/convert", "query": "file=....//....//etc/passwd", "agent": "Nikto"},
    {"ip": "198.51.100.99", "minute": 12, "method": "GET", "path": "/", "query": "", "agent": "Mozilla/5.0"},
]

_SQLI = re.compile(r"(union\s+select|'\s*or\s+1\s*=\s*1|or\s+1=1|sleep\s*\(|benchmark\s*\()", re.I)
_TRAVERSAL = re.compile(r"(\.\./|\.\.\\|%2e%2e|\.\.\.\.//)", re.I)
_ENV_PATHS = ("/.env", "wp-config", "/.git/", "/config.php", "/.aws")
_ADMIN_PATHS = ("/phpmyadmin", "/wp-login", "/admin", "/phpinfo", "/enb-login", "/mme/")


def classify_attempt(entry: dict) -> str:
    path = entry.get("path", "")
    query = entry.get("query", "")
    target = f"{path}?{query}"
    if entry.get("filename") or path.rstrip("/").endswith("upload.php") or "upload" in path:
        return "upload_attempt"
    if _TRAVERSAL.search(target):
        return "lfi_probe"
    if _SQLI.search(query):
        return "sqli_probe"
    if any(p in path for p in _ENV_PATHS):
        return "env_harvest"
    return "scanner"


def threat_score(entry: dict, cls: str = None) -> int:
    cls = cls or classify_attempt(entry)
    score = _CLASS_WEIGHT[cls]
    if entry.get("agent", "").lower() in ("sqlmap", "nikto", "zgrab"):
        score += 5
    return min(100, score)


def _bursts(entries) -> list:
    counts = Counter(e["ip"] for e in entries)
    return [{"ip": ip, "attempts": n} for ip, n in sorted(counts.items()) if n >= 4]


def honeypotx_summary(entries=None) -> dict:
    entries = list(entries if entries is not None else LOG_ENTRIES)
    classified = []
    for e in entries:
        cls = classify_attempt(e)
        classified.append({**e, "class": cls, "threat_score": threat_score(e, cls),
                           "bait": any(p in e["path"] for p in _ENV_PATHS + _ADMIN_PATHS)})
    bursts = _bursts(entries)
    burst_ips = {b["ip"] for b in bursts}
    for c in classified:  # burst bonus, applied after burst detection
        if c["ip"] in burst_ips:
            c["threat_score"] = min(100, c["threat_score"] + 10)
    top = max(classified, key=lambda c: c["threat_score"]) if classified else None
    return {
        "name": "HoneypotX",
        "mode": "log-analysis-only",
        "listener_open": False,
        "attempts": len(classified),
        "entries": classified,
        "by_class": dict(Counter(c["class"] for c in classified)),
        "top_threat_score": top["threat_score"] if top else 0,
        "top_attempt": top,
        "bursts": bursts,
        "bait_sessions": [
            {"session_id": f"bait-{i:02d}", "ip": c["ip"], "path": c["path"],
             "recorded": True, "access_granted": False}
            for i, c in enumerate(classified) if c["bait"]
        ],
        "access_granted": False,
    }
