"""Extend the film's existing read-hold audio without building HTML or exporting video."""
import json
import subprocess
from array import array
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILM = ROOT / 'showcase/madden-curse'
RATE = 44100
CHANNELS = 2
BITRATE = '192k'


def configuration():
    module = (FILM / 'music-edit.mjs').as_uri()
    code = 'const {MUSIC_EDIT}=await import(' + json.dumps(module) + ');console.log(JSON.stringify(MUSIC_EDIT));'
    result = subprocess.run(['node', '--input-type=module', '-e', code], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def decode(path):
    result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 's16le', '-ar', str(RATE),
                             '-ac', str(CHANNELS), '-'], check=True, capture_output=True)
    samples = array('h')
    samples.frombytes(result.stdout)
    return samples


def extend(samples, edit):
    index = lambda seconds: round(seconds * RATE) * CHANNELS
    at, start = index(edit['at']), index(edit['from'])
    length, fade = index(edit['length']), round(edit['fade'] * RATE)
    if start < 0 or start + length > at or at > len(samples) or not fade:
        raise ValueError('Invalid music extension window')
    phrase = samples[start:start + length]
    output = samples[:at] + phrase * edit['repeats'] + samples[at:]
    for seam in range(edit['repeats'] + 1):
        boundary = at + seam * length
        for frame in range(fade):
            gain = frame / fade
            for channel in range(CHANNELS):
                right = boundary + frame * CHANNELS + channel
                left = boundary - (frame + 1) * CHANNELS + channel
                output[right] = round(output[right] * gain)
                output[left] = round(output[left] * gain)
    return output


def splice_ending(samples, ending, edit):
    at = round(edit['at'] * RATE)
    length = round(edit['length'] * RATE)
    overlap = round(edit['crossfade'] * RATE)
    fade = round(edit['fadeOut'] * RATE)
    if not (0 < overlap <= at and overlap < length and 1 < fade <= length
            and (at + overlap) * CHANNELS <= len(samples) and length * CHANNELS <= len(ending)):
        raise ValueError('Invalid music finale window')
    output = samples[:at * CHANNELS] + ending[:length * CHANNELS]
    for frame in range(overlap):
        gain = (frame + 1) / overlap
        for channel in range(CHANNELS):
            left = (at + frame) * CHANNELS + channel
            right = frame * CHANNELS + channel
            output[left] = round(samples[left] * (1 - gain) + ending[right] * gain)
    for frame in range(fade):
        gain = 1 - frame / (fade - 1)
        for channel in range(CHANNELS):
            index = (at + length - fade + frame) * CHANNELS + channel
            output[index] = round(output[index] * gain)
    return output


def main():
    config = configuration()
    samples = extend(decode(FILM / config['baseSource']), config['extension'])
    samples = splice_ending(samples, decode(FILM / config['finale']['source']), config['finale'])
    target = FILM / config['source']
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(RATE), '-ac', str(CHANNELS),
                    '-i', '-', '-c:a', 'libmp3lame', '-b:a', BITRATE, str(target)], input=samples.tobytes(), check=True)
    print(f'{target.name}: {len(samples) / CHANNELS / RATE:.3f}s; original closing passage begins at film 74.077s')


if __name__ == '__main__':
    main()
