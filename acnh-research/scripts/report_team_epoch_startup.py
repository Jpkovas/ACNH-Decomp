"""Aggregate coordinator-observed startup; keep captures and game inputs private."""
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def private_path(path: Path) -> Path:
    path = (ROOT / path).resolve()
    path.relative_to((ROOT / 'private').resolve())
    return path


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--dialogue-ppm', type=Path, required=True)
    parser.add_argument('--intro-ppm', type=Path, required=True)
    parser.add_argument('--report', type=Path,
        default=Path('metadata/windows/1.0.0/startup-epoch-team-validation.json'))
    args = parser.parse_args()
    run_path = private_path(args.run)
    run = json.loads(run_path.read_text(encoding='utf-8-sig'))
    assert run['harness_terminal_complete'] and run['postprocessing_complete']
    assert run['terminal_state'] == 'natural-exit' and not run['forced_termination']
    assert run['process_exit_code'] == run['harness_exit_code'] == 0
    assert run['process_absent_confirmed'] and run['auxiliary_process_absent_confirmed']
    assert not run['errors'] and not run['postprocess_errors']
    assert run['environment_restored'] and run['timing_lock']['action'] == 'released-same-lease'
    audio_path = private_path(Path(run['audio_analysis']))
    audio = json.loads(audio_path.read_text(encoding='utf-8-sig'))
    assert audio['sha256'] == run['audio_wav_sha256']
    assert sum(x['nonzero_samples'] for x in audio['channel_metrics']) > 0
    assert run['audio_wav_raw'] and sha(private_path(Path(run['audio_wav_raw']))) == run['audio_wav_sha256_before_finalize']
    observations = []
    for label, source in [('introduction', args.intro_ppm), ('dialogue', args.dialogue_ppm)]:
        p = private_path(source)
        assert str(p) in run['screenshots']
        raw = p.read_bytes()
        magic, dimensions, maximum, rgb = raw.split(b'\n', 3)
        width, height = map(int, dimensions.split())
        assert magic == b'P6' and maximum == b'255' and len(rgb) == width * height * 3
        assert any(rgb)
        observations.append(dict(kind=label, private_capture=relative(p),
            sha256=hashlib.sha256(raw).hexdigest(), width=width, height=height,
            assessment='Coordinator visually inspected a lossless PNG conversion of this PPM.'))
    preflight_path = ROOT / 'private/team/epoch-startup/preflight.json'
    preflight = json.loads(preflight_path.read_text())
    for name, identity in [('runtime', 'runtime_sha256'), ('game_code', 'game_code_sha256')]:
        assert run['artifact_hashes_after_exit'][name] == run[identity]
    baseline_runs = []
    for prefix, entries in [('native-20261013-182810', 9), ('native-20261013-183257', 14)]:
        p = ROOT / 'private/windows/logs' / (prefix + '.json')
        b = json.loads(p.read_text(encoding='utf-8-sig'))
        controls = dict(headless=b['headless'], docked=b['docked'],
            input_script=b['input_script'], press_length_ms=b['press_length_ms'],
            shot_every_frames=b['shot_every_frames'], native_audio=b['native_audio'],
            native_vp9=b['native_vp9'], live_input=bool(b['live_input_file']),
            capture_filesystem=b['filesystem_capture'],
            capture_gpu_fifo=bool(b['gpu_fifo_capture']),
            capture_graphics=bool(b['graphics_capture_trigger']))
        assert all(run['flags'][k] == v for k, v in controls.items() if k != 'input_script')
        assert run['flags']['input_script'] == controls['input_script']
        assert b['audio_backend_sha256'] == run['backends']['audio_sha256']
        assert b['vp9_backend_sha256'] == run['backends']['vp9_sha256']
        baseline_runs.append(dict(run=prefix, entries=entries, private_report=relative(p),
            report_sha256=sha(p), runtime_sha256=b['runtime_sha256'],
            module_sha256=b['game_code_sha256'], exit_code=b['exit_code'],
            elapsed_seconds=b['elapsed_seconds'], common_controls=controls))
    result = dict(schema_version=1, passed=True,
        result='One coordinator-controlled epoch-v2 candidate reached the initial dialogue with nonzero PCM and exited naturally.',
        private_run_report=relative(run_path), run_report_sha256=sha(run_path),
        process_id=run['process_id'], requested_seconds=run['flags']['seconds'],
        process_elapsed_seconds=run['process_elapsed_seconds'],
        harness_elapsed_seconds=run['elapsed_seconds'],
        terminal_state=run['terminal_state'], process_exit_code=run['process_exit_code'],
        process_absent_confirmed=True, runtime_sha256=run['runtime_sha256'],
        module_sha256=run['game_code_sha256'], backend_hashes=run['artifact_hashes_after_exit'],
        audio=dict(private_report=relative(audio_path), report_sha256=sha(audio_path),
            duration_seconds=audio['duration_seconds'], channels=audio['channels'],
            pcm_frames=audio['pcm_frames'], channel_metrics=audio['channel_metrics'],
            wav_sha256=audio['sha256'], raw_wav_sha256=run['audio_wav_sha256_before_finalize']),
        visual_observations=observations, preflight_sha256=sha(preflight_path),
        romfs_sha256=preflight['files']['private/windows/bridge/ACNH_1_0_0_data/romfs.bin']['sha256'],
        comparison=baseline_runs, candidate_run_count=1,
        reconstructed_coverage=dict(entries=14, bytes=2212, denominator=44815680, increment=0),
        default_promoted=False, playable_validated=False, gameplay_validated=False,
        save_reload_validated=False, limitations=[
            'Single candidate run; repeated startup and affected gameplay remain pending.',
            'Candidate changes runtime/API and module provider together; this does not isolate a performance cause.',
            'Visual labels are explicit coordinator observations; hashes bind the inspected private captures.',
            'No input was applied beyond an empty normal live-input file.',
            'Nonzero PCM and zero clipping do not establish perceptual audio accuracy.',
            'Hybrid execution still includes original/translated/interpreted dependencies.',
            'Tutorial, real save/reload and completed native reconstruction remain unproved.'])
    destination = (ROOT / args.report).resolve()
    destination.relative_to((ROOT / 'metadata').resolve())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, report=relative(destination),
        terminal_state=result['terminal_state'], process_seconds=result['process_elapsed_seconds'],
        nonzero_samples=sum(x['nonzero_samples'] for x in audio['channel_metrics']),
        coverage_increment=0)))


if __name__ == '__main__':
    main()
