"""Bind one real player35 startup to frozen module proofs and private evidence.

Only aggregate facts/hashes are public. No raw captures, assets, PCM, ARM64 code,
keys or firmware are copied. This is technical milestone evidence awaiting
coordinator acceptance; it neither promotes defaults nor edits public coverage.
"""
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import argparse
import array
import functools
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import re
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'private'
OWN = PRIVATE / 'team/player35-startup'
PUBLIC = ROOT / 'metadata/windows/1.0.0/startup-player35-team-validation.json'
DLL = '5829252d9988715a4727ed015f216675b0b0b3ac06c8a639caac65afeb09cd9b'
RUNTIME = 'df489bdd58d0304bd0f924cd9a753ec67d52ca0e28a47562251b2fa695083658'
DEFAULT_DLL = '2797747f4e69977388ff27cf9d04341b2b55a631a9c739f30351b7101a9a730d'
DEFAULT_RUNTIME = 'dfe9256e44081bdeefa30c6b87e18442c0eade390cc919ff1d401be7c96c7f94'
FROZEN_EPOCH_REPORTER = '4e7419326893e2f66c1a19b15c00a41d9a4eb9c4ac2cc2060da0877dd857f271'
FROZEN_EPOCH_REPORT = 'be7396e1c20dc003d44b68446b0f68665210e23bbc151bce9656f39250e2b0e6'
POST_RUN_ORCHESTRATION = {'scripts/build_windows_game.ps1', 'windows_bridge/CMakeLists.txt'}
BASELINES = [('native-20261013-182810', 9, 'dialogue',
              'Coordinator observation preserved in handoff; not inferred from frame counts.'),
             ('native-20261013-183257', 14, 'loading',
              'Coordinator controlled comparison remained loading with zero PCM.'),
             ('epoch-team-20261013-194828', 14, 'dialogue',
              'Coordinator inspected captures bound by frozen startup-epoch-team-validation.json.')]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def private_path(name):
    p = (ROOT / Path(name)).resolve()
    p.relative_to(PRIVATE.resolve())
    return p


def relative(name):
    return Path(name).resolve().relative_to(ROOT.resolve()).as_posix()


def read(name):
    return json.loads(Path(name).read_text(encoding='utf-8-sig'))


def direct_sha(name):
    with Path(name).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


@functools.lru_cache(maxsize=None)
def sha(name):
    return direct_sha(name)


def binding(name, expected=None):
    p = private_path(name)
    actual = sha(p)
    if expected:
        require(actual == expected, 'Private evidence hash differs: ' + relative(p))
    return dict(private_path=relative(p), sha256=actual, bytes=p.stat().st_size)


def validate_terminal(run, rich=True):
    require(run['mode'] == 'native', 'Expected the recorded hybrid native mode')
    if rich:
        for name in ('harness_terminal_complete', 'postprocessing_complete',
                     'process_handle_captured', 'process_absent_confirmed',
                     'auxiliary_process_absent_confirmed', 'audio_finalized',
                     'environment_restored'):
            require(run.get(name) is True, 'Incomplete terminal evidence: ' + name)
        require(run['terminal_state'] == 'natural-exit' and not run['forced_termination'],
                'Forced or missing natural terminal')
        require(run['termination_reason'] is None, 'Unexpected termination reason')
        require(run['process_exit_code'] == run['harness_exit_code'] == 0, 'Nonzero terminal exit')
        require(not run['errors'] and not run['postprocess_errors'], 'Harness/postprocess errors')
        require(run['pid_absence_observation'] == 'handle-exited-and-pid-absent', 'Missing absence observation')
        require(run['timing_lock']['action'] == 'released-same-lease' and
                run['timing_lock']['attention'] is None, 'Timing lease cleanup differs')
        analysis = run['audio_analysis_process']
        require(analysis['exit_code'] == 0 and analysis['handle_captured'] and
                analysis['handle_exited'] and not analysis['forced_termination'],
                'Audio analysis child did not end naturally')
        require(run['flags']['seconds'] == 180 and 180 <= run['process_elapsed_seconds'] < 200,
                'Unexpected startup window')
        require(not any(run.get(k) for k in ('playable_validated', 'gameplay_validated',
                                            'save_reload_validated')), 'Startup report overclaims gameplay')
    else:
        require(run['exit_code'] == 0 and 180 <= run['elapsed_seconds'] < 200,
                'Legacy comparison is not a recorded normal 180-second-window exit')


