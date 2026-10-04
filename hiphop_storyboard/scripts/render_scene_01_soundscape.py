#!/usr/bin/env python3
"""Render a short, original synthetic sound-design sketch for Scene 01.

No recordings or third-party samples are used. Run from any directory with:
    python3 render_scene_01_soundscape.py [optional-output.wav]
"""
from __future__ import annotations

import math
import random
import struct
import sys
import wave
from array import array
from pathlib import Path

SAMPLE_RATE = 22_050
DURATION = 18.0
FRAME_COUNT = int(SAMPLE_RATE * DURATION)
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "assets" / "scene_01_soundscape.wav"
OUT.parent.mkdir(parents=True, exist_ok=True)

left = array("f", [0.0]) * FRAME_COUNT
right = array("f", [0.0]) * FRAME_COUNT
random.seed(14594)


def pan_gains(pan: float) -> tuple[float, float]:
    angle = (max(-1.0, min(1.0, pan)) + 1.0) * math.pi / 4.0
    return math.cos(angle), math.sin(angle)


def envelope(t: float, start: float, end: float, attack: float = 0.025, release: float = 0.16) -> float:
    if t < start or t >= end:
        return 0.0
    fade_in = 1.0 if attack <= 0 else min(1.0, (t - start) / attack)
    fade_out = 1.0 if release <= 0 else min(1.0, (end - t) / release)
    # Short smooth fades avoid clicks while keeping the sound tactile.
    fade_in = fade_in * fade_in * (3.0 - 2.0 * fade_in)
    fade_out = fade_out * fade_out * (3.0 - 2.0 * fade_out)
    return max(0.0, min(fade_in, fade_out))


def add_tone(freq: float, start: float, end: float, amp: float, pan: float = 0.0,
             attack: float = 0.02, release: float = 0.15, phase: float = 0.0,
             vibrato: float = 0.0, vibrato_rate: float = 4.0) -> None:
    i0, i1 = max(0, int(start * SAMPLE_RATE)), min(FRAME_COUNT, int(end * SAMPLE_RATE))
    gl, gr = pan_gains(pan)
    for i in range(i0, i1):
        t = i / SAMPLE_RATE
        env = envelope(t, start, end, attack, release)
        wobble = 1.0 + vibrato * math.sin(2.0 * math.pi * vibrato_rate * t)
        s = math.sin(2.0 * math.pi * freq * wobble * (t - start) + phase) * amp * env
        left[i] += s * gl
        right[i] += s * gr


def add_filtered_noise(start: float, end: float, amp: float, pan: float = 0.0,
                       cutoff: float = 850.0, attack: float = 0.08, release: float = 0.2,
                       moving_pan: bool = False, highpass: float = 0.0) -> None:
    i0, i1 = max(0, int(start * SAMPLE_RATE)), min(FRAME_COUNT, int(end * SAMPLE_RATE))
    alpha = 1.0 - math.exp(-2.0 * math.pi * cutoff / SAMPLE_RATE)
    hp_alpha = 1.0 - math.exp(-2.0 * math.pi * highpass / SAMPLE_RATE) if highpass else 0.0
    low, hp_low = 0.0, 0.0
    for i in range(i0, i1):
        t = i / SAMPLE_RATE
        raw = random.uniform(-1.0, 1.0)
        low += alpha * (raw - low)
        sample = low
        if highpass:
            hp_low += hp_alpha * (raw - hp_low)
            sample = raw - hp_low
        env = envelope(t, start, end, attack, release)
        if moving_pan:
            progress = (t - start) / max(0.001, end - start)
            current_pan = pan + (progress * 2.0 - 1.0) * 0.78
        else:
            current_pan = pan
        gl, gr = pan_gains(current_pan)
        s = sample * amp * env
        left[i] += s * gl
        right[i] += s * gr


def add_click(at: float, strength: float = 0.24, pan: float = 0.0) -> None:
    """A tiny plastic switch click: sharp transient plus a short body resonance."""
    i0 = max(0, int(at * SAMPLE_RATE))
    length = int(0.105 * SAMPLE_RATE)
    gl, gr = pan_gains(pan)
    for j in range(length):
        i = i0 + j
        if i >= FRAME_COUNT:
            break
        t = j / SAMPLE_RATE
        decay = math.exp(-t * 58.0)
        noise = random.uniform(-1.0, 1.0) * decay * 0.34
        body = (math.sin(2 * math.pi * 730 * t) * 0.45 + math.sin(2 * math.pi * 1_480 * t) * 0.22) * decay
        s = (noise + body) * strength
        left[i] += s * gl
        right[i] += s * gr


def add_rail_clack(at: float, strength: float, pan: float) -> None:
    """Soft, irregular rail joint with a dry metal ring."""
    i0 = max(0, int(at * SAMPLE_RATE))
    length = int(0.21 * SAMPLE_RATE)
    gl, gr = pan_gains(pan)
    for j in range(length):
        i = i0 + j
        if i >= FRAME_COUNT:
            break
        t = j / SAMPLE_RATE
        decay = math.exp(-t * 21.0)
        attack = min(1.0, t * 2_500.0)
        noise = random.uniform(-1.0, 1.0) * 0.18
        ring = math.sin(2 * math.pi * 475 * t) * 0.55 + math.sin(2 * math.pi * 920 * t) * 0.22
        s = (noise + ring) * decay * attack * strength
        left[i] += s * gl
        right[i] += s * gr


