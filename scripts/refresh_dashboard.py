#!/usr/bin/env python3
"""Rebuild the dashboard with dated archives and rollback on a failed refresh."""
import argparse
import csv
from datetime import date, datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GENERATED = [
    'data/source_catalog.csv', 'data/document_coverage.csv', 'data/collection_summary.json',
    'data/collected_forecasts.csv', 'data/issuer_outcomes.csv', 'data/revenue_pilot.csv',
    'data/eps_pilot.csv', 'data/eps_pilot.json',
    *['data/market/' + name for name in ['prices.csv', 'splits.csv', 'summary.json',
        'forecast_panel.csv', 'forecast_series.csv', 'forecast_gaps.json',
        'monthly_gap_map.json', 'monthly_gap_map.csv', 'collection_targets.json',
        'backtest_readiness.json', 'delivery_report.json', 'missing_data_dates.csv']],
    'web/public/data/dashboard.json', 'web/dist',
]


def copy_path(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


class Rollback:
    """Restore all generated artifacts, including files absent before the run."""
    def __init__(self, root, run, paths=GENERATED):
        self.root, self.run, self.paths = root, run, paths

    def __enter__(self):
        for name in self.paths:
            if (self.root / name).exists():
                copy_path(self.root / name, self.run / 'before' / name)
        return self

    def __exit__(self, error_type, error, traceback):
        if error_type is not None:
            for name in self.paths:
                target, backup = self.root / name, self.run / 'before' / name
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink(missing_ok=True)
                if backup.exists():
                    copy_path(backup, target)
        return False


def input_paths(root):
    paths = [root / name for name in ['data/universe.csv', 'data/archive.sqlite',
             'data/market/basis_aliases.json', 'data/market/imported_ntm.json',
             'data/market/observation_exclusions.json', 'data/market/availability_evidence.json',
             'data/market/ensemble_compatibility.json', 'data/market/model_date_evidence.json',
             'data/market/price_supplements.json']]
    paths += list((root / 'data/collection').glob('*/*.csv'))
    paths += list((root / 'data/collection').glob('*/*.json'))
    paths += list((root / 'scripts').glob('*.py')) + list((root / 'scripts').glob('*.mjs'))
    paths += list((root / 'web/src').glob('*.ts')) + list((root / 'web/src').glob('*.tsx'))
    return sorted({path for path in paths if path.is_file()})


def archive_inputs(root, run):
    records = []
    for source in input_paths(root):
        relative = source.relative_to(root)
        copy_path(source, run / 'inputs' / relative)
        records.append({'path': str(relative), 'sha256': hashlib.sha256((run / 'inputs' / relative).read_bytes()).hexdigest()})
    return records


def validate_prices(root, before, cutoff):
    summary = json.loads((root / 'data/market/summary.json').read_text())
    with (root / 'data/universe.csv').open() as handle:
        expected = {r['company_id'] for r in csv.DictReader(handle)}
    available = {r['company_id'] for r in summary['coverage'] if r['status'] == 'available'}
    if available != expected or not summary['adjustment_definition_verified'] or summary['cutoff'] != cutoff:
        raise ValueError('Price refresh lacks a company, split-adjustment evidence or the requested cutoff')
    with (root / 'data/market/prices.csv').open() as handle:
        current = {(r['company_id'], r['date']) for r in csv.DictReader(handle)}
    if before.exists():
        with before.open() as handle:
            missing = {(r['company_id'], r['date']) for r in csv.DictReader(handle) if r['date'] <= cutoff} - current
        if missing:
            raise ValueError(f'Price refresh lost {len(missing)} previously retained sessions')


def refresh(args, root=ROOT):
    market = json.loads((root / 'data/market/summary.json').read_text())
    as_of = args.as_of or (datetime.now(timezone.utc).date().isoformat() if args.prices else market['cutoff'])
    if date.fromisoformat(as_of) > datetime.now(timezone.utc).date():
        raise ValueError('The refresh cutoff cannot be in the future')
    if not (args.prices or args.replay_prices) and as_of != market['cutoff']:
        raise ValueError('Changing the cutoff requires --prices so that split units stay consistent')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    run = root / 'data/refresh' / stamp
    run.mkdir(parents=True)
    record = {'started_at': stamp, 'as_of': as_of, 'status': 'running', 'commands': [],
              'prices_requested': args.prices, 'replay_prices': args.replay_prices, 'discovery_days': args.discover_days}

    def save():
        (run / 'run.json').write_text(json.dumps(record, indent=2) + '\n')

    def execute(command):
        record['commands'].append(command)
        save()
        print('Running: ' + ' '.join(command), flush=True)
        with (run / 'commands.log').open('a') as log:
            log.write('\n' + ' '.join(command) + '\n')
            log.flush()
            subprocess.run(command, cwd=root, check=True, stdout=log, stderr=subprocess.STDOUT)

    save()
    try:
        with Rollback(root, run):
            record['archived_inputs'] = archive_inputs(root, run)
            save()
            if args.discover_days:
                from discover_reports import discover
                record['discovery'] = discover(date.fromisoformat(as_of), args.discover_days, root)
                save()
            if args.prices or args.replay_prices:
                command = [sys.executable, 'scripts/collect_prices.py', '--start', market['requested_start'], '--cutoff', as_of]
                if args.replay_prices:
                    command.append('--offline')
                execute(command)
            execute([sys.executable, 'scripts/apply_price_supplements.py'])
            validate_prices(root, run / 'before/data/market/prices.csv', as_of)
            for script in ['index_collection', 'merge_forecasts', 'build_forecast_panel',
                           'build_korean_outcomes', 'compare_revenue_pilot', 'compare_eps_pilot', 'build_dashboard_data']:
                command = [sys.executable, f'scripts/{script}.py']
                if script == 'index_collection':
                    command.append('--no-db-update')
                if script in {'build_forecast_panel', 'compare_eps_pilot', 'build_dashboard_data'}:
                    command += ['--as-of', as_of]
                execute(command)
            execute(['node', 'scripts/build_gap_map.mjs'])
            execute(['node', 'scripts/build_backtest_readiness.mjs'])
            execute(['node', 'scripts/build_delivery_report.mjs'])
            # Vite builds away from the served directory. Publish only on success.
            staged = run / 'dist'
            execute(['npm', 'run', 'build', '--prefix', 'web', '--', '--outDir', str(staged)])
            if {str(path.relative_to(root)) for path in input_paths(root)} != {item['path'] for item in record['archived_inputs']}:
                raise ValueError('Collection inputs were added or removed during refresh; retry after collection finishes')
            for item in record['archived_inputs']:
                if hashlib.sha256((root / item['path']).read_bytes()).hexdigest() != item['sha256']:
                    raise ValueError(f"Input changed during refresh: {item['path']}. Retry after collection finishes.")
            if (root / 'web/dist').exists():
                (root / 'web/dist').rename(run / 'previous_dist')
            staged.rename(root / 'web/dist')
            for name in GENERATED:
                if (root / name).exists():
                    copy_path(root / name, run / 'after' / name)
            bundle = json.loads((root / 'web/public/data/dashboard.json').read_text())
            record.update(status='complete', finished_at=datetime.now(timezone.utc).isoformat(),
                          forecasts=bundle['totals']['forecast_observations'],
                          latest_prices={c['id']: c['prices'][-1]['date'] for c in bundle['companies']},
                          notice='Only reviewed collections enter the chart. New discovery PDFs remain in the review inbox.')
            save()
    except BaseException as error:
        record.update(status='failed_restored', error=str(error), finished_at=datetime.now(timezone.utc).isoformat())
        save()
        raise
    print(json.dumps({k: v for k, v in record.items() if k not in {'archived_inputs', 'commands'}}))
    print(f'Archive and command log: {run.relative_to(root)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    prices = parser.add_mutually_exclusive_group()
    prices.add_argument('--prices', action='store_true', help='Download public daily prices; otherwise rebuild offline')
    prices.add_argument('--replay-prices', action='store_true', help='Reparse the latest retained price downloads without requesting them again')
    parser.add_argument('--as-of', help='YYYY-MM-DD; defaults to today with --prices, otherwise retained price cutoff')
    parser.add_argument('--discover-days', type=int, default=0, choices=range(32), metavar='0..31', help='Check seven public report IDs; new PDFs await EPS review')
    args = parser.parse_args()
    def stop(signum, frame):
        raise InterruptedError('Refresh interrupted; restoring generated artifacts')
    signal.signal(signal.SIGTERM, stop)
    with (ROOT / 'data/.refresh.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error('Another dashboard refresh is running')
        refresh(args)


if __name__ == '__main__':
    main()