def controls(run, rich):
    if rich:
        r = dict(run['flags'])
    else:
        r = dict(run)
        r.update(live_input=bool(run['live_input_file']),
                 capture_filesystem=run['filesystem_capture'],
                 capture_gpu_fifo=bool(run['gpu_fifo_capture']),
                 capture_graphics=bool(run['graphics_capture_trigger']))
    keys = ('headless', 'docked', 'input_script', 'press_length_ms', 'shot_every_frames',
            'native_audio', 'native_vp9', 'live_input', 'capture_filesystem',
            'capture_gpu_fifo', 'capture_graphics', 'audio_wav_only')
    return dict(mode=run['mode'], **{k: r[k] for k in keys})


def logs(run):
    result = {k: binding(run[k]) for k in ('stdout', 'stderr', 'game_log', 'live_input_file')}
    require(not private_path(run['live_input_file']).read_text(encoding='utf-8-sig').strip(),
            'Controlled live input file is not empty')
    stderr = private_path(run['stderr']).read_text(errors='replace')
    found = re.findall(r'^frames=(\d+) hash=([0-9a-f]+)\s*$', stderr, re.M)
    require(len(found) == 1, 'Ambiguous or missing terminal frame summary')
    result['rendered_frames'] = int(found[0][0])
    result['runtime_frame_hash'] = found[0][1]
    result['live_input_has_commands'] = False
    result['stderr_contains_warnings'] = 'not done' in stderr
    return result


def audio_evidence(run, recompute=False, raw_required=False):
    report_path = private_path(run['audio_analysis'])
    audio = read(report_path)
    wav_path = private_path(run['audio_wav'])
    final = wav_path.read_bytes()
    require(sha(wav_path) == audio['sha256'], 'Final WAV does not match analysis hash')
    require(len(final) >= 44 and final[:4] == b'RIFF' and final[8:16] == b'WAVEfmt ' and
            final[36:40] == b'data', 'Expected canonical PCM capture')
    require(struct.unpack_from('<HHIIHH', final, 20) == (1, 2, 48000, 192000, 4, 16),
            'PCM format differs')
    require(struct.unpack_from('<I', final, 4)[0] == len(final)-8 and
            struct.unpack_from('<I', final, 40)[0] == len(final)-44 and (len(final)-44) % 4 == 0,
            'Final WAV lengths/frames differ')
    frames = (len(final)-44)//4
    require((audio['sample_rate'], audio['channels'], audio['bits'], audio['pcm_frames'],
             audio['actual_data_bytes']) == (48000, 2, 16, frames, len(final)-44),
            'Audio report layout/count differs')
    require(audio['duration_seconds'] == frames/48000 and audio['riff_lengths_finalized'],
            'Audio duration/finalization differs')
    result = dict(analysis=binding(report_path), final_wav=binding(wav_path),
                  sample_rate=48000, channels=2, bits=16, pcm_frames=frames,
                  duration_seconds=audio['duration_seconds'], channel_metrics=audio['channel_metrics'],
                  pcm_payload_sha256=hashlib.sha256(final[44:]).hexdigest(),
                  metrics_independently_recomputed=recompute)
    if raw_required:
        raw_path = private_path(run['audio_wav_raw'])
        raw = raw_path.read_bytes()
        require(sha(raw_path) == run['audio_wav_sha256_before_finalize'], 'Raw WAV hash differs')
        require(sha(wav_path) == run['audio_wav_sha256'], 'Terminal final WAV hash differs')
        require(len(raw) == len(final) and raw[:4] == final[:4] and raw[8:40] == final[8:40]
                and raw[44:] == final[44:], 'WAV finalization changed bytes beyond RIFF/data lengths')
        require(struct.unpack_from('<I', raw, 40)[0] == audio['previous_advertised_data_bytes'],
                'Previous WAV data length differs')
        result.update(raw_wav=binding(raw_path), only_riff_data_lengths_finalized=True)
    if recompute:
        pcm = array.array('h')
        pcm.frombytes(final[44:])
        if sys.byteorder != 'little': pcm.byteswap()
        actual = []
        for channel in range(2):
            values = pcm[channel::2]
            actual.append(dict(nonzero_samples=sum(v != 0 for v in values),
                peak=max(map(abs, values), default=0),
                rms=math.sqrt(sum(float(v)*v for v in values)/max(1, len(values))),
                clipped_samples=sum(v in (-32768, 32767) for v in values)))
        require(actual == audio['channel_metrics'], 'Independent PCM metrics differ')
    result['nonzero_samples'] = sum(c['nonzero_samples'] for c in audio['channel_metrics'])
    result['clipped_samples'] = sum(c['clipped_samples'] for c in audio['channel_metrics'])
    return result


