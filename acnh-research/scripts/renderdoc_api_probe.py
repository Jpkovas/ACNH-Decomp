"""Run with qrenderdoc --py before UI startup; keep introspection private."""
import json
import os
import sys
import traceback
from pathlib import Path
import renderdoc as rd

root = Path(os.environ.get('ACNH_RESEARCH_ROOT', str(Path.cwd()/'acnh-research')))
try:
    capture = rd.OpenCaptureFile()
    report = {
        'capture_api': [name for name in dir(capture) if not name.startswith('_')],
        'controller_api': [name for name in dir(rd.ReplayController) if not name.startswith('_')],
        'pipeline_api': [name for name in dir(rd.PipeState) if not name.startswith('_')],
    }
    capture.Shutdown()
except Exception:
    report = {'error': traceback.format_exc()}
(root/'private/windows/renderdoc-api.json').write_text(json.dumps(report, indent=2)+'\n')
sys.exit(0)
