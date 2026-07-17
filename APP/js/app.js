(function (root) {
  "use strict";

  const Q = root.QSOLIMC;
  if (!Q || !Q.Composition || !Q.Visualization) {
    throw new Error("QSOL-IMC application scripts did not load in dependency order");
  }

  const document = root.document;
  const form = document.getElementById("config-form");
  const elements = {
    tempo: document.getElementById("tempo"),
    tempoOutput: document.getElementById("tempo-output"),
    tuning: document.getElementById("tuning"),
    tuningOutput: document.getElementById("tuning-output"),
    peak: document.getElementById("peak"),
    peakOutput: document.getElementById("peak-output"),
    preflight: document.getElementById("preflight"),
    error: document.getElementById("form-error"),
    renderButton: document.getElementById("render-button"),
    resetButton: document.getElementById("reset-button"),
    statusPill: document.getElementById("status-pill"),
    renderStatus: document.getElementById("render-status"),
    progress: document.getElementById("progress-bar"),
    waveform: document.getElementById("waveform"),
    spectrum: document.getElementById("spectrum"),
    fallback: document.getElementById("canvas-fallback"),
    waveformTab: document.getElementById("waveform-tab"),
    spectrumTab: document.getElementById("spectrum-tab"),
    waveformPanel: document.getElementById("waveform-panel"),
    spectrumPanel: document.getElementById("spectrum-panel"),
    play: document.getElementById("play-button"),
    stop: document.getElementById("stop-button"),
    loop: document.getElementById("loop-playback"),
    position: document.getElementById("position"),
    duration: document.getElementById("duration"),
    metricFrames: document.getElementById("metric-frames"),
    metricPeak: document.getElementById("metric-peak"),
    metricRms: document.getElementById("metric-rms"),
    metricSize: document.getElementById("metric-size"),
    wavHash: document.getElementById("wav-hash"),
    manifestHash: document.getElementById("manifest-hash"),
    recipeHash: document.getElementById("recipe-hash"),
    fingerprintHash: document.getElementById("fingerprint-hash"),
    downloadWav: document.getElementById("download-wav"),
    downloadManifest: document.getElementById("download-manifest"),
    downloadRecipe: document.getElementById("download-recipe"),
    downloadFingerprint: document.getElementById("download-fingerprint")
  };

  let currentResult = null;
  let rendering = false;
  let audioContext = null;
  let decodedBuffer = null;
  let decodedHash = null;
  let sourceNode = null;
  let playStartedAt = 0;
  let positionAnimation = 0;
  let playbackGeneration = 0;
  let decoding = false;
  let resultStale = false;

  function rawFormConfig() {
    const checkedVoice = form.querySelector('input[name="voice"]:checked');
    return {
      voice: checkedVoice ? checkedVoice.value : "hybrid",
      seed: document.getElementById("seed").value,
      tempo: elements.tempo.value,
      bars: document.getElementById("bars").value,
      tuning: elements.tuning.value,
      sampleRate: document.getElementById("sample-rate").value,
      bitDepth: document.getElementById("bit-depth").value,
      peak: elements.peak.value
    };
  }

  function formatNumber(value, digits) {
    return new Intl.NumberFormat(undefined, {
      minimumFractionDigits: digits || 0,
      maximumFractionDigits: digits || 0
    }).format(value);
  }

  function formatTime(seconds) {
    const safe = Math.max(0, Number.isFinite(seconds) ? seconds : 0);
    const minutes = Math.floor(safe / 60);
    const remainder = safe - minutes * 60;
    return minutes + ":" + remainder.toFixed(3).padStart(6, "0");
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KiB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MiB";
  }

  function showError(error, action) {
    const message = error && error.message ? error.message : String(error);
    elements.error.textContent = message;
    elements.error.hidden = false;
    elements.statusPill.textContent = "Error";
    elements.statusPill.dataset.state = "error";
    elements.renderStatus.textContent = (action || "Action") + " stopped: " + message;
  }

  function clearError() {
    elements.error.hidden = true;
    elements.error.textContent = "";
  }

  function updateReadouts() {
    elements.tempoOutput.value = elements.tempo.value + " BPM";
    elements.tempoOutput.textContent = elements.tempo.value + " BPM";
    const tuningText = Number(elements.tuning.value).toFixed(2) + " Hz";
    elements.tuningOutput.value = tuningText;
    elements.tuningOutput.textContent = tuningText;
    const peakText = Number(elements.peak.value).toFixed(1).replace("-", "−") + " dBFS";
    elements.peakOutput.value = peakText;
    elements.peakOutput.textContent = peakText;
    try {
      const config = Q.Composition.normalizeConfig(rawFormConfig());
      elements.preflight.textContent = config.durationSeconds.toFixed(2) + " s · " + formatNumber(config.frameCount) + " frames";
      clearError();
      if (!rendering) {
        if (currentResult && resultStale) {
          elements.statusPill.textContent = "Needs render";
          elements.statusPill.dataset.state = "idle";
          elements.renderStatus.textContent = "Settings changed. Render again to create a matching artifact snapshot.";
        } else if (!currentResult) {
          elements.statusPill.textContent = "Ready";
          elements.statusPill.dataset.state = "idle";
          elements.renderStatus.textContent = "Ready to render locally.";
        }
      }
    } catch (error) {
      elements.preflight.textContent = "Correct the highlighted contract";
      showError(error, "Configuration");
    }
  }

  function setFormBusy(busy) {
    rendering = busy;
    elements.renderButton.disabled = busy;
    elements.renderButton.querySelector("span").textContent = busy ? "Rendering locally…" : "Render offline loop";
    const controls = form.querySelectorAll("input, select, button");
    controls.forEach(function toggle(control) {
      if (control !== elements.renderButton) control.disabled = busy;
    });
    updateOutputAvailability();
  }

  function updateOutputAvailability() {
    const unavailable = rendering || !currentResult || resultStale;
    elements.play.disabled = unavailable || decoding;
    elements.stop.disabled = unavailable;
    elements.loop.disabled = rendering;
    [elements.downloadWav, elements.downloadManifest, elements.downloadRecipe, elements.downloadFingerprint]
      .forEach(function toggle(button) { button.disabled = unavailable; });
  }

  function updateProgress(event) {
    let percent = 0;
    if (event.stage === "synthesis") percent = event.total ? 8 + 78 * event.completed / event.total : 8;
    else if (event.stage === "master") percent = 90;
    else if (event.stage === "provenance") percent = 96;
    else if (event.stage === "complete") percent = 100;
    elements.progress.style.width = Math.max(0, Math.min(100, percent)).toFixed(1) + "%";
    elements.renderStatus.textContent = event.label + ".";
  }

  function updateResult(result) {
    // Invalidate a decode/play operation that began against the previous
    // artifact before publishing this immutable render snapshot.
    stopPlayback();
    currentResult = result;
    resultStale = false;
    decodedBuffer = null;
    decodedHash = null;
    try {
      Q.Visualization.drawWaveform(elements.waveform, result.audio.left, result.audio.right);
      Q.Visualization.drawSpectrum(elements.spectrum, result.audio.left, result.audio.right, result.config.sampleRate);
      elements.fallback.hidden = true;
    } catch (visualError) {
      elements.fallback.textContent = "Audio rendered successfully; canvas inspection is unavailable in this browser.";
      elements.fallback.hidden = false;
    }
    elements.duration.textContent = formatTime(result.config.durationSeconds);
    elements.position.textContent = formatTime(0);
    elements.metricFrames.textContent = formatNumber(result.config.frameCount);
    elements.metricPeak.textContent = (20 * Math.log10(Math.max(1e-12, result.fingerprint.peak))).toFixed(2) + " dBFS";
    elements.metricRms.textContent = (20 * Math.log10(Math.max(1e-12, result.fingerprint.rms))).toFixed(2) + " dBFS";
    elements.metricSize.textContent = formatBytes(result.wavBytes.length);
    elements.wavHash.textContent = result.fingerprint.wav_sha256;
    elements.manifestHash.textContent = result.manifest.manifest_core_sha256;
    elements.recipeHash.textContent = result.manifest.recipe_sha256;
    elements.fingerprintHash.textContent = result.fingerprint.fingerprint_sha256;
    elements.statusPill.textContent = "Complete";
    elements.statusPill.dataset.state = "done";
    elements.renderStatus.textContent = "Offline render complete. Exact WAV and JSON receipts are ready.";
  }

  async function render(event) {
    event.preventDefault();
    if (rendering) return;
    stopPlayback();
    clearError();
    let config;
    try {
      config = Q.Composition.normalizeConfig(rawFormConfig());
    } catch (error) {
      showError(error, "Render");
      return;
    }
    setFormBusy(true);
    elements.statusPill.textContent = "Working";
    elements.statusPill.dataset.state = "working";
    elements.progress.style.width = "2%";
    try {
      await new Promise(function nextPaint(resolve) { root.requestAnimationFrame(resolve); });
      const result = await Q.Composition.renderLoop(config, updateProgress);
      updateResult(result);
    } catch (error) {
      showError(error);
      elements.progress.style.width = "0%";
    } finally {
      setFormBusy(false);
    }
  }

  function selectTab(name) {
    const waveform = name === "waveform";
    elements.waveformTab.setAttribute("aria-selected", String(waveform));
    elements.spectrumTab.setAttribute("aria-selected", String(!waveform));
    elements.waveformTab.tabIndex = waveform ? 0 : -1;
    elements.spectrumTab.tabIndex = waveform ? -1 : 0;
    elements.waveformPanel.hidden = !waveform;
    elements.spectrumPanel.hidden = waveform;
  }

  function tabKeydown(event) {
    const tabs = [elements.waveformTab, elements.spectrumTab];
    const current = tabs.indexOf(event.currentTarget);
    let next = current;
    if (event.key === "ArrowRight") next = (current + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (current - 1 + tabs.length) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault();
    selectTab(next === 0 ? "waveform" : "spectrum");
    tabs[next].focus();
  }

  function stopPlayback() {
    playbackGeneration += 1;
    decoding = false;
    if (sourceNode) {
      sourceNode.onended = null;
      try { sourceNode.stop(); } catch (_error) { /* already stopped */ }
      sourceNode.disconnect();
      sourceNode = null;
    }
    if (positionAnimation) root.cancelAnimationFrame(positionAnimation);
    positionAnimation = 0;
    elements.play.textContent = "▶";
    elements.play.setAttribute("aria-label", "Play rendered loop");
    elements.position.textContent = formatTime(0);
    updateOutputAvailability();
  }

  function updatePosition() {
    if (!sourceNode || !currentResult || !audioContext) return;
    const duration = currentResult.config.durationSeconds;
    const elapsed = Math.max(0, audioContext.currentTime - playStartedAt);
    const position = elements.loop.checked ? elapsed % duration : Math.min(elapsed, duration);
    elements.position.textContent = formatTime(position);
    positionAnimation = root.requestAnimationFrame(updatePosition);
  }

  async function play() {
    if (!currentResult) return;
    const result = currentResult;
    stopPlayback();
    const generation = playbackGeneration;
    const AudioContextClass = root.AudioContext || root.webkitAudioContext;
    if (!AudioContextClass) {
      showError(new Error("This browser does not expose the Web Audio API"), "Playback");
      return;
    }
    decoding = true;
    updateOutputAvailability();
    try {
      if (!audioContext) audioContext = new AudioContextClass();
      if (audioContext.state === "suspended") await audioContext.resume();
      let buffer = decodedHash === result.fingerprint.wav_sha256 ? decodedBuffer : null;
      if (!buffer) {
        const wavCopy = result.wavBytes.slice().buffer;
        buffer = await audioContext.decodeAudioData(wavCopy);
      }
      if (generation !== playbackGeneration || currentResult !== result) return;
      decodedBuffer = buffer;
      decodedHash = result.fingerprint.wav_sha256;
      const node = audioContext.createBufferSource();
      sourceNode = node;
      node.buffer = buffer;
      node.loop = elements.loop.checked;
      node.connect(audioContext.destination);
      node.onended = function ended() {
        if (sourceNode !== node || node.loop || generation !== playbackGeneration) return;
        stopPlayback();
      };
      playStartedAt = audioContext.currentTime;
      node.start();
      elements.play.textContent = "↻";
      elements.play.setAttribute("aria-label", "Restart rendered loop");
      updatePosition();
    } catch (error) {
      if (generation === playbackGeneration) {
        stopPlayback();
        showError(error, "Playback");
      }
    } finally {
      if (generation === playbackGeneration) {
        decoding = false;
        updateOutputAvailability();
      }
    }
  }

  function downloadBytes(bytes, type, filename) {
    const blob = new Blob([bytes], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.hidden = true;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    root.setTimeout(function release() { URL.revokeObjectURL(url); }, 30_000);
  }

  function artifactStem() {
    return "qsol-imc-" + currentResult.config.voiceMode + "-" + currentResult.fingerprint.wav_sha256.slice(0, 12);
  }

  function downloadJson(value, suffix) {
    downloadBytes(Q.Hash.canonicalBytes(value), "application/json;charset=utf-8", artifactStem() + suffix);
  }

  function configurationChanged() {
    if (currentResult && !rendering && !resultStale) {
      resultStale = true;
      stopPlayback();
      elements.progress.style.width = "0%";
    }
    updateReadouts();
    updateOutputAvailability();
  }

  form.addEventListener("submit", render);
  form.addEventListener("input", configurationChanged);
  form.addEventListener("change", configurationChanged);
  elements.resetButton.addEventListener("click", function reset() {
    form.reset();
    configurationChanged();
  });
  elements.waveformTab.addEventListener("click", function () { selectTab("waveform"); });
  elements.spectrumTab.addEventListener("click", function () { selectTab("spectrum"); });
  elements.waveformTab.addEventListener("keydown", tabKeydown);
  elements.spectrumTab.addEventListener("keydown", tabKeydown);
  elements.play.addEventListener("click", play);
  elements.stop.addEventListener("click", stopPlayback);
  elements.loop.addEventListener("change", function updateLooping() {
    if (sourceNode) sourceNode.loop = elements.loop.checked;
  });
  elements.downloadWav.addEventListener("click", function () {
    if (currentResult) downloadBytes(currentResult.wavBytes, "audio/wav", artifactStem() + ".wav");
  });
  elements.downloadManifest.addEventListener("click", function () {
    if (currentResult) downloadJson(currentResult.manifest, ".manifest.json");
  });
  elements.downloadRecipe.addEventListener("click", function () {
    if (currentResult) downloadJson(currentResult.recipe, ".recipe.json");
  });
  elements.downloadFingerprint.addEventListener("click", function () {
    if (currentResult) downloadJson(currentResult.fingerprint, ".fingerprint.json");
  });
  root.addEventListener("beforeunload", stopPlayback);

  updateReadouts();
  updateOutputAvailability();
})(globalThis);
