import sys
import shlex
import subprocess
from datetime import date
import time

print('Uploading {} started ...'.format(sys.argv[3]))
today = date.today().strftime("%Y-%m-%d")
millis = round(time.time() * 1000)

# proxy might be required here
cmd = '''curl -u ci:eyJ2ZXIiOiIyIiwidHlwIjoiSldUIiwiYWxnIjoiUlMyNTYiLCJraWQiOiJYNktmUmpWZkFaUVk2bXdYYk9Fa25KYmZmUzNoMWpLaUN4SlY3R1RIbkxrIn0.eyJleHQiOiJ7XCJyZXZvY2FibGVcIjpcInRydWVcIn0iLCJzdWIiOiJqZmFjQDAxZzNkcjc4Y3M0emZmMDViYmF2eDUwMXAxXC91c2Vyc1wvY2kiLCJzY3AiOiJhcHBsaWVkLXBlcm1pc3Npb25zXC91c2VyIiwiYXVkIjoiKkAqIiwiaXNzIjoiamZmZUAwMDAiLCJleHAiOjE2ODQ2NzMxMzMsImlhdCI6MTY1MzEzNzEzMywianRpIjoiYWQ0MGJkZmMtOGVlMi00OWE5LWE1Y2MtMmRiMzI4YmJkYWEyIn0.SUV4V7N6-PmfpVGmBrQJysqdXVnT1fZs8IKzJlce9mzk4O0TGW7GV4Ips8oiO-pPK5bBEz0pEXyTDGgLwg3ke36G4ynmdoEJyb0LJ-0vXSv3NmMvgEwZNk_GrlMVA66N-EAH2d9p4W566ONh9YpPn7IUndgLqERwIyR25d0BycK6gMlyhlw5H0MpUHYaRlQiA7yDuq-54xyW_OyKbd_86CDzjw_Fr_HW4Scf3F5NNGEhlhTKFanynGcdfbveMcY4GBusdSs15-WdTctXCmZZpzXYHJtyW6ssRgoXrIlMI-scVdKZl0mQ6GK84NsLKy-RjtOakmw20Glg5C2P3SHX9w -X PUT "https://splbinaries.jfrog.io/artifactory/spl-generic-local/{TODAY}/{FLAVOR}_{SUBSYSTEM}_{MILLIS}.exe" -T {UPLOAD_FILE_PATH}'''.format(TODAY=today, FLAVOR=sys.argv[1], SUBSYSTEM=sys.argv[2], MILLIS=millis, UPLOAD_FILE_PATH=sys.argv[3])
print(cmd)
args = shlex.split(cmd)
process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
if stderr:
    print(stderr)
    print('Upload failed.')
    exit(1)
else:
    print('Upload finished.')
    exit(0)
