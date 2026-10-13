"""Inspect selected Vulkan draws in a private RenderDoc capture."""
import json
import os
import struct
import sys
import traceback
from pathlib import Path

import renderdoc as rd

root = Path(os.environ['ACNH_RESEARCH_ROOT']).resolve()
out = Path(os.environ['ACNH_RENDERDOC_ARTIFACT_DIR']).resolve()
out.relative_to(root / 'private/windows')
out.mkdir(parents=True, exist_ok=True)
report = {}
cap = None
controller = None


def fields(value, names):
    return {name: str(getattr(value, name)) for name in names if hasattr(value, name)}


try:
    cap = rd.OpenCaptureFile()
    status = cap.OpenFile(os.environ['ACNH_RENDERDOC_CAPTURE'], '', None)
    if status.code != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if status.code != rd.ResultCode.Succeeded:
        raise RuntimeError(str(status))
    textures = {str(t.resourceId): t for t in controller.GetTextures()}
    report['docs'] = {name: getattr(rd.ReplayController, name).__doc__ for name in
                      ('GetCBufferVariableContents', 'DisassembleShader', 'GetUsage')}
    report['draws'] = []
    for event in [int(v) for v in os.environ['ACNH_RENDERDOC_EVENTS'].split(',')]:
        controller.SetFrameEvent(event, True)
        pipe = controller.GetPipelineState()
        row = dict(event=event, targets=[str(t.resource) for t in pipe.GetOutputTargets()], stages=[])
        report['draws'].append(row)
        for stage in (rd.ShaderStage.Vertex, rd.ShaderStage.Fragment):
            shader = pipe.GetShader(stage)
            reflection = pipe.GetShaderReflection(stage)
            if reflection is None:
                continue
            info = dict(stage=str(stage), shader=str(shader), resources=[], constants=[])
            row['stages'].append(info)
            try:
                assembly = controller.DisassembleShader(pipe.GetGraphicsPipelineObject(), reflection, '')
                (out / ('event-%d-%s.shader.txt' % (event, str(stage)))).write_text(assembly)
            except Exception as exc:
                info['disassembly_error'] = str(exc)
            for resource in pipe.GetReadOnlyResources(stage, True):
                descriptor = resource.descriptor
                entry = fields(descriptor, ('resource', 'view', 'type', 'byteOffset', 'byteSize'))
                entry['access'] = fields(resource.access, ('index', 'arrayElement', 'stage', 'type'))
                info['resources'].append(entry)
                texture = textures.get(str(descriptor.resource))
                if texture is not None:
                    entry['texture'] = dict(width=texture.width, height=texture.height, depth=texture.depth,
                                            arrays=texture.arraysize, format=texture.format.Name())
                    entry['usage'] = [dict(event=u.eventId, usage=str(u.usage))
                                      for u in controller.GetUsage(descriptor.resource)]
                    if texture.width * texture.height * texture.depth <= 4096:
                        raw_texture = controller.GetTextureData(descriptor.resource, rd.Subresource())
                        entry['texture']['raw_bytes'] = len(raw_texture)
                        entry['texture']['nonzero_bytes'] = sum(v != 0 for v in raw_texture)
                        (out / ('event-%d-%s.bin' % (event, str(descriptor.resource).replace('::', '-')))).write_bytes(raw_texture)
                    save = rd.TextureSave()
                    save.resourceId = descriptor.resource
                    save.destType = rd.FileType.PNG
                    controller.SaveTexture(save, str(out / ('event-%d-%s.png' % (event, str(descriptor.resource).replace('::', '-')))))
            for block in pipe.GetConstantBlocks(stage, True):
                descriptor = block.descriptor
                entry = fields(descriptor, ('resource', 'byteOffset', 'byteSize'))
                entry['access'] = fields(block.access, ('index', 'arrayElement', 'stage', 'type'))
                info['constants'].append(entry)
                raw = controller.GetBufferData(descriptor.resource, descriptor.byteOffset, descriptor.byteSize)
                (out / ('event-%d-%s-constant-%s.bin' % (event, str(stage), str(block.access.index)))).write_bytes(raw)
                entry['first_u32'] = list(struct.unpack_from('<%dI' % min(32, len(raw)//4), raw))
                entry['first_f32'] = list(struct.unpack_from('<%df' % min(32, len(raw)//4), raw))
        for target in pipe.GetOutputTargets():
            if str(target.resource) not in textures:
                continue
            save = rd.TextureSave()
            save.resourceId = target.resource
            save.destType = rd.FileType.PNG
            controller.SaveTexture(save, str(out / ('event-%d-output-%s.png' % (event, str(target.resource).replace('::', '-')))))
except Exception:
    report['error'] = traceback.format_exc()
finally:
    if controller is not None:
        controller.Shutdown()
    if cap is not None:
        cap.Shutdown()
    (out / 'pipeline-analysis.json').write_text(json.dumps(report, indent=2)+'\n')
sys.exit(0)
