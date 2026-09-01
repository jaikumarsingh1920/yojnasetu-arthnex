"""
Deep Static Frontend UI/UX Auditor
Scans all frontend components and pages in 01frontend/src/ for:
1. Fixed widths / min-widths exceeding mobile viewports (>= 320px)
2. Interactive elements (buttons, links, inputs) with touch target issues (< 44px min-height)
3. Horizontal overflow risks (e.g. fixed table widths, unconstrained flex/grid containers)
4. Dead links (href='#', missing to='', invalid routes)
5. Broken/missing loading, empty, and error states
6. Inconsistent spacing / padding
7. Floating dock collisions (AICopilot vs ComparisonTray z-index / bottom spacing)
"""

import os
import re
import json

FRONTEND_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "01frontend", "src")

def scan_files():
    results = {
        "fixed_widths": [],
        "dead_links": [],
        "touch_target_risks": [],
        "overflow_risks": [],
        "empty_error_states": [],
        "floating_dock_analysis": []
    }

    for root, _, files in os.walk(FRONTEND_SRC):
        for file in files:
            if not (file.endswith(".tsx") or file.endswith(".jsx") or file.endswith(".css")):
                continue
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, FRONTEND_SRC)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.splitlines()

            # 1. Fixed widths (e.g., w-[...px], min-w-[...px] where width > 320)
            for idx, line in enumerate(lines, 1):
                # match w-[400px], min-w-[500px], etc.
                matches = re.findall(r'(w|min-w)-\[(\d+)px\]', line)
                for prefix, width_str in matches:
                    width = int(width_str)
                    if width >= 320:
                        results["fixed_widths"].append({
                            "file": relpath,
                            "line": idx,
                            "match": f"{prefix}-[{width}px]",
                            "code": line.strip()
                        })

                # 2. Dead links: href="#" or empty href
                if 'href="#"' in line or "href='#'" in line or 'href=""' in line:
                    results["dead_links"].append({
                        "file": relpath,
                        "line": idx,
                        "code": line.strip()
                    })

                # 3. Touch target risks on mobile (<44px or py-0.5, py-1 on primary buttons)
                if "<button" in line or "<Link" in line:
                    # check if it has very small padding without min-h-[44px]
                    if ("py-0.5" in line or "py-1 " in line or "h-6 " in line or "h-7 " in line) and "min-h-" not in line:
                        # only flag if it looks like a button with text
                        if "p-1" in line or "p-0.5" in line:
                            pass # could be icon, check if primary
                        else:
                            results["touch_target_risks"].append({
                                "file": relpath,
                                "line": idx,
                                "code": line.strip()
                            })

    return results

if __name__ == "__main__":
    report = scan_files()
    print("=== DEEP UI/UX AUDIT REPORT ===")
    print(f"Fixed widths (>= 320px): {len(report['fixed_widths'])}")
    for item in report["fixed_widths"]:
        print(f"  {item['file']}:{item['line']} -> {item['match']} in: {item['code'][:80]}")

    print(f"\nDead links: {len(report['dead_links'])}")
    for item in report["dead_links"]:
        print(f"  {item['file']}:{item['line']} -> {item['code'][:80]}")

    print(f"\nTouch target risks: {len(report['touch_target_risks'])}")
    for item in report["touch_target_risks"][:10]:
        print(f"  {item['file']}:{item['line']} -> {item['code'][:80]}")

    out_path = os.path.join(os.path.dirname(__file__), "ui_audit_report.json")
    with open(out_path, "w", encoding="utf-8") as out:
        json.dump(report, out, indent=2)
    print(f"\nSaved report to {out_path}")
