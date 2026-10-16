"""Reject missing/empty/all-skipped reports and strip payloads before upload."""

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def inspect_report(path, sanitize=False):
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, UnicodeError):
        if sanitize:
            path.write_text(
                '<testsuite errors="1"><error message="Invalid report; raw contents withheld"/></testsuite>\n'
            )
        raise ValueError("Malformed test report") from None
    cases = list(root.iter("testcase"))
    skipped = sum(case.find("skipped") is not None for case in cases)
    failed = sum(
        case.find("failure") is not None or case.find("error") is not None
        for case in cases
    )
    if sanitize:
        clean = ET.Element(
            "testsuite",
            tests=str(len(cases)),
            failures=str(failed),
            skipped=str(skipped),
        )
        for case in cases:
            result = ET.SubElement(
                clean,
                "testcase",
                {
                    k: case.attrib[k]
                    for k in ("name", "classname", "time")
                    if k in case.attrib
                },
            )
            for kind in ("failure", "error", "skipped"):
                if case.find(kind) is not None:
                    ET.SubElement(
                        result,
                        kind,
                        message="Details omitted from shared artifact; inspect CI test step",
                    )
        ET.indent(clean)
        ET.ElementTree(clean).write(path, encoding="unicode")
        with path.open("a") as stream:
            stream.write("\n")
    if (
        not cases
        or skipped == len(cases)
        or failed
        or any(int(s.attrib.get("errors", "0")) for s in root.iter("testsuite"))
    ):
        raise ValueError("Required suite failed or was entirely skipped")
    return len(cases) - skipped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--sanitize", action="store_true")
    args = parser.parse_args()
    for path in args.reports:
        count = inspect_report(path, args.sanitize)
        print(f"PASS: {path.name}: {count} tests executed")


if __name__ == "__main__":
    main()
