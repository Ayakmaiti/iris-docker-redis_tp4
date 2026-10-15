import csv, json, subprocess, time, uuid
from pathlib import Path

def run(args):
    subprocess.run(args, check=True)
rows = []
for variant in ('naif', 'opt'):
    builder = 'iris-bench-' + uuid.uuid4().hex[:10]
    run(['docker', 'buildx', 'create', '--name', builder, '--driver', 'docker-container'])
    try:
        run(['docker', 'buildx', 'inspect', builder, '--bootstrap'])
        for role in ('train', 'serve'):
            times = []
            for mode in ('cold', 'warm'):
                command = ['docker', 'buildx', 'build', '--builder', builder,
                           '--load', '-f', f'Dockerfile.{role}.{variant}',
                           '-t', f'iris-{role}:{variant}']
                if mode == 'cold':
                    command += ['--no-cache', '--pull']
                start = time.perf_counter()
                run(command + ['.'])
                times.append(round(time.perf_counter() - start, 2))
            size = int(subprocess.check_output(['docker', 'image', 'inspect',
                       f'iris-{role}:{variant}', '--format', '{{.Size}}'], text=True))
            rows.append({'image': f'iris-{role}:{variant}', 'size_MiB': round(size/1024**2, 2),
                         'cold_s': times[0], 'warm_s': times[1]})
    finally:
        run(['docker', 'buildx', 'rm', builder])
with open('comparaison.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps(rows, indent=2))
