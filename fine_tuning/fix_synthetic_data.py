"""
Fix known issues in synthetic_data_formatted.jsonl

Issues to fix:
A. CURRENT_DATE misuse -> MAX(date) subquery
B. stock_grade JOIN without date filter
C. Invalid market_index exchange values (S&P 500, DOW JONES, RUSSELL 2000, KOSPI200)
D. Invalid final_grade values ('A+', 'A', 'B+' -> Korean grades)
E. volume aliased as trading_value for US queries
F. avg_trading_value_5d semantic mismatch
"""
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
INPUT_FILE = DATA_DIR / "synthetic_data_formatted.jsonl"
OUTPUT_FILE = DATA_DIR / "synthetic_data_formatted.jsonl"
BACKUP_FILE = DATA_DIR / "synthetic_data_formatted.jsonl.bak"


def fix_sql(sql: str) -> str:
    """Apply all fixes to a SQL string."""
    original = sql

    # =================================================================
    # A. CURRENT_DATE -> MAX(date) subquery
    # =================================================================

    # kr_indicators: "AND i.date = CURRENT_DATE" or "WHERE i.date = CURRENT_DATE"
    sql = re.sub(
        r'(?<!\w)i\.date\s*=\s*CURRENT_DATE(?!\s*[-+])',
        'i.date = (SELECT MAX(date) FROM kr_indicators)',
        sql
    )

    # kr_individual_investor_daily_trading: "t.date = CURRENT_DATE"
    sql = re.sub(
        r'(?<!\w)t\.date\s*=\s*CURRENT_DATE(?!\s*[-+])',
        't.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading)',
        sql
    )

    # kr_individual_investor_daily_trading with alias: "kidt.date = CURRENT_DATE"
    sql = re.sub(
        r'(?<!\w)kidt\.date\s*=\s*CURRENT_DATE(?!\s*[-+])',
        'kidt.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading)',
        sql
    )

    # kr_individual_investor_daily_trading: "t.date >= CURRENT_DATE - INTERVAL"
    sql = re.sub(
        r'(?<!\w)t\.date\s*>=\s*CURRENT_DATE\s*-\s*INTERVAL',
        't.date >= (SELECT MAX(date) FROM kr_individual_investor_daily_trading) - INTERVAL',
        sql
    )

    # kr_intraday_total: "date = CURRENT_DATE - INTERVAL '1 day'"
    sql = re.sub(
        r'(?<!\w)date\s*=\s*CURRENT_DATE\s*-\s*INTERVAL\s*\'1 day\'',
        'date = (SELECT MAX(date) FROM kr_intraday_total)',
        sql
    )

    # kr_intraday_total: "date >= CURRENT_DATE - INTERVAL 'N days'"
    sql = re.sub(
        r'(?<!\w)date\s*>=\s*CURRENT_DATE\s*-\s*INTERVAL\s*\'(\d+)\s*days?\'',
        r"date >= (SELECT MAX(date) FROM kr_intraday_total) - INTERVAL '\1 days'",
        sql
    )

    # kr_intraday_total: "date >= DATE_TRUNC('week', CURRENT_DATE)"
    sql = re.sub(
        r"date\s*>=\s*DATE_TRUNC\('week',\s*CURRENT_DATE\)",
        "date >= DATE_TRUNC('week', (SELECT MAX(date) FROM kr_intraday_total))",
        sql
    )

    # kr_indicators: "i.date >= CURRENT_DATE - INTERVAL"
    sql = re.sub(
        r'(?<!\w)i\.date\s*>=\s*CURRENT_DATE\s*-\s*INTERVAL',
        'i.date >= (SELECT MAX(date) FROM kr_indicators) - INTERVAL',
        sql
    )

    # Generic standalone date = CURRENT_DATE (for CTE context with kr_intraday_total)
    # Only match when it looks like "vc.date = CURRENT_DATE" or similar CTE alias
    sql = re.sub(
        r'(?<!\w)vc\.date\s*=\s*CURRENT_DATE',
        'vc.date = (SELECT MAX(date) FROM kr_intraday_total)',
        sql
    )

    # =================================================================
    # B. stock_grade JOIN without date filter
    # =================================================================

    # kr_stock_grade: JOIN ... ON k.symbol = g.symbol (without date)
    # Match pattern: "JOIN kr_stock_grade g ON <alias>.symbol = g.symbol" without existing date filter
    sql = re.sub(
        r'JOIN\s+kr_stock_grade\s+(\w+)\s+ON\s+(\w+)\.symbol\s*=\s*\1\.symbol(?!\s+AND\s+\1\.date)',
        r'JOIN kr_stock_grade \1 ON \2.symbol = \1.symbol AND \1.date = (SELECT MAX(date) FROM kr_stock_grade)',
        sql
    )

    # us_stock_grade: JOIN ... ON d.symbol = g.symbol (without date)
    sql = re.sub(
        r'JOIN\s+us_stock_grade\s+(\w+)\s+ON\s+(\w+)\.symbol\s*=\s*\1\.symbol(?!\s+AND\s+\1\.date)',
        r'JOIN us_stock_grade \1 ON \2.symbol = \1.symbol AND \1.date = (SELECT MAX(date) FROM us_stock_grade)',
        sql
    )

    # kr_stock_grade without JOIN (FROM kr_stock_grade WHERE ... without date)
    # Pattern: "FROM kr_stock_grade" ... "WHERE" ... without "date ="
    # This is harder to regex safely, skip for now

    # =================================================================
    # C. Invalid market_index exchange values
    # =================================================================
    sql = sql.replace("exchange = 'KOSPI200'", "exchange = 'KOSPI'")
    sql = sql.replace("exchange = 'S&P 500'", "exchange = 'NYSE'")
    sql = sql.replace("exchange = 'DOW JONES'", "exchange = 'NYSE'")
    sql = sql.replace("exchange = 'RUSSELL 2000'", "exchange = 'NYSE'")

    # =================================================================
    # D. Invalid final_grade values
    # =================================================================
    sql = sql.replace("final_grade IN ('A+', 'A', 'B+')", "final_grade IN ('강력 매수', '매수', '매수 고려')")
    sql = sql.replace("final_grade IN ('A+', 'A')", "final_grade IN ('강력 매수', '매수')")
    sql = sql.replace("final_grade = 'A+'", "final_grade = '강력 매수'")

    # =================================================================
    # E. US volume aliased as trading_value
    # =================================================================
    sql = re.sub(
        r'd\.volume\s+as\s+trading_value',
        'd.trading_value',
        sql,
        flags=re.IGNORECASE
    )

    # Also fix ORDER BY d.volume when it should be d.trading_value
    # (only when trading_value alias was used - tricky to detect, skip for safety)

    # =================================================================
    # F. ::text cast on DATE comparison
    # =================================================================
    sql = re.sub(
        r'\(CURRENT_DATE\s*-\s*INTERVAL\s*\'(\d+)\s*days?\'\)::text',
        r"(SELECT MAX(stlm_dt) FROM kr_executive) - INTERVAL '\1 days'",
        sql
    )

    return sql


