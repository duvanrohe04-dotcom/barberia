import json
import urllib.request
import tarfile
import io

name = 'evoapicloud/evolution-api'
tag = 'v2.3.7'

url = f'https://auth.docker.io/token?service=registry.docker.io&scope=repository:{name}:pull'
with urllib.request.urlopen(url, timeout=20) as r:
    token = json.load(r)['token']

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.oci.image.index.v1+json'}

req = urllib.request.Request(f'https://registry-1.docker.io/v2/{name}/manifests/{tag}', headers=headers)
with urllib.request.urlopen(req, timeout=20) as r:
    idx = json.load(r)

amd64 = [m for m in idx['manifests'] if m['platform']['architecture'] == 'amd64'][0]
print('selected manifest:', amd64['digest'])
req = urllib.request.Request(f'https://registry-1.docker.io/v2/{name}/manifests/{amd64['digest']}', headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.oci.image.manifest.v1+json'})
with urllib.request.urlopen(req, timeout=20) as r:
    manifest = json.load(r)

for i, layer in enumerate(manifest['layers']):
    print('layer', i, layer['digest'], layer['size'])
    req = urllib.request.Request(f'https://registry-1.docker.io/v2/{name}/blobs/{layer['digest']}', headers={'Authorization': f'Bearer {token}'})
    data = urllib.request.urlopen(req, timeout=120).read()
    try:
        tar = tarfile.open(fileobj=io.BytesIO(data), mode='r:gz')
    except Exception as e:
        print('not gzip', e)
        continue
    for member in tar.getmembers():
        if 'deploy_database.sh' in member.name:
            print('FOUND', member.name)
            txt = tar.extractfile(member).read().decode('utf-8', errors='ignore')
            print(txt)
            raise SystemExit
print('script not found')
