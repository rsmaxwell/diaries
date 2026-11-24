#!/usr/bin/env python3
"""0028 HTTP gateway: offline safety and Docker 29 network-order regression."""
import json
import copy
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
SCRIPT = TOOLS / 'verify-0028-step2-reader-http.sh'
LABEL='uk.co.rsmaxwell.diaries.0028.isolated-rehearsal'
BACK='diaries-0028-replay-net'
FRONT='diaries-0028-replay-http-front'
EXPECTED={
 '8081/tcp':[{'HostIp':'127.0.0.1','HostPort':'58081'}],
 '8082/tcp':[{'HostIp':'127.0.0.1','HostPort':'58082'}]
}


def sample():
    return {
      'Config': {'Labels':{LABEL:'true'},'Image':'nginx:alpine'},
      'NetworkSettings': {'Networks': {BACK:{'NetworkID':'a'}},
                          'Ports': {'8081/tcp':None,'8082/tcp':None}},
      'HostConfig': {'PortBindings': copy.deepcopy(EXPECTED)},
      'Mounts':[{'Destination':'/etc/nginx/conf.d/default.conf','RW':False}]
    }


class ProxyRebuildContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content=SCRIPT.read_text(encoding='utf-8')
        cls.logic=cls.content.split("<<'PY_PROXY'\n",1)[1].split('\nPY_PROXY',1)[0]

    def classify(self,obj):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            (d/'docker').write_text('#!/usr/bin/env python3\nimport os\nprint(os.environ["DOCKER_INSPECT_JSON"])\n', encoding='utf-8')
            (d/'docker').chmod(0o755)
            env=os.environ.copy()
            env['PATH']=f'{d}{os.pathsep}{env.get("PATH","")}'
            env['DOCKER_INSPECT_JSON']=json.dumps([obj])
            return subprocess.run(
                [sys.executable,'-','diaries-0028-replay-http-proxy',BACK,FRONT,LABEL],
                input=self.logic,text=True,capture_output=True,env=env)

    def test_bash_syntax(self):
        subprocess.run(['bash','-n',str(SCRIPT)],check=True)

    def test_old_internal_only_proxy_replaced(self):
        r=self.classify(sample())
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout.strip(),'replace')

    def test_absent_internal_bindings_can_be_repaired(self):
        obj=sample()
        obj['HostConfig']['PortBindings']={}
        r=self.classify(obj)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout.strip(),'replace')

    def test_full_dual_home_with_effective_host_ports_reused(self):
        obj=sample()
        obj['NetworkSettings']['Networks'][FRONT]={'NetworkID':'b'}
        obj['NetworkSettings']['Ports']=EXPECTED
        r=self.classify(obj)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout.strip(),'keep')

    def test_dual_home_without_ports_replaced(self):
        obj=sample()
        obj['NetworkSettings']['Networks'][FRONT]={'NetworkID':'b'}
        r=self.classify(obj)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout.strip(),'replace')

    def test_unlabelled_proxy_never_removed(self):
        obj=sample();obj['Config']['Labels'].clear()
        r=self.classify(obj)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('refusing replacement',r.stderr)

    def test_unexpected_network_never_removed(self):
        obj=sample();obj['NetworkSettings']['Networks']['bridge']={}
        r=self.classify(obj)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('unexpected HTTP proxy networks',r.stderr)

    def test_non_loopback_binding_never_removed(self):
        obj=sample();obj['HostConfig']['PortBindings']['8082/tcp'][0]['HostIp']='0.0.0.0'
        r=self.classify(obj)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('unexpected bindings',r.stderr)

    def test_missing_readonly_mount_never_removed(self):
        obj=sample();obj['Mounts'][0]['RW']=True
        r=self.classify(obj)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('read-only nginx',r.stderr)

    def test_frontend_first_and_stopped_before_network_attachment(self):
        s=self.content
        self.assertIn('docker create --name "$proxy" --network "$frontend"',s)
        i=s.index('docker create --name "$proxy" --network "$frontend"')
        j=s.index('docker network connect "$backend" "$proxy"',i)
        k=s.index('docker start "$proxy"',j)
        self.assertLess(i,j)
        self.assertLess(j,k)
        self.assertNotIn('docker rm -f "$db"',s)
        self.assertNotIn('docker rm -f "$reader"',s)
        self.assertNotIn('docker rm -f "$broker"',s)
        self.assertNotIn('docker rm -f "$responder"',s)


if __name__=='__main__':
    unittest.main(verbosity=2)
