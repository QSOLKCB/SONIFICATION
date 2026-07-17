# QSOL-IMC Offline App

This directory is a zero-dependency browser edition of QSOL SONIFICATION. It
contains only local HTML, CSS, and classic JavaScript files.

## Run it

Open `index.html` directly in a current desktop browser. No server, install,
account, upload, network connection, service worker, or build step is required.

1. Select a voice and render settings.
2. Choose **Render offline loop**.
3. Listen locally or download the WAV and JSON receipts individually.

Browsers require playback to begin from a user action. If audio is silent,
check that the tab is allowed to play sound and press Play again.

## Self-tests

Open `tests/index.html` directly. The same suite can be run from the repository
root with:

```text
node APP/tests/run.cjs
node APP/tests/dom-smoke.cjs
```

## Determinism boundary

The app uses the browser-specific `qsol-imc.browser-float64/v1` ABI.
Equal inputs replay to equal WAV bytes inside the same app/runtime. It does not
claim byte identity with the Python/NumPy renderer or every JavaScript engine:
transcendental math and floating-point reduction details may differ. The seed,
event plan, DSP constants, quantization, hashing, and WAV layout remain explicit
and inspectable.

Playback is outside artifact identity because Web Audio may convert to float32
and resample to the audio device.

## Privacy and offline scope

The source contains no `fetch`, XMLHttpRequest, WebSocket, analytics, remote
font, CDN, or upload code. Audio and provenance are generated in memory. Files
leave the app only when the user presses a download button.

MIT licensed with the repository. Created by Trent Slade / QSOL-IMC.
