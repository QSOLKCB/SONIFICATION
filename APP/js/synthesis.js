(function (root) {
  "use strict";

  const Q = root.QSOLIMC = root.QSOLIMC || {};
  const TAU = Math.PI * 2;
  const MAX_NOTE_SAMPLES = 4_000_000;
  const MAX_FM_INTERNAL_SAMPLES = 8_000_000;
  const ADDITIVE_RATIOS = Object.freeze([1, 2, 3, 4, 5, 6, 8]);
  const ADDITIVE_AMPLITUDES = Object.freeze([1, 0.46, 0.31, 0.19, 0.13, 0.09, 0.055]);

  function assertRequest(options) {
    const frequencyHz = Number(options.frequencyHz);
    const durationSeconds = Number(options.durationSeconds);
    const velocity = Number(options.velocity);
    const sampleRate = Number(options.sampleRate);
    const seed = options.seed;
    if (!Number.isFinite(frequencyHz) || frequencyHz <= 0) {
      throw new RangeError("frequencyHz must be finite and positive");
    }
    if (!Number.isFinite(durationSeconds) || durationSeconds <= 0 || durationSeconds > 30) {
      throw new RangeError("durationSeconds must be in (0, 30]");
    }
    if (!Number.isFinite(velocity) || velocity < 0 || velocity > 1) {
      throw new RangeError("velocity must be in [0, 1]");
    }
    if (!Number.isInteger(sampleRate) || sampleRate < 8000 || sampleRate > 192000) {
      throw new RangeError("sampleRate must be an integer in [8000, 192000]");
    }
    if (typeof seed !== "bigint" || seed < 0n || seed > Q.Math64.MASK64) {
      throw new TypeError("seed must be an unsigned 64-bit bigint");
    }
    const gateSamples = Math.max(1, Math.round(durationSeconds * sampleRate));
    return { frequencyHz, durationSeconds, velocity, sampleRate, seed, gateSamples };
  }

  function envelope(gateSamples, sampleRate, settings) {
    const attack = Math.max(1, Math.round(settings.attack * sampleRate));
    const decay = Math.max(1, Math.round(settings.decay * sampleRate));
    const release = Math.max(1, Math.round(settings.release * sampleRate));
    const sustain = settings.sustain;
    const curve = settings.curve || 1;
    const total = gateSamples + release;
    if (total > MAX_NOTE_SAMPLES) {
      throw new RangeError("note exceeds the browser sample budget");
    }
    const values = new Float64Array(total);
    for (let index = 0; index < gateSamples; index += 1) {
      let level;
      if (index < attack) {
        level = Math.pow(index / attack, curve);
      } else if (index < attack + decay) {
        const position = (index - attack) / decay;
        level = 1 - (1 - sustain) * Math.pow(position, curve);
      } else {
        level = sustain;
      }
      values[index] = level;
    }
    const releaseStart = gateSamples > 0 ? values[gateSamples - 1] : sustain;
    for (let index = 0; index < release; index += 1) {
      const position = (index + 1) / release;
      values[gateSamples + index] = releaseStart * Math.pow(1 - position, curve);
    }
    values[0] = 0;
    values[values.length - 1] = 0;
    return values;
  }

  function randomUnit(seed, lane) {
    return Q.Math64.uint64ToUnit(Q.Math64.splitmix64At(seed, BigInt(lane)));
  }

  function phase(seed, lane) {
    return TAU * randomUnit(seed, lane);
  }

  function additive(options) {
    const request = assertRequest(options);
    const contour = envelope(request.gateSamples, request.sampleRate, {
      attack: 0.008,
      decay: 0.16,
      sustain: 0.58,
      release: 0.28,
      curve: 1.65
    });
    const output = new Float64Array(contour.length);
    if (request.velocity === 0) return output;

    const safeLimit = request.sampleRate * 0.47;
    let retainedWeight = 0;
    for (let partial = 0; partial < ADDITIVE_RATIOS.length; partial += 1) {
      if (request.frequencyHz * ADDITIVE_RATIOS[partial] < safeLimit) retainedWeight += Math.abs(ADDITIVE_AMPLITUDES[partial]);
    }
    if (retainedWeight === 0) return output;

    for (let index = 0; index < output.length; index += 1) {
      const time = index / request.sampleRate;
      let sample = 0;
      for (let partial = 0; partial < ADDITIVE_RATIOS.length; partial += 1) {
        const frequency = request.frequencyHz * ADDITIVE_RATIOS[partial];
        if (frequency >= safeLimit) continue;
        sample += ADDITIVE_AMPLITUDES[partial] * Math.sin(TAU * frequency * time + phase(request.seed, partial));
      }
      output[index] = sample * contour[index] * request.velocity / retainedWeight;
    }
    return output;
  }

  function fm(options) {
    const request = assertRequest(options);
    const oversample = 2;
    const targetContour = envelope(request.gateSamples, request.sampleRate, {
      attack: 0.004,
      decay: 0.14,
      sustain: 0.62,
      release: 0.22,
      curve: 1.8
    });
    const targetCount = targetContour.length;
    if (targetCount * oversample > MAX_FM_INTERNAL_SAMPLES) {
      throw new RangeError("FM note exceeds the oversampled browser budget");
    }
    const output = new Float64Array(targetCount);
    if (request.velocity === 0) return output;

    const internalRate = request.sampleRate * oversample;
    const internalGate = request.gateSamples * oversample;
    const contour = envelope(internalGate, internalRate, {
      attack: 0.004,
      decay: 0.14,
      sustain: 0.62,
      release: 0.22,
      curve: 1.8
    });
    const internal = new Float64Array(contour.length);
    const carrierFrequency = request.frequencyHz;
    const modulatorFrequency = request.frequencyHz * 2;
    const internalLimit = internalRate * 0.45;
    const maximumIndex = Math.max(0, (internalLimit - carrierFrequency) / modulatorFrequency);
    const boundedIndex = Math.min(2.35, maximumIndex);
    const carrierPhase = phase(request.seed, 0);
    const modulatorPhase = phase(request.seed, 1);

    for (let index = 0; index < internal.length; index += 1) {
      const time = index / internalRate;
      const env = contour[index];
      const indexContour = boundedIndex * (0.32 + 0.68 * Math.sqrt(Math.max(0, env)));
      const modulator = Math.sin(TAU * modulatorFrequency * time + modulatorPhase);
      internal[index] = request.velocity * env * Math.sin(
        TAU * carrierFrequency * time + carrierPhase + indexContour * modulator
      );
    }

    for (let index = 0; index < targetCount; index += 1) {
      const center = index * oversample;
      const previous = internal[Math.max(0, center - 1)];
      const current = internal[center];
      const next = internal[Math.min(internal.length - 1, center + 1)];
      output[index] = Math.max(-request.velocity, Math.min(request.velocity, 0.25 * previous + 0.5 * current + 0.25 * next));
    }
    output[0] = 0;
    output[output.length - 1] = 0;
    return output;
  }

  function karplus(options) {
    const request = assertRequest(options);
    const contour = envelope(request.gateSamples, request.sampleRate, {
      attack: 0.001,
      decay: 0.04,
      sustain: 0.78,
      release: 0.42,
      curve: 1.55
    });
    const output = new Float64Array(contour.length);
    if (request.velocity === 0) return output;

    const brightness = 0.62;
    const feedback = 0.996;
    const filterDelay = 0.5 * (1 - brightness);
    const delaySamples = request.sampleRate / request.frequencyHz - filterDelay;
    if (!Number.isFinite(delaySamples) || delaySamples < 2 || delaySamples > 1_000_000) {
      throw new RangeError("frequency produces an unsupported Karplus delay");
    }
    const initialCount = Math.min(output.length, Math.max(2, Math.ceil(delaySamples)));
    const excitation = new Float64Array(initialCount);
    let mean = 0;
    for (let index = 0; index < initialCount; index += 1) {
      const unit = randomUnit(request.seed, index);
      excitation[index] = unit * 2 - 1;
      mean += excitation[index];
    }
    mean /= initialCount;

    const pickDelay = Math.max(1, Math.round(0.19 * delaySamples));
    const tonePhase = phase(request.seed, 7);
    let peak = 0;
    for (let index = 0; index < initialCount; index += 1) {
      const noise = excitation[index] - mean;
      const shifted = excitation[(index - pickDelay % initialCount + initialCount) % initialCount] - mean;
      const combed = noise - 0.72 * shifted;
      const tone = Math.sin(TAU * request.frequencyHz * index / request.sampleRate + tonePhase);
      excitation[index] = 0.84 * combed + 0.16 * tone;
      peak = Math.max(peak, Math.abs(excitation[index]));
    }
    if (peak > 0) {
      for (let index = 0; index < initialCount; index += 1) output[index] = excitation[index] / peak;
    }

    let previousDelayed = 0;
    for (let index = initialCount; index < output.length; index += 1) {
      const position = index - delaySamples;
      const lower = Math.floor(position);
      const fraction = position - lower;
      const delayed = (1 - fraction) * output[lower] + fraction * output[lower + 1];
      if (index === initialCount) previousDelayed = output[Math.max(0, lower - 1)];
      const damped = brightness * delayed + (1 - brightness) * 0.5 * (delayed + previousDelayed);
      output[index] = feedback * damped;
      previousDelayed = delayed;
    }

    let previousInput = 0;
    let previousOutput = 0;
    peak = 0;
    for (let index = 0; index < output.length; index += 1) {
      const current = output[index] - previousInput + 0.995 * previousOutput;
      previousInput = output[index];
      previousOutput = current;
      output[index] = current;
      peak = Math.max(peak, Math.abs(current));
    }
    const scale = peak > 0 ? request.velocity / peak : 0;
    for (let index = 0; index < output.length; index += 1) {
      output[index] *= scale * contour[index];
    }
    return output;
  }

  function synthesize(name, options) {
    if (name === "additive") return additive(options);
    if (name === "fm") return fm(options);
    if (name === "karplus") return karplus(options);
    throw new RangeError("unknown instrument: " + name);
  }

  const contracts = Object.freeze({
    additive: Object.freeze({
      implementation: "AdditiveSynth.browser.v1",
      partial_ratios: ADDITIVE_RATIOS,
      partial_amplitudes: ADDITIVE_AMPLITUDES,
      guard_band: 0.94,
      seed_phase_source: "splitmix64-indexed-high53/v1"
    }),
    fm: Object.freeze({
      implementation: "FMSynth.browser.v1",
      carrier_ratio: 1,
      modulator_ratio: 2,
      modulation_index: 2.35,
      oversample: 2,
      decimator: "three-tap-triangle/v1"
    }),
    karplus: Object.freeze({
      implementation: "KarplusStrong.browser.v1",
      feedback: 0.996,
      brightness: 0.62,
      pick_position: 0.19,
      excitation: "splitmix64-indexed-high53-zero-mean/v1",
      fractional_delay: "linear/v1"
    })
  });

  Q.Synthesis = Object.freeze({
    MAX_NOTE_SAMPLES,
    MAX_FM_INTERNAL_SAMPLES,
    additive,
    fm,
    karplus,
    synthesize,
    contracts
  });
})(globalThis);