def add_sweep(start: float, end: float, f0: float, f1: float, amp: float, pan: float = 0.0) -> None:
    i0, i1 = max(0, int(start * SAMPLE_RATE)), min(FRAME_COUNT, int(end * SAMPLE_RATE))
    gl, gr = pan_gains(pan)
    span = max(0.001, end - start)
    for i in range(i0, i1):
        t = i / SAMPLE_RATE
        p = (t - start) / span
        freq = f0 + (f1 - f0) * p
        phase = 2.0 * math.pi * (f0 * (t - start) + 0.5 * (f1 - f0) * (t - start) ** 2 / span)
        env = envelope(t, start, end, 0.35, 0.55)
        s = math.sin(phase) * amp * env * (0.8 + 0.2 * math.sin(2 * math.pi * 3.2 * t))
        left[i] += s * gl
        right[i] += s * gr


# Quiet station bed: transformer hum, fluorescent buzz, filtered room air.
add_tone(52.0, 0.0, 15.18, 0.022, attack=0.8, release=0.32, vibrato=0.018, vibrato_rate=0.7)
add_tone(104.0, 0.0, 15.18, 0.010, attack=0.8, release=0.32, phase=0.7, vibrato=0.015, vibrato_rate=0.7)
add_tone(60.0, 0.0, 15.18, 0.006, attack=0.5, release=0.35, phase=0.4)
add_filtered_noise(0.0, 15.16, 0.088, cutoff=170.0, attack=1.3, release=0.38)
add_filtered_noise(0.0, 15.12, 0.018, cutoff=3_800.0, highpass=750.0, attack=1.0, release=0.28)

# A train swells out of the tunnel and moves from left to right across the stereo field.
add_filtered_noise(4.45, 12.15, 0.29, pan=0.0, cutoff=1_150.0, attack=2.45, release=1.18, moving_pan=True)
add_filtered_noise(4.8, 11.95, 0.12, pan=0.0, cutoff=210.0, attack=2.4, release=1.35, moving_pan=True)
add_tone(47.0, 4.65, 12.0, 0.052, attack=2.5, release=1.3, vibrato=0.035, vibrato_rate=1.1)
add_tone(69.0, 4.9, 11.8, 0.031, attack=2.3, release=1.3, phase=1.0, vibrato=0.028, vibrato_rate=0.8)
add_sweep(6.25, 11.7, 580.0, 1_720.0, 0.021, pan=0.12)

# Irregular wheel-on-rail clacks peak as the train passes, not a pre-made beat.
for number, when in enumerate([5.85, 6.37, 6.91, 7.40, 7.95, 8.49, 9.00, 9.56, 10.09, 10.64, 11.20, 11.74]):
    add_rail_clack(when, 0.12 if number not in (4, 8) else 0.17, pan=-0.55 + number * 0.09)

# The tape motor becomes audible only after the REC button is pressed.
add_click(3.25, strength=0.42, pan=-0.08)
add_tone(113.0, 3.35, 14.94, 0.008, attack=0.05, release=0.13, vibrato=0.025, vibrato_rate=5.5)
add_filtered_noise(3.35, 14.94, 0.010, cutoff=5_500.0, highpass=1_800.0, attack=0.08, release=0.18)

# Stop the recorder at 15s; four sampled rail taps hint at the 92 BPM beat to come.
add_click(15.0, strength=0.55, pan=0.08)
for n, when in enumerate([15.62, 16.27, 16.92, 17.57]):
    add_rail_clack(when, 0.115, pan=(-0.45 if n < 2 else 0.45))

# Fade only the final 100 ms; the STOP click and four rhythmic sample taps stay clear.
for i in range(FRAME_COUNT):
    t = i / SAMPLE_RATE
    edge = min(1.0, max(0.0, (DURATION - t) / 0.12))
    left[i] *= edge
    right[i] *= edge

peak = max(max(abs(x) for x in left), max(abs(x) for x in right)) or 1.0
scale = 0.88 / peak

with wave.open(str(OUT), "wb") as wav:
    wav.setnchannels(2)
    wav.setsampwidth(2)
    wav.setframerate(SAMPLE_RATE)
    for l, r in zip(left, right):
        # Gentle saturation acts as a simple peak catcher while keeping transients.
        l = math.tanh(l * scale * 1.08) / math.tanh(1.08)
        r = math.tanh(r * scale * 1.08) / math.tanh(1.08)
        wav.writeframesraw(struct.pack("<hh", int(max(-1.0, min(1.0, l)) * 32767), int(max(-1.0, min(1.0, r)) * 32767)))

print(f"Wrote {OUT} ({DURATION:.2f}s, stereo, {SAMPLE_RATE} Hz)")