def ppm_capture(name):
    p = private_path(name)
    raw = p.read_bytes()
    magic, dimensions, maximum, rgb = raw.split(b'\n', 3)
    width, height = map(int, dimensions.split())
    require(magic == b'P6' and maximum == b'255' and width > 0 and height > 0 and
            len(rgb) == width*height*3, 'Invalid complete PPM capture')
    return dict(**binding(p), width=width, height=height), rgb


def snapshots_and_gates(preflight, coverage_path, terminal_time):
    snap_path = ROOT/'private/team/player35-integration/final-snapshot.json'
    snapshot = read(snap_path)
    require(sha(snap_path) == preflight['snapshot_sha256'], 'Preflight/final snapshot binding differs')
    require(preflight['source_bindings'] == 33 and not preflight['source_drift'] and
            preflight['defaults_preserved'], 'Preflight source/default check differs')
    source_status=[]
    terminal_datetime=datetime.fromisoformat(terminal_time.replace('Z','+00:00'))
    orchestration_archive=PRIVATE/'team/publication35-review/pre-change'
    archive_path=orchestration_archive/'snapshot.json'
    archive=read(archive_path)
    require(datetime.fromisoformat(archive['created_utc'].replace('Z','+00:00')) > terminal_datetime,
            'Orchestration archive predates the completed run')
    for name, expected in snapshot['source_hashes'].items():
        current=direct_sha(ROOT/name)
        changed=current != expected
        mtime=datetime.fromtimestamp((ROOT/name).stat().st_mtime,timezone.utc)
        if changed:
            require(name in POST_RUN_ORCHESTRATION and mtime > terminal_datetime,
                    'Non-authorized or pre-terminal final source drift: '+name)
        status=dict(path=name,historical_sha256=expected,current_sha256=current,
            changed_after_run=changed,current_mtime_utc=mtime.isoformat(),
            authority='Coordinator explicitly authorized post-run Clean/CPU orchestration work by pin_review'
                      if changed else None,
            claim='Historical compiled runtime/module proof remains pinned to final-snapshot05d8; new build route not executed'
                  if changed else 'Current hash matches historical source snapshot')
        if name in POST_RUN_ORCHESTRATION:
            require(archive['files'][name] == expected, 'Historical orchestration archive record differs')
            status['historical_before_copy']=binding(orchestration_archive/name,expected)
            status['authority']='Coordinator authorized post-run Clean/CPU orchestration review by pin_review'
            status['claim']='Historical before-copy governs the finished run; current build route has no new build/runtime proof here'
        source_status.append(status)
    for name, expected in snapshot['generated_hashes'].items():
        require(sha(private_path(name)) == expected, 'Final generated/provenance drift: '+name)
    for name, expected in snapshot['report_hashes'].items():
        require(sha(private_path(name)) == expected, 'Final ABI report drift: '+name)
    manifest_path = ROOT/'private/windows/bridge-player35-candidate/reconstructed-replacements.json'
    manifest = read(manifest_path)
    mh = sha(manifest_path)
    require(mh == snapshot['candidate_manifest_sha256'], 'Final candidate manifest differs')
    require(len(manifest['replacements']) == 35, 'Expected35 manifest')
    coverage = read(coverage_path)
    require(coverage['passed'] and not coverage['accepted_for_publication'] and
            coverage['coverage_increment'] == 0, 'Expected unpublished private coverage proxy')
    require((coverage['candidate_complete_entries'], coverage['candidate_original_body_bytes'],
             coverage['proposed_added_entries'], coverage['proposed_added_body_bytes'],
             coverage['exefs_text_bytes']) == (35,4696,21,2484,44815680), 'Candidate scope differs')
    require(coverage['tested_candidate_dll_sha256'] == DLL and
            coverage['corresponding_manifest_sha256'] == mh, 'Private coverage artifact binding differs')
    require(coverage['candidate_coverage_percent'] == 100*4696/44815680, 'Candidate percentage differs')
    bodies = coverage['complete_original_bodies']
    require(len(bodies) == 35 and sum(b['original_body_bytes'] for b in bodies) == 4696 and
            {(b['module'],b['relative_address']) for b in bodies} ==
            {(r['module'],r['module_relative']) for r in manifest['replacements']}, 'Coverage/manifest intervals differ')
    intervals = []
    for b in bodies:
        start=int(b['relative_address'],16); end=start+b['original_body_bytes']
        require(end > start and not any(m == b['module'] and start < y and x < end
                 for m,x,y in intervals), 'Duplicate/overlapping candidate body interval')
        intervals.append((b['module'],start,end))
    require(sum(m['text_bytes'] for m in coverage['modules']) == 44815680, 'Full denominator differs')
    reports = {}
    for name, h in coverage['gate_report_hashes'].items():
        p=ROOT/'private/team/player35-integration/reports'/(name+'.json')
        require(sha(p) == h, 'Coverage current ABI gate binding differs: '+name)
        gate=read(p)
        require(gate['passed'], 'Failed module gate: '+name)
        require(gate.get('library_sha256',gate.get('dll_sha256',gate.get('tested_library_sha256'))) == DLL,
                'Module ABI proof binds another DLL: '+name)
        if name != 'core':
            require(gate.get('corresponding_manifest_sha256',gate.get('replacements_manifest_sha256')) == mh,
                    'Module ABI proof binds another manifest: '+name)
        if name.startswith('player'):
            require((gate['abi_case_count'],gate['normal_terminal_cases'],gate['prefix_cases']) == (246,186,60),
                    'Player corpus scope differs')
            require(gate['validator_sha256'] == direct_sha(ROOT/'scripts/validate_player35_module.py'),
                    'Player validator drift')
        if name.startswith('saveio'):
            require((gate['native_cases'],gate['module_guard_fallback_sentinel_cases'],
                     gate['module_interior_fallback_sentinel_cases'],gate['module_original_defined_fallback_cases']) ==
                    (150,15,5,6), 'SaveIO corpus scope differs')
        reports[name]=dict(**binding(p), passed=True)
    require(set(reports) == {'core','context','flag-table','access-key','npad','saveio-api',
                             'saveio-no-api','player-api','player-no-api'}, 'Required actual-module gate inventory differs')
    for name in ('runtime-ctest', 'player-api-bound', 'player-no-api-bound'):
        g=snapshot['gate_proofs'][name]
        require(g['exit_code'] == 0 and g['inputs_unchanged'] and
                sha(private_path(g['record'])) == g['sha256'] and
                sha(private_path(g['log'])) == g['log_sha256'], 'Bound gate record/log differs: '+name)
    ctest=snapshot['gate_proofs']['runtime-ctest']
    require('100% tests passed, 0 tests failed out of 13' in private_path(ctest['log']).read_text(),
            'Historical CTest count/summary differs')
    loader=snapshot['loader_proof']
    loader_path=private_path(loader['path'])
    require(sha(loader_path) == loader['sha256'], 'Historical loader proof hash differs')
    loader_report=read(loader_path)
    require(loader_report['passed'] and len(loader_report['cases']) == 4 and
            loader_report['runtime_sha256_before'] == loader_report['runtime_sha256_after'] == RUNTIME and
            all(c['passed'] and c['returncode'] == 1 and c['terminal_exit_observed'] and
                not c['forced_termination'] for c in loader_report['cases']), 'Historical loader cases differ')
    return dict(snapshot=binding(snap_path), manifest=binding(manifest_path),
                private_coverage=binding(coverage_path), actual_module_reports=reports,
                historical_source_bindings=len(snapshot['source_hashes']), source_status=source_status,
                post_run_orchestration_changes=[s for s in source_status if s['changed_after_run']],
                post_run_orchestration_before_archive=binding(archive_path),
                historical_runtime_gates=dict(ctest_tests=13,ctest_record=binding(private_path(ctest['record'])),
                    loader=binding(loader_path),loader_cases=4,new_execution_performed_by_aggregator=False),
                generated_bindings=len(snapshot['generated_hashes']),
                compiled_new_objects=len(snapshot['compiled_candidate_objects']), reused_objects=len(snapshot['reused_objects']),
                clean_build=False, cross_machine_reproducibility_validated=False)


