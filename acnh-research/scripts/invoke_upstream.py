"""Run reviewed upstream CLIs with their import root in the embedded interpreter."""
import runpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
tool=sys.argv[1]
if tool not in ('compiler','decompiler'):raise SystemExit('Expected compiler or decompiler')
checkout=root/'vendor'/('acnh-eventflow-'+tool)
sys.path.insert(0,str(checkout))
sys.argv=[str(checkout/'main.py'),*sys.argv[2:]]
runpy.run_path(str(checkout/'main.py'),run_name='__main__')