def process_file(input_path: Path, output_path: Path):
    """Process JSONL file, fixing SQL in assistant messages."""
    lines = input_path.read_text(encoding='utf-8').strip().split('\n')
    fixed_lines = []
    fix_count = 0

    for i, line in enumerate(lines, 1):
        if not line.strip():
            fixed_lines.append(line)
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print(f"  WARNING: Invalid JSON on line {i}, skipping")
            fixed_lines.append(line)
            continue

        messages = record.get('messages', [])
        modified = False

        for msg in messages:
            if msg.get('role') == 'assistant':
                original_sql = msg['content']
                fixed_sql = fix_sql(original_sql)
                if fixed_sql != original_sql:
                    msg['content'] = fixed_sql
                    modified = True

        if modified:
            fix_count += 1

        fixed_lines.append(json.dumps(record, ensure_ascii=False))

    output_path.write_text('\n'.join(fixed_lines) + '\n', encoding='utf-8')
    return len(lines), fix_count


def main():
    print("=" * 60)
    print("Fixing synthetic_data_formatted.jsonl")
    print("=" * 60)

    # Backup original
    if INPUT_FILE.exists():
        import shutil
        shutil.copy2(INPUT_FILE, BACKUP_FILE)
        print(f"Backup created: {BACKUP_FILE}")

    total, fixed = process_file(INPUT_FILE, OUTPUT_FILE)
    print(f"Total lines: {total}")
    print(f"Lines with fixes: {fixed}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