def aggregate(run_path, ppm_path, png_path, observation, observer):
    require(observation.strip() and observer.strip(), 'Explicit visual observation and attribution required')
    run=read(run_path)
    validate_terminal(run)
    require(run['runtime_sha256'] == RUNTIME and run['game_code_sha256'] == DLL, 'Unexpected candidate pair')
    require(run['artifact_hashes_after_exit']['runtime'] == RUNTIME and
            run['artifact_hashes_after_exit']['game_code'] == DLL, 'Artifact changed during game run')
    require(sha(private_path(run['runtime_path'])) == RUNTIME and
            sha(private_path(Path(run['game_directory'])/'ACNH_1_0_0_code.dll')) == DLL,
            'Current candidate artifacts differ')
    preflight_path=OWN/'preflight.json'
    preflight=read(preflight_path)
    require(preflight['lease']['lease_id'] == run['timing_lock']['lease_id'], 'Preflight/run lease differs')
    for name, expected in preflight['files'].items():
        require(direct_sha(ROOT/name) == expected, 'Preflight file drift: '+name)
    require(preflight['lease']['runtime_sha256'] == RUNTIME and
            preflight['lease']['game_code_sha256'] == DLL, 'Preflight candidate pair differs')
    old_romfs_preflight=read(private_path(preflight['romfs_hash_reused_from']))
    old_romfs=old_romfs_preflight['files']['private/windows/bridge/ACNH_1_0_0_data/romfs.bin']
    romfs_path=PRIVATE/'windows/bridge/ACNH_1_0_0_data/romfs.bin'
    romfs_stat=romfs_path.stat()
    require(preflight['romfs_size_and_mtime_unchanged'] is True and
            preflight['romfs_sha256'] == old_romfs['sha256'] and
            romfs_stat.st_size == old_romfs['size'] and romfs_stat.st_mtime_ns == old_romfs['mtime_ns'],
            'Reused ROMFS hash/size/mtime binding differs')
    for name in ('audio','vp9','renderdoc'):
        backend=run['backends']
        require(sha(private_path(backend[name+'_path'])) == backend[name+'_sha256'] ==
                run['artifact_hashes_after_exit'][name], 'Backend hash differs: '+name)
    require(direct_sha(ROOT/'scripts/inspect_bridge_audio.py') == run['audio_analysis_process']['script_sha256'],
            'Audio analyser source differs')
    require(direct_sha(private_path(run['audio_analysis_process']['path'])) == run['audio_analysis_process']['sha256'],
            'Audio analyser executable differs')
    ledger=snapshots_and_gates(preflight, OWN/'coverage-coordinator.json',run['terminal_observed_utc'])
    current_logs=logs(run)
    require(current_logs['rendered_frames'] == 1980, 'Expected recorded1980 frame summary')
    audio=audio_evidence(run,recompute=True,raw_required=True)
    require(audio['nonzero_samples'] > 0, 'No startup PCM signal')
    all_captures=[]
    for name in run['screenshots']:
        capture,_=ppm_capture(name); all_captures.append(capture)
    require(len({c['private_path'] for c in all_captures}) == len(all_captures), 'Duplicate screenshot paths')
    capture,rgb=ppm_capture(ppm_path)
    require(relative(ppm_path) in {c['private_path'] for c in all_captures}, 'Observed capture is outside run')
    import PIL
    from PIL import Image
    with Image.open(png_path) as im:
        require(im.size == (capture['width'],capture['height']) and im.convert('RGB').tobytes() == rgb,
                'Inspected PNG is not the exact lossless PPM conversion')
    capture.update(inspected_png=binding(png_path), png_rgb_equals_ppm=True,
        observation=observation, observer=observer,
        semantic_label_source='Explicit visual inspection by attributed AI coordinator/reviewer; not automatic RGB/frame classification')
    baseline_summaries=[]
    frozen_epoch=read(ROOT/'metadata/windows/1.0.0/startup-epoch-team-validation.json')
    frozen_dispatch=read(ROOT/'metadata/windows/1.0.0/startup-dispatch-validation.json')
    for prefix,entries,label,assessment in BASELINES:
        p=ROOT/'private/windows/logs'/(prefix+'.json'); b=read(p)
        rich='flags' in b
        validate_terminal(b,rich)
        require(controls(b,rich) == controls(run,True), 'Recorded control mismatch: '+prefix)
        ba=audio_evidence(b,raw_required=rich); bl=logs(b)
        if rich:
            require(sha(p) == frozen_epoch['run_report_sha256'], 'Frozen epoch terminal report differs')
            require(b['backends']['audio_sha256'] == run['backends']['audio_sha256'] and
                    b['backends']['vp9_sha256'] == run['backends']['vp9_sha256'] and
                    b['backends']['renderdoc_sha256'] == run['backends']['renderdoc_sha256'],
                    'Epoch comparison backend hashes differ')
        else:
            published=next(x for x in frozen_dispatch['runs'] if x['run']==prefix)
            require(sha(p) == published['provenance']['terminal_report'] and
                    sha(private_path(b['audio_analysis'])) == published['provenance']['audio_report'],
                    'Frozen legacy comparison reports differ')
            require(b['audio_backend_sha256'] == run['backends']['audio_sha256'] and
                    b['vp9_backend_sha256'] == run['backends']['vp9_sha256'], 'Legacy audio/VP9 backends differ')
        baseline_summaries.append(dict(run=prefix, entries=entries, evidence=binding(p),
            runtime_sha256=b['runtime_sha256'], module_sha256=b['game_code_sha256'],
            exit_code=b['process_exit_code'] if rich else b['exit_code'],
            recorded_elapsed_seconds=b['process_elapsed_seconds'] if rich else b['elapsed_seconds'],
            elapsed_field_source='process_elapsed_seconds' if rich else 'legacy elapsed_seconds',
            rich_terminal_handle_evidence=rich, recorded_common_controls=controls(b,rich),
            logs=bl,audio=ba, visual_result=label,visual_assessment=assessment,
            limitations=[] if rich else ['Legacy report records exit/elapsed rather than terminal handles, PID-absence and cleanup.',
                'Legacy report omits requested seconds and RenderDoc binary hash; shared recorded controls are compared.']))
    starting=read(ROOT/'private/team/player35-integration/starting-snapshot.json')
    preserved={s:h for s,h in starting['source_and_report_hashes'].items()
               if s.startswith('metadata/windows/1.0.0/')}
    preserved['scripts/report_team_epoch_startup.py']=FROZEN_EPOCH_REPORTER
    preserved['metadata/windows/1.0.0/startup-epoch-team-validation.json']=FROZEN_EPOCH_REPORT
    for s,h in preserved.items():
        require(direct_sha(ROOT/s) == h, 'Frozen public14 evidence changed: '+s)
    require(direct_sha(ROOT/'private/windows/bridge/ACNH_1_0_0_code.dll') == DEFAULT_DLL and
            direct_sha(ROOT/'build/windows-bridge/vulkan/scarletnx.exe') == DEFAULT_RUNTIME, 'Default artifact changed')
    result=dict(schema_version=1,component='Coordinator player35 real-startup technical milestone',passed=True,
        technical_acceptance_recommended=True,coordinator_acceptance_pending=True,
        result='The integrated35 candidate reached the initial Timmy/Tommy dialogue with nonzero PCM in one naturally completed Windows startup run.',
        execution_kind='Hybrid native module with reconstructed entries and retained original translated/interpreted dependencies',
        terminal=dict(private_report=relative(run_path),report_sha256=sha(run_path),process_id=run['process_id'],
            requested_seconds=180,process_elapsed_seconds=run['process_elapsed_seconds'],harness_elapsed_seconds=run['elapsed_seconds'],
            terminal_state='natural-exit',process_exit_code=0,harness_exit_code=0,process_absent_confirmed=True,
            auxiliary_process_absent_confirmed=True,forced_termination=False,cleanup_confirmed=True),
        runtime_sha256=RUNTIME,module_sha256=DLL,backend_hashes=run['artifact_hashes_after_exit'],
        logs=current_logs,audio=audio,visual_observation=capture,captures=all_captures,
        preflight=binding(preflight_path),romfs=dict(sha256=preflight['romfs_sha256'],
            fresh_hash_in_this_run=False,reused_from=relative(private_path(preflight['romfs_hash_reused_from'])),
            size_and_mtime_unchanged=preflight['romfs_size_and_mtime_unchanged']),
        integrated_candidate_proof=ledger,comparison=baseline_summaries,recorded_common_controls=controls(run,True),
        coverage=dict(candidate_entries=35,candidate_original_body_bytes=4696,denominator_bytes=44815680,
            candidate_proxy_percent=100*4696/44815680,candidate_increment_entries=21,candidate_increment_original_body_bytes=2484,
            infrastructure_increment_bytes=0,public_entries=14,public_original_body_bytes=2212,public_metric_increment=0),
        public14_preserved_hashes=preserved,default_module_sha256=DEFAULT_DLL,default_runtime_sha256=DEFAULT_RUNTIME,
        candidate_run_count=1,default_promoted=False,public_coverage_promoted=False,publication_performed=False,
        playable_validated=False,gameplay_validated=False,tutorial_complete=False,save_reload_validated=False,
        source_sha256=direct_sha(Path(__file__)), limitations=[
            'Single 180-second startup run; repeated stability and affected gameplay are not validated.',
            'Provider/runtime/player selection differs across pairs; this comparison does not isolate performance causality.',
            'Frame count does not establish correctness, speed or perceptual graphical accuracy; backend warnings remain.',
            'Actual calls/hit counts for all 35 entries and the epoch API during gameplay were not instrumented by this startup.',
            'Visual dialogue label is explicit AI coordinator/reviewer inspection bound to a lossless private capture.',
            'Empty live-input files provide no input interaction/gameplay proof.',
            'Nonzero PCM and zero clipping do not establish perceptual audio correctness.',
            'ROMFS digest is reused from the earlier preflight after size/mtime check, not freshly hashed for this run.',
            'Historical build reused 376 hashed donor objects; no clean whole-game or cross-machine reproducibility claim.',
            'Original SDK/SaveIO model distinctions in module gates and hybrid dependencies remain.',
            'Save/reload, tutorial/gameplay, complete native reconstruction and the overall goal remain unfinished.'])
    result['verification_runtime']=dict(python_executable_sha256=direct_sha(Path(sys.executable)),
        python_version=sys.version.split()[0],pillow_version=PIL.__version__,
        use='Offline aggregate verification; not part of the game/runtime build')
    return result


