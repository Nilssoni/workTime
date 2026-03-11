import argparse
from datetime import date, timedelta
from utils import calc_work_duration, td_to_hours, parse_date, start_of_week, end_of_week, iso_week_key
import storage

def cmd_add(args):
    # Defaults
    lunch = 30 if args.lunch is None else args.lunch
    d = parse_date(args.date) if args.date else date.today()
    worked = calc_work_duration(args.start, args.end, lunch_minutes=lunch)
    worked_minutes = int(worked.total_seconds() // 60)

    entry_id = storage.add_entry(
        work_date=d.isoformat(),
        start_time=args.start,
        end_time=args.end,
        lunch_minutes=lunch,
        worked_minutes=worked_minutes
    )
    print(f"Added entry #{entry_id} for {d.isoformat()}: {args.start}-{args.end}, lunch {lunch} min → {td_to_hours(worked)} h")

    
def cmd_day(args):
    d = parse_date(args.date) if args.date else date.today()
    entries = storage.list_entries_by_date(d.isoformat())
    if not entries:
        print(f"No entries for {d.isoformat()}")
        return
    total = 0
    print(f"Entries for {d.isoformat()}:")
    for e in entries:
        h = round(e["worked_minutes"] / 60.0, 2)
        total += e["worked_minutes"]
        print(f"  #{e['id']}: {e['start_time']} - {e['end_time']} (lunch {e['lunch_minutes']} min) → {h} h")
    print(f"Total: {round(total/60.0, 2)} h")

def cmd_week(args):
    # Accept either a date to find its week, or explicit start/end
    if args.date:
        d = parse_date(args.date)
        s = start_of_week(d)
        e = end_of_week(d)
    else:
        # default: current week
        d = date.today()
        s = start_of_week(d)
        e = end_of_week(d)

    entries = storage.list_entries_between(s.isoformat(), e.isoformat())
    if not entries:
        print(f"No entries for week {iso_week_key(s)} ({s.isoformat()} … {e.isoformat()})")
        return

    print(f"Week {iso_week_key(s)} ({s.isoformat()} … {e.isoformat()}):")
    day_totals = {}
    week_total = 0
    for e in entries:
        day_totals.setdefault(e["work_date"], 0)
        day_totals[e["work_date"]] += e["worked_minutes"]
        week_total += e["worked_minutes"]

    for day in sorted(day_totals.keys()):
        print(f"  {day}: {round(day_totals[day]/60.0, 2)} h")

    print(f"Total week: {round(week_total/60.0, 2)} h")

def cmd_delete(args):
    count = storage.delete_entry(args.id)
    if count:
        print(f"Deleted entry #{args.id}")
    else:
        print(f"No entry with id {args.id}")

def cmd_edit(args):
    updates = {}
    if args.start:
        updates["start_time"] = args.start
    if args.end:
        updates["end_time"] = args.end
    if args.lunch is not None:
        updates["lunch_minutes"] = args.lunch

    # If times or lunch changed, recompute worked_minutes if all required fields present
    # Fetch current record to re-calc safely
    if updates:
        # We need the record; simple approach: query by date range very wide and pick
        from storage import _connect
        import sqlite3
        conn = _connect()
        cur = conn.execute("SELECT work_date, start_time, end_time, lunch_minutes FROM entries WHERE id = ?", (args.id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            print(f"No entry with id {args.id}")
            return

        work_date, start_time, end_time, lunch_minutes = row
        if "start_time" in updates:
            start_time = updates["start_time"]
        if "end_time" in updates:
            end_time = updates["end_time"]
        if "lunch_minutes" in updates:
            lunch_minutes = updates["lunch_minutes"]

        # Recompute worked minutes
        worked = calc_work_duration(start_time, end_time, lunch_minutes)
        updates["worked_minutes"] = int(worked.total_seconds() // 60)

    changed = storage.edit_entry(args.id, updates)
    if changed:
        print(f"Updated entry #{args.id}")
    else:
        print(f"No changes applied to #{args.id}")


def build_parser():
    p = argparse.ArgumentParser(prog="workHours", description="Track work hours with lunch deduction and weekly totals.")
    sub = p.add_subparsers(dest="cmd")

    # --- add ---
    add = sub.add_parser("add", help="Add a work entry")
    add.add_argument("--date", help="Date YYYY-MM-DD (default: today)")
    add.add_argument("--start", required=True, help="Start time HH:MM (24h)")
    add.add_argument("--end", required=True, help="End time HH:MM (24h)")
    add.add_argument("--lunch", type=int, help="Lunch in minutes (default 30)")
    add.set_defaults(func=cmd_add)

    # --- day ---
    day = sub.add_parser("day", help="Show a day's entries and total")
    day.add_argument("--date", help="Date YYYY-MM-DD (default: today)")
    day.set_defaults(func=cmd_day)

    # --- week ---
    week = sub.add_parser("week", help="Show weekly totals (Mon–Sun). Provide --date to anchor the week.")
    week.add_argument("--date", help="Any date YYYY-MM-DD to pick the week (default: today’s week)")
    week.set_defaults(func=cmd_week)
    # --- delete ---
    delete = sub.add_parser("delete", help="Delete an entry by id")
    delete.add_argument("id", type=int, help="Entry ID")
    delete.set_defaults(func=cmd_delete)
    # --- edit ---
    edit = sub.add_parser("edit", help="Edit an existing entry")
    edit.add_argument("id", type=int)
    edit.add_argument("--start", help="New start time")
    edit.add_argument("--end", help="New end time")
    edit.add_argument("--lunch", type=int, help="New lunch length")
    edit.set_defaults(func=cmd_edit)

    return p


def main():
    storage.init_db()
    parser = build_parser()
    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()