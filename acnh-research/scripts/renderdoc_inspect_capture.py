"""Inspect a private capture with qrenderdoc --py; no UI or uploads."""
import json
import os
import struct
import sys
import traceback
from pathlib import Path
import renderdoc as rd

root = Path(os.environ['ACNH_RESEARCH_ROOT'])
output = root/'private/windows/renderdoc-analysis.json'
cap = None
controller = None
report = {}
try:
    filename = Path(os.environ['ACNH_RENDERDOC_CAPTURE'])
    cap = rd.OpenCaptureFile()
    result = cap.OpenFile(str(filename), '', None)
    if result.code != rd.ResultCode.Succeeded:
        raise RuntimeError(str(result))
    result, controller = cap.OpenCapture(rd.ReplayOptions(), None)
    if result.code != rd.ResultCode.Succeeded:
        raise RuntimeError(str(result))
    textures = {str(t.resourceId): t for t in controller.GetTextures()}
    def rgb_nonzero(texture, raw):
        if texture.format.Name() == 'R10G10B10A2_UNORM':
            return sum((word[0] & 0x3fffffff) != 0 for word in struct.iter_unpack('<I', raw))
        if not texture.format.Special() and texture.format.compCount == 4 and texture.format.compByteWidth == 1:
            return sum(any(raw[i:i+3]) for i in range(0, len(raw), 4))
        return None
    report['textures'] = [dict(id=str(t.resourceId), width=t.width, height=t.height,
                               format=t.format.Name(), special_format=t.format.Special(),
                               component_count=t.format.compCount,
                               component_bytes=t.format.compByteWidth,
                               component_type=str(t.format.compType)) for t in textures.values()]
    def walk(actions):
        for action in actions:
            yield action
            yield from walk(action.children)
    actions = list(walk(controller.GetRootActions()))
    report['actions'] = len(actions)
    report['action_details'] = [dict(event=a.eventId, name=a.GetName(controller.GetStructuredFile()),
        flags=str(a.flags), copy_source=str(a.copySource), copy_destination=str(a.copyDestination))
        for a in actions]
    report['api_docs'] = {name: getattr(rd.PipeState, name).__doc__ for name in
                          ('GetConstantBlocks', 'GetConstantBlock', 'GetReadOnlyResources')}
    report['fullsize_draws'] = []
    for action in actions:
        if not (action.flags & rd.ActionFlags.Drawcall):
            continue
        controller.SetFrameEvent(action.eventId, True)
        pipe = controller.GetPipelineState()
        targets = pipe.GetOutputTargets()
        target_ids = [str(t.resource) for t in targets]
        if not any(i in textures and textures[i].width >= 1280 and textures[i].height >= 720 for i in target_ids):
            continue
        mesh = controller.GetPostVSData(0, 0, rd.MeshDataStage.VSOut)
        raw = controller.GetBufferData(mesh.vertexResourceId, mesh.vertexByteOffset, mesh.vertexByteStride*4)
        positions = []
        if mesh.vertexByteStride >= 16:
            for i in range(min(4, len(raw)//mesh.vertexByteStride)):
                positions.append(struct.unpack_from('<4f', raw, i*mesh.vertexByteStride))
        vertices = [dict(id=str(b.resourceId), offset=b.byteOffset, stride=b.byteStride, size=b.byteSize)
                    for b in pipe.GetVBuffers()]
        report['fullsize_draws'].append(dict(event=action.eventId, indices=action.numIndices,
            targets=target_ids, vertex_shader=str(pipe.GetShader(rd.ShaderStage.Vertex)),
            fragment_shader=str(pipe.GetShader(rd.ShaderStage.Fragment)),
            positions=positions, vertex_stride=mesh.vertexByteStride, vertex_buffers=vertices))
        row = report['fullsize_draws'][-1]
        row['raw_first_vertex'] = list(struct.unpack_from('<'+'f'*(mesh.vertexByteStride//4), raw)) if raw else []
        row['resources'] = []
        for resource in pipe.GetReadOnlyResources(rd.ShaderStage.Fragment, True):
            descriptor = resource.descriptor
            row['resources'].append({name: str(getattr(descriptor, name)) for name in
                                     ('resource', 'view', 'type') if hasattr(descriptor, name)})
        if len(report['fullsize_draws']) >= 24:
            break
    large_textures = [t for t in textures.values() if t.width >= 1280 and t.height >= 720]
    selected_id = os.environ.get('ACNH_RENDERDOC_TARGET', str(large_textures[0].resourceId))
    target = textures[selected_id]
    report['selected_target'] = selected_id
    event_list = os.environ.get('ACNH_RENDERDOC_EVENTS')
    selected_events = [int(v) for v in event_list.split(',')] if event_list else sorted(set(
        [row['event'] for row in report['fullsize_draws'][:1] + report['fullsize_draws'][-2:]]))
    report['event_images'] = []
    for event in selected_events:
        controller.SetFrameEvent(event, True)
        for texture in large_textures:
            resource = str(texture.resourceId)
            raw = controller.GetTextureData(texture.resourceId, rd.Subresource())
            report['event_images'].append(dict(event=event, resource=resource,
                rgb_nonzero=rgb_nonzero(texture, raw)))
            save = rd.TextureSave()
            save.resourceId = texture.resourceId
            save.destType = rd.FileType.PNG
            controller.SaveTexture(save, str(root/('private/windows/rdoc-event-'+str(event)+'-'+resource.replace('::','-')+'.png')))
    controller.SetFrameEvent(max(a.eventId for a in actions), True)
    report['pixel_history'] = []
    for x, y in [(960, 540), (1750, 950), (1810, 1010)]:
        history = controller.PixelHistory(target.resourceId, x, y, rd.Subresource(), rd.CompType.UNorm)
        report['pixel_history'].append(dict(x=x, y=y, modifications=[dict(
            event=m.eventId,
            flags={name: bool(getattr(m, name)) for name in ('backfaceCulled', 'depthTestFailed', 'depthClipped',
                    'scissorClipped', 'shaderDiscarded', 'sampleMasked', 'unboundPS') if hasattr(m, name)},
            before=list(m.preMod.col.floatValue), after=list(m.postMod.col.floatValue),
            shader=list(m.shaderOut.col.floatValue)) for m in history]))
    report['texture_channels'] = []
    for texture in textures.values():
        if texture.format.Special() or texture.format.compCount != 4 or texture.format.compByteWidth != 1:
            continue
        raw = controller.GetTextureData(texture.resourceId, rd.Subresource())
        if len(raw) != texture.width*texture.height*4:
            continue
        alpha = raw[3::4]
        rgb_count = rgb_nonzero(texture, raw)
        report['texture_channels'].append(dict(id=str(texture.resourceId), width=texture.width,
            height=texture.height, alpha_min=min(alpha), alpha_max=max(alpha),
            alpha_nonzero=sum(v != 0 for v in alpha), rgb_nonzero=rgb_count))
        if texture.width >= 1280:
            save = rd.TextureSave()
            save.resourceId = texture.resourceId
            save.destType = rd.FileType.PNG
            controller.SaveTexture(save, str(root/('private/windows/rdoc-image-'+str(texture.resourceId).replace('::','-')+'.png')))
    report['debug_messages'] = [dict(description=m.description, event=m.eventId) for m in controller.GetDebugMessages()]
except Exception:
    report['error'] = traceback.format_exc()
finally:
    if controller is not None:
        controller.Shutdown()
    if cap is not None:
        cap.Shutdown()
    output.write_text(json.dumps(report, indent=2)+'\n')
sys.exit(0)
