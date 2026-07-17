(function (root) {
  "use strict";

  const Q = root.QSOLIMC = root.QSOLIMC || {};
  // Keeps the eight-bar default-tempo profile at the highest listed sample
  // rate available while bounding the app's synchronous pack/hash tail.
  const MAX_RENDER_FRAMES = 750_000;
  const MAX_EVENTS = 1024;
  const MAX_ESTIMATED_BYTES = 96 * 1024 * 1024;
  const BEATS_PER_BAR = 4;

  function decimalRational(value, name) {
    const text = String(value).trim();
    const match = /^(\d+)(?:\.(\d+))?$/.exec(text);
    if (!match) throw new TypeError(name + " must be a positive decimal number");
    const fraction = match[2] || "";
    const denominator = 10n ** BigInt(fraction.length);
    const numerator = BigInt(match[1] + fraction);
    if (numerator <= 0n) throw new RangeError(name + " must be positive");
    return { text, numerator, denominator, number: Number(text) };
  }

  function halfUpRatio(numerator, denominator) {
    if (numerator < 0n || denominator <= 0n) throw new RangeError("half-up ratio requires positive values");
    return (2n * numerator + denominator) / (2n * denominator);
  }

  function integerField(value, name, minimum, maximum) {
    const text = String(value).trim();
    if (!/^\d+$/.test(text)) throw new TypeError(name + " must be an integer");
    const parsed = Number(text);
    if (!Number.isSafeInteger(parsed) || parsed < minimum || parsed > maximum) {
      throw new RangeError(name + " must be in [" + minimum + ", " + maximum + "]");
    }
    return parsed;
  }

  function normalizeConfig(raw) {
    if (!raw || typeof raw !== "object") throw new TypeError("render configuration must be an object");
    const tempoSource = raw.tempoText !== undefined
      ? raw.tempoText
      : (raw.tempoBpm === undefined ? raw.tempo : raw.tempoBpm);
    const tuningSource = raw.tuningText !== undefined
      ? raw.tuningText
      : (raw.tuningA4Hz === undefined ? raw.tuning : raw.tuningA4Hz);
    const tempo = decimalRational(tempoSource, "tempo");
    const a4 = decimalRational(tuningSource, "A4 reference");
    const peak = Number(raw.peakDbfs === undefined ? raw.peak : raw.peakDbfs);
    const bars = integerField(raw.bars, "bars", 1, 16);
    const sampleRate = integerField(raw.sampleRate, "sample rate", 8000, 192000);
    const bitDepth = integerField(raw.bitDepth, "bit depth", 16, 24);
    const voiceMode = String(raw.voiceMode === undefined ? raw.voice : raw.voiceMode);
    const seed = Q.Math64.parseSeed(raw.seed);

    if (tempo.number < 20 || tempo.number > 400) throw new RangeError("tempo must be between 20 and 400 BPM");
    if (a4.number < 200 || a4.number > 1000) throw new RangeError("A4 reference must be between 200 and 1000 Hz");
    if (!Number.isFinite(peak) || peak < -24 || peak > -0.1) throw new RangeError("output peak must be between -24 and -0.1 dBFS");
    if (bitDepth !== 16 && bitDepth !== 24) throw new RangeError("bit depth must be 16 or 24");
    if (!["hybrid", "additive", "fm", "karplus"].includes(voiceMode)) {
      throw new RangeError("voice must be hybrid, additive, fm, or karplus");
    }

    const totalBeats = bars * BEATS_PER_BAR;
    const frameNumerator = BigInt(sampleRate * 60 * totalBeats) * tempo.denominator;
    const frameCountBig = halfUpRatio(frameNumerator, tempo.numerator);
    if (frameCountBig > BigInt(MAX_RENDER_FRAMES)) {
      throw new RangeError("render requires " + frameCountBig + " frames; browser limit is " + MAX_RENDER_FRAMES);
    }
    const frameCount = Number(frameCountBig);
    const estimatedBytes = frameCount * 60 + 4 * 1024 * 1024;
    if (estimatedBytes > MAX_ESTIMATED_BYTES) throw new RangeError("render exceeds the browser memory preflight budget");

    return Object.freeze({
      tempoBpm: tempo.number,
      tempoText: tempo.text,
      bars,
      beatsPerBar: BEATS_PER_BAR,
      totalBeats,
      sampleRate,
      bitDepth,
      tuningA4Hz: a4.number,
      tuningText: a4.text,
      seed,
      seedHex: Q.Math64.seedHex(seed),
      peakDbfs: peak,
      voiceMode,
      frameCount,
      durationSeconds: frameCount / sampleRate,
      estimatedBytes
    });
  }

  function eventsFromSteps(spec, totalBeats) {
    const events = [];
    const patternBeats = spec.steps.length * spec.stepBeats;
    const repeats = Math.ceil(totalBeats / patternBeats);
    for (let repeat = 0; repeat < repeats; repeat += 1) {
      for (let index = 0; index < spec.steps.length; index += 1) {
        const offset = spec.steps[index];
        if (offset === null) continue;
        const onset = repeat * patternBeats + index * spec.stepBeats;
        if (onset >= totalBeats) continue;
        events.push(Object.freeze({
          onset_beats: onset,
          duration_beats: spec.durationBeats,
          note: spec.rootNote + offset,
          velocity: spec.velocities[index % spec.velocities.length],
          pan: spec.pans[index % spec.pans.length],
          cents_offset: 0
        }));
      }
    }
    return Object.freeze(events);
  }

  function buildTracks(config) {
    const specs = {
      fm: {
        name: "phase-machine bass", instrument: "fm", gain: 0.82, seed_lane: 0x11,
        steps: [0, null, 0, 3, 0, null, 5, 7], rootNote: 33, stepBeats: 0.5, durationBeats: 0.44,
        velocities: [0.94, 0.66, 0.78, 0.70, 0.88, 0.62, 0.80, 0.74], pans: [-0.08, 0.04, 0.08, -0.04]
      },
      additive: {
        name: "harmonic glass", instrument: "additive", gain: 0.54, seed_lane: 0x22,
        steps: [0, 7, 3, 10], rootNote: 57, stepBeats: 1, durationBeats: 1.34,
        velocities: [0.66, 0.54, 0.61, 0.50], pans: [-0.52, 0.46, -0.24, 0.56]
      },
      karplus: {
        name: "deterministic wire", instrument: "karplus", gain: 0.63, seed_lane: 0x33,
        steps: [0, 7, null, 12, 10, null, 7, 3], rootNote: 45, stepBeats: 0.5, durationBeats: 0.70,
        velocities: [0.82, 0.58, 0.68, 0.76, 0.64, 0.56, 0.72, 0.61], pans: [0.36, -0.42, 0.24, -0.30]
      }
    };
    const names = config.voiceMode === "hybrid" ? ["fm", "additive", "karplus"] : [config.voiceMode];
    const tracks = names.map(function makeTrack(name) {
      const spec = specs[name];
      return Object.freeze({
        name: spec.name,
        instrument: spec.instrument,
        gain: spec.gain,
        seed_lane: spec.seed_lane,
        events: eventsFromSteps(spec, config.totalBeats)
      });
    });
    const eventCount = tracks.reduce(function sum(total, track) { return total + track.events.length; }, 0);
    if (eventCount > MAX_EVENTS) throw new RangeError("arrangement exceeds the browser event budget");
    return Object.freeze(tracks);
  }

  function noteFrequency(note, referenceHz) {
    return referenceHz * Math.pow(2, (note - 69) / 12);
  }

  function deriveSeed(seed, lane, eventIndex) {
    const component = (seed ^ (BigInt(lane) << 32n) ^ BigInt(eventIndex)) & Q.Math64.MASK64;
    return Q.Math64.splitmix64(component);
  }

  function beatToFrame(beat, totalBeats, frameCount) {
    return Math.floor(beat * frameCount / totalBeats + 0.5) % frameCount;
  }

  function addCircular(left, right, signal, onsetFrame, pan, gain) {
    const angle = (pan + 1) * Math.PI / 4;
    const leftGain = Math.cos(angle) * gain;
    const rightGain = Math.sin(angle) * gain;
    for (let offset = 0; offset < signal.length; offset += 1) {
      const frame = (onsetFrame + offset) % left.length;
      left[frame] += signal[offset] * leftGain;
      right[frame] += signal[offset] * rightGain;
    }
  }

  function identityTrack(track) {
    return {
      name: track.name,
      instrument: track.instrument,
      gain: track.gain,
      seed_lane: track.seed_lane,
      events: track.events.map(function cloneEvent(event) { return Object.assign({}, event); }),
      instrument_contract: Q.Synthesis.contracts[track.instrument]
    };
  }

  function recipeFor(config, tracks) {
    return Q.Provenance.buildRecipe({
      settings: {
        tempo_bpm: config.tempoBpm,
        bars: config.bars,
        beats_per_bar: config.beatsPerBar,
        total_beats: config.totalBeats,
        frame_count: config.frameCount,
        sample_rate: config.sampleRate,
        bit_depth: config.bitDepth,
        tuning_a4_hz: config.tuningA4Hz,
        seed: config.seedHex,
        peak_dbfs: config.peakDbfs,
        voice_mode: config.voiceMode,
        master: { algorithm: "rational-soft-clip/v1", drive: 1.15 },
        loop_tail_policy: "circular-fold/v1"
      },
      arrangement: tracks.map(identityTrack),
      metadata: {
        synthesis: "sample-free",
        hidden_entropy: false,
        seed_derivation: "splitmix64-xor-lane32/v1",
        quantizer: "symmetric-half-away-from-zero/v1",
        wav_writer: "riff-pcm-le/v1",
        playback_identity: false,
        mapping_boundary: "Phase 1 uses explicit musical step patterns; advanced mathematical mappings require separately versioned contracts."
      }
    });
  }

  function yieldControl() {
    return new Promise(function schedule(resolve) {
      if (typeof root.requestAnimationFrame === "function") root.requestAnimationFrame(function () { resolve(); });
      else if (typeof root.setTimeout === "function") root.setTimeout(resolve, 0);
      else resolve();
    });
  }

  async function renderLoop(rawConfig, progress) {
    // Never trust a caller-supplied derived frameCount. Normalizing again is
    // inexpensive and keeps every allocation behind the same range and memory
    // preflight, even for programmatic callers outside the form UI.
    const config = normalizeConfig(rawConfig);
    const tracks = buildTracks(config);
    const totalEvents = tracks.reduce(function sum(total, track) { return total + track.events.length; }, 0);
    const mixLeft = new Float64Array(config.frameCount);
    const mixRight = new Float64Array(config.frameCount);
    let completed = 0;
    const report = typeof progress === "function" ? progress : function () {};
    report({ stage: "synthesis", completed: 0, total: totalEvents, label: "Preparing deterministic event plan" });

    for (const track of tracks) {
      const trackLeft = new Float64Array(config.frameCount);
      const trackRight = new Float64Array(config.frameCount);
      for (let eventIndex = 0; eventIndex < track.events.length; eventIndex += 1) {
        const event = track.events[eventIndex];
        const signal = Q.Synthesis.synthesize(track.instrument, {
          frequencyHz: noteFrequency(event.note + event.cents_offset / 100, config.tuningA4Hz),
          durationSeconds: event.duration_beats * 60 / config.tempoBpm,
          velocity: event.velocity,
          sampleRate: config.sampleRate,
          seed: deriveSeed(config.seed, track.seed_lane, eventIndex)
        });
        addCircular(
          trackLeft,
          trackRight,
          signal,
          beatToFrame(event.onset_beats, config.totalBeats, config.frameCount),
          event.pan,
          track.gain
        );
        completed += 1;
        report({ stage: "synthesis", completed, total: totalEvents, label: "Rendering " + track.name });
        if (completed % 4 === 0) await yieldControl();
      }
      for (let frame = 0; frame < config.frameCount; frame += 1) {
        mixLeft[frame] += trackLeft[frame];
        mixRight[frame] += trackRight[frame];
      }
      await yieldControl();
    }

    report({ stage: "master", completed: totalEvents, total: totalEvents, label: "Mastering and packing PCM" });
    const mixed = { left: mixLeft, right: mixRight, sampleRate: config.sampleRate };
    const audio = Q.Audio.normalizePeak(Q.Audio.softClip(mixed, 1.15), config.peakDbfs);
    const encoded = Q.Audio.encodeWav(audio, config.bitDepth);
    const recipe = recipeFor(config, tracks);
    report({ stage: "provenance", completed: totalEvents, total: totalEvents, label: "Hashing local artifact receipt" });
    const fingerprint = Q.Provenance.buildFingerprint({
      pcm: encoded.pcm,
      pcmBytes: encoded.pcmBytes,
      wavBytes: encoded.wavBytes,
      sampleRate: encoded.sampleRate,
      bitDepth: encoded.bitDepth,
      channels: encoded.channels
    });
    const manifest = Q.Provenance.buildManifest({
      applicationVersion: Q.VERSION,
      recipe,
      fingerprint,
      lineage: [{
        relationship: "architectural-lineage",
        project: "QSOLKCB/SPECTRAL",
        note: "Domain-separated provenance and explicit claim boundaries are adapted from SPECTRAL; this is a browser-native music-first implementation."
      }]
    });
    Q.Provenance.validateManifest(manifest);
    report({ stage: "complete", completed: totalEvents, total: totalEvents, label: "Offline render complete" });
    return Object.freeze({
      config,
      tracks,
      audio,
      pcm: encoded.pcm,
      pcmBytes: encoded.pcmBytes,
      wavBytes: encoded.wavBytes,
      recipe,
      fingerprint,
      manifest
    });
  }

  Q.Composition = Object.freeze({
    MAX_RENDER_FRAMES,
    MAX_EVENTS,
    normalizeConfig,
    buildTracks,
    deriveSeed,
    addCircular,
    renderLoop
  });
})(globalThis);