def main():
    began=datetime.now(timezone.utc).isoformat()
    began_monotonic=time.monotonic()
    p=argparse.ArgumentParser()
    p.add_argument('--run',type=Path,default=Path('private/windows/logs/player35-team-20261013-203659.json'))
    p.add_argument('--dialogue-ppm',type=Path,default=Path('private/windows/logs/player35-team-20261013-203659_0072.ppm'))
    p.add_argument('--dialogue-png',type=Path,default=Path('private/team/player35-startup/player35-team-20261013-203659_0072.png'))
    p.add_argument('--visual-observation',required=True)
    p.add_argument('--observer',required=True)
    p.add_argument('--report',type=Path,default=PUBLIC)
    p.add_argument('--private-report',type=Path,default=OWN/'acceptance-validation.json')
    a=p.parse_args()
    run,ppm,png=map(private_path,(a.run,a.dialogue_ppm,a.dialogue_png))
    destination=(ROOT/a.report).resolve(); private_destination=private_path(a.private_report)
    require(destination == PUBLIC.resolve() or (destination.parent == OWN.resolve() and
            destination.name.startswith('acceptance') and destination.suffix=='.json'), 'Output outside assigned ownership')
    require(private_destination.parent==OWN.resolve() and private_destination.name.startswith('acceptance') and
            private_destination.suffix=='.json','Private output outside assigned ownership')
    result=aggregate(run,ppm,png,a.visual_observation,a.observer)
    rendered=json.dumps(result,indent=2)+'\n'
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(rendered,encoding='utf-8')
    private_destination.write_text(rendered,encoding='utf-8')
    execution=dict(started_utc=began,completed_utc=datetime.now(timezone.utc).isoformat(),
        elapsed_seconds=time.monotonic()-began_monotonic,
        argv=[sys.executable,'-B',*sys.argv],verification_runtime=result['verification_runtime'],
        source_sha256=result['source_sha256'],report_sha256=direct_sha(destination),
        public_report=relative(destination),private_report=relative(private_destination),
        game_launched=False,compiler_executed=False,defaults_changed=False)
    (OWN/'acceptance-execution.json').write_text(json.dumps(execution,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,report=relative(destination),sha256=direct_sha(destination),
        frames=result['logs']['rendered_frames'],nonzero_pcm_samples=result['audio']['nonzero_samples'],
        candidate_entries=35,candidate_bytes=4696,public_entries=14,public_bytes=2212,public_metric_increment=0)))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        failure=dict(passed=False,utc=datetime.now(timezone.utc).isoformat(),
            source_sha256=direct_sha(Path(__file__)),argv=[sys.executable,'-B',*sys.argv],
            error_type=type(error).__name__,error=str(error),
            existing_aggregate_not_replaced=True,game_launched=False,default_promoted=False)
        OWN.mkdir(parents=True,exist_ok=True)
        (OWN/('acceptance-failure-'+stamp+'.json')).write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8')
        raise
