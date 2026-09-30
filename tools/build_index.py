#!/usr/bin/env python3
"""Rebuilds <variant>/index.json from <variant>/stories/*.json.

Usage: python3 tools/build_index.py survival [lessons ...]

- Only stories with "status": "published" are listed (drafts/archived are not).
- catalogVersion increases on every change so apps can tell something moved.
- Global (catalogue-wide) achievements come from <variant>/achievements.json.
- Upcoming-story teasers come from <variant>/coming_soon.json ({"comingSoon": [...]}).
Validate stories first:  (cd ~/cyoa && dart run tool/validate_story.dart <dir>)
"""
import json, sys, datetime, pathlib

root = pathlib.Path(__file__).resolve().parent.parent

def build(variant: str) -> None:
    d = root / variant
    idx_path = d / "index.json"
    old = json.loads(idx_path.read_text()) if idx_path.exists() else {}
    entries = []
    for f in sorted((d / "stories").glob("*.json")):
        s = json.loads(f.read_text())
        if s.get("status", "published") != "published":
            continue
        entries.append({
            "id": s["id"],
            "version": s.get("version", 1),
            "path": f"stories/{f.name}",
            "title": s["title"],
            "audience": s.get("audience", "general"),
            **({"publishedAt": s["publishedAt"]} if s.get("publishedAt") else {}),
        })
    ach_path = d / "achievements.json"
    globals_ = json.loads(ach_path.read_text())["globalAchievements"] if ach_path.exists() else []
    cs_path = d / "coming_soon.json"
    coming = json.loads(cs_path.read_text())["comingSoon"] if cs_path.exists() else []
    body = {"globalAchievements": globals_, "comingSoon": coming, "stories": entries}
    old_body = {k: old.get(k) for k in ("globalAchievements", "comingSoon", "stories")}
    version = old.get("catalogVersion", 0) + (0 if body == old_body else 1)
    index = {
        "schemaVersion": 1,
        "catalogVersion": version,
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
        if body != old_body else old.get("updatedAt"),
        **body,
    }
    idx_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(f"{variant}: catalogVersion {version}, {len(entries)} stories: " + ", ".join(e["id"] for e in entries))

for v in sys.argv[1:] or ["survival", "lessons"]:
    build(v)
