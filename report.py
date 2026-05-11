#!/usr/bin/env python3
import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation

UUID_PAT    = re.compile(r'^[0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12}$')
ACCOUNT_PAT = re.compile(r'^GIG-USR-\d+$')
TS_NEWLINE  = re.compile(r'(\d{4}-\d{2}-\d{2}T[\d:Z]*)\n([\d:Z]*,)')


def parse_csv(path):
    total, valid_sum = 0, Decimal('0')
    with open(path) as f:
        content = f.read()

    # normalize embedded newlines inside timestamps (mirrors NiFi FixTimestampNewlines)
    content = TS_NEWLINE.sub(r'\1\2', content)

    lines = content.splitlines()
    for line in lines[1:]:  # skip header
        line = line.strip()
        if not line:
            continue
        total += 1
        cols = [c.strip() for c in line.split(',')]
        if len(cols) < 6:
            continue
        tid, aid, amount, _, _, status = cols[:6]
        if not UUID_PAT.match(tid):    continue
        if not ACCOUNT_PAT.match(aid): continue
        try:
            amt = Decimal(amount)
        except InvalidOperation:
            continue
        if status != 'SUCCESS': continue
        valid_sum += amt
    return total, valid_sum


def psql(sql):
    container = subprocess.run(
        ['docker', 'compose', 'ps', '-q', 'postgres'],
        capture_output=True, text=True
    ).stdout.strip()
    out = subprocess.run(
        ['docker', 'exec', container, 'psql', '-U', 'gig', '-d', 'gigdb', '-tAc', sql],
        capture_output=True, text=True
    )
    return out.stdout.strip()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 report.py <source.csv>")
        sys.exit(1)

    source_total, source_sum = parse_csv(sys.argv[1])

    db_count = int(psql("SELECT COUNT(*) FROM transactions;"))
    db_sum   = Decimal(psql("SELECT COALESCE(SUM(amount), 0) FROM transactions;"))
    skipped  = source_total - db_count

    W = 34
    print()
    print("=" * W)
    print("        MIGRATION REPORT")
    print("=" * W)
    print(f"{'Total Source Records:':<26} {source_total}")
    print(f"{'Total Successfully Migrated:':<26} {db_count}")
    print(f"{'Total Failed/Skipped:':<26} {skipped}")
    print("-" * W)
    print(f"{'Source Financial Value:':<26} {source_sum:.4f}")
    print(f"{'Migrated Financial Value:':<26} {db_sum:.4f}")
    print("=" * W)


if __name__ == '__main__':
    main()
