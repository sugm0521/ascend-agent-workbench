"""Read a selected batch's state and file counts, no launches or state writes."""
import argparse
import hashlib
import json
from pathlib import Path


def status(plan_path, state_path):
    raw = plan_path.read_bytes()
    plan, state = json.loads(raw), json.loads(state_path.read_text())
    if state['plan_sha256'] != hashlib.sha256(raw).hexdigest():
        raise ValueError('state and plan do not match')
    if len(plan['groups']) != len(state['groups']):
        raise ValueError('group count differs')
    groups = []
    for group, recorded in zip(plan['groups'], state['groups']):
        if recorded['id'] != group['id']:
            raise ValueError('group identity differs')
        evidence = Path(group['root']) / 'api-evidence'
        groups.append({'id': group['id'], 'status_recorded': recorded['status'],
            'request_files': len(list(evidence.glob('*.request.json'))),
            'response_files': len(list(evidence.glob('*.response.json'))),
            'root': group['root']})
    return {'supervisor_status_recorded': state['status'], 'groups': groups,
        'completed_groups_recorded': sum(g['status_recorded'] == 'completed' for g in groups),
        'evidence_scope': 'File counts are not unique completed questions or response-quality acceptance'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--state-file', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(status(args.plan, args.state_file)))


if __name__ == '__main__':
    main()
