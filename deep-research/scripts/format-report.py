#!/usr/bin/env python3
"""
format-report.py — Citation cleanup and report formatting for deep-research.

Usage:
    python scripts/format-report.py research/<topic>/research.md

Features:
    - Renumbers citations sequentially by order of first appearance
    - Deduplicates references (same URL → same number)
    - Strips tracking parameters from URLs (utm_*, fbclid, etc.)
    - Validates that all inline citations have matching references
    - Optionally exports to PDF (requires pandoc)

Flags:
    --check     Validate only, don't modify the file
    --pdf       Export to PDF after formatting (requires pandoc)
    --stdout    Print formatted output instead of overwriting the file
"""

import re
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "gclsrc", "dclid", "msclkid", "mc_cid", "mc_eid",
    "ref", "source", "s", "si",
}


def strip_tracking_params(url: str) -> str:
    """Remove common tracking query parameters from a URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    cleaned = {k: v for k, v in params.items() if k.lower() not in TRACKING_PARAMS}
    clean_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=clean_query))


def parse_references(text: str) -> dict[str, tuple[str, str]]:
    """
    Parse the References section.
    Returns {number_str: (title, url)} for each reference.
    """
    refs = {}
    ref_pattern = re.compile(r"^\[(\d+)\]\s+(.+?)\s*—\s*(https?://\S+)", re.MULTILINE)
    for match in ref_pattern.finditer(text):
        num, title, url = match.group(1), match.group(2).strip(), match.group(3).strip()
        refs[num] = (title, strip_tracking_params(url))
    return refs


def find_inline_citations(text: str) -> list[str]:
    """Find all inline citation numbers like [1], [2], etc."""
    # Exclude references section lines (starting with [N])
    citations = set()
    in_references = False
    for line in text.split("\n"):
        if re.match(r"^##\s+References", line):
            in_references = True
            continue
        if in_references and line.startswith("## "):
            in_references = False
        if not in_references:
            for match in re.finditer(r"\[(\d+)\]", line):
                citations.add(match.group(1))
    return sorted(citations, key=int)


def renumber_citations(text: str) -> str:
    """
    Renumber all citations sequentially by order of first appearance.
    Deduplicates references with the same URL.
    """
    refs = parse_references(text)
    if not refs:
        return text

    # Build URL → first-seen reference number mapping
    url_to_canonical: dict[str, str] = {}
    old_to_new: dict[str, str] = {}
    next_num = 1

    # Find citation order by scanning the body (not references section)
    ref_section_start = text.find("## References")
    body = text[:ref_section_start] if ref_section_start != -1 else text

    seen_order = []
    for match in re.finditer(r"\[(\d+)\]", body):
        num = match.group(1)
        if num not in seen_order and num in refs:
            seen_order.append(num)

    # Assign new numbers, deduplicating by URL
    new_refs: dict[str, tuple[str, str]] = {}
    for old_num in seen_order:
        if old_num not in refs:
            continue
        title, url = refs[old_num]
        if url in url_to_canonical:
            old_to_new[old_num] = url_to_canonical[url]
        else:
            new_num = str(next_num)
            next_num += 1
            url_to_canonical[url] = new_num
            old_to_new[old_num] = new_num
            new_refs[new_num] = (title, url)

    # Replace inline citations in the body
    def replace_citation(match: re.Match) -> str:
        old_num = match.group(1)
        if old_num in old_to_new:
            return f"[{old_to_new[old_num]}]"
        return match.group(0)

    new_body = re.sub(r"\[(\d+)\]", replace_citation, body)

    # Rebuild references section
    ref_lines = ["## References"]
    for num in sorted(new_refs.keys(), key=int):
        title, url = new_refs[num]
        ref_lines.append(f"[{num}] {title} — {url}")

    # Reassemble
    if ref_section_start != -1:
        # Preserve anything after references (unlikely but safe)
        after_refs = text[ref_section_start:]
        # Find the end of references section
        next_section = re.search(r"\n## (?!References)", after_refs)
        tail = after_refs[next_section.start():] if next_section else ""
        result = new_body.rstrip() + "\n\n" + "\n".join(ref_lines) + "\n" + tail
    else:
        result = new_body.rstrip() + "\n\n" + "\n".join(ref_lines) + "\n"

    return result


def validate(text: str) -> list[str]:
    """Check for citation issues. Returns list of warnings."""
    warnings = []
    refs = parse_references(text)
    inline = find_inline_citations(text)

    ref_nums = set(refs.keys())
    inline_nums = set(inline)

    orphan_citations = inline_nums - ref_nums
    unused_refs = ref_nums - inline_nums

    for num in sorted(orphan_citations, key=int):
        warnings.append(f"Citation [{num}] has no matching reference")

    for num in sorted(unused_refs, key=int):
        warnings.append(f"Reference [{num}] is never cited in the text")

    # Check for duplicate URLs
    urls = {}
    for num, (title, url) in refs.items():
        if url in urls:
            warnings.append(
                f"Duplicate URL: [{num}] and [{urls[url]}] point to {url}"
            )
        else:
            urls[url] = num

    return warnings


def export_pdf(md_path: Path) -> Path:
    """Export markdown to PDF using pandoc."""
    if not shutil.which("pandoc"):
        print("Error: pandoc not found. Install it to export PDFs.", file=sys.stderr)
        sys.exit(1)

    pdf_path = md_path.with_suffix(".pdf")
    subprocess.run(
        ["pandoc", str(md_path), "-o", str(pdf_path),
         "--pdf-engine=xelatex", "-V", "geometry:margin=1in"],
        check=True,
    )
    return pdf_path


def main():
    parser = argparse.ArgumentParser(
        description="Format and validate deep-research reports"
    )
    parser.add_argument("file", type=Path, help="Path to research.md")
    parser.add_argument("--check", action="store_true", help="Validate only")
    parser.add_argument("--pdf", action="store_true", help="Export to PDF")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"Error: {args.file} not found", file=sys.stderr)
        sys.exit(1)

    text = args.file.read_text()

    # Validate
    warnings = validate(text)
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}", file=sys.stderr)
        if args.check:
            sys.exit(1 if warnings else 0)

    if args.check:
        print("OK — no issues found")
        sys.exit(0)

    # Format
    formatted = renumber_citations(text)

    if args.stdout:
        print(formatted)
    else:
        args.file.write_text(formatted)
        print(f"Formatted: {args.file}")

    # Re-validate after formatting
    post_warnings = validate(formatted)
    if post_warnings:
        for w in post_warnings:
            print(f"  POST-FORMAT WARNING: {w}", file=sys.stderr)

    # PDF export
    if args.pdf:
        pdf_path = export_pdf(args.file)
        print(f"Exported: {pdf_path}")


if __name__ == "__main__":
    main()
