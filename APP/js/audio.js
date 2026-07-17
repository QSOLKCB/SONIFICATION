/* Deterministic stereo validation, PCM quantization, and RIFF/WAVE packing. */
(function installAudioCore(root) {
  "use strict";

  const Q = root.QSOLIMC;
  if (!Q) {
    throw new Error("namespace.js must be loaded before audio.js");
  }

  function validateSampleRate(sampleRate) {
    if (!Number.isInteger(sampleRate)) {
      throw new TypeError("sampleRate must be an integer");
    }
    if (sampleRate < 8000 || sampleRate > 192000) {
      throw new RangeError("sampleRate must be between 8000 and 192000");
    }
    return sampleRate;
  }

  function validateBitDepth(bitDepth) {
    if (bitDepth !== 16 && bitDepth !== 24) {
      throw new RangeError("bitDepth must be 16 or 24");
    }
    return bitDepth;
  }

  function validateStereo(audio) {
    if (audio === null || typeof audio !== "object") {
      throw new TypeError("audio must be a stereo audio object");
    }
    if (!(audio.left instanceof Float64Array) || !(audio.right instanceof Float64Array)) {
      throw new TypeError("audio.left and audio.right must be Float64Array values");
    }
    if (audio.left.length < 1 || audio.left.length !== audio.right.length) {
      throw new RangeError("stereo audio must contain equal non-empty channels");
    }
    const sampleRate = validateSampleRate(audio.sampleRate);
    for (let index = 0; index < audio.left.length; index += 1) {
      if (!Number.isFinite(audio.left[index]) || !Number.isFinite(audio.right[index])) {
        throw new RangeError("audio contains a non-finite sample at frame " + index);
      }
    }
    return Object.freeze({
      frames: audio.left.length,
      left: audio.left,
      right: audio.right,
      sampleRate: sampleRate,
    });
  }

  function cloneStereo(audio) {
    const source = validateStereo(audio);
    return {
      left: new Float64Array(source.left),
      right: new Float64Array(source.right),
      sampleRate: source.sampleRate,
    };
  }

  function rationalSoftClip(audio, drive) {
    const source = validateStereo(audio);
    const gain = drive === undefined ? 1.15 : drive;
    if (typeof gain !== "number" || !Number.isFinite(gain) || gain < 0.01 || gain > 16) {
      throw new RangeError("drive must be finite and between 0.01 and 16");
    }

    const left = new Float64Array(source.frames);
    const right = new Float64Array(source.frames);
    for (let index = 0; index < source.frames; index += 1) {
      const leftDriven = source.left[index] * gain;
      const rightDriven = source.right[index] * gain;
      left[index] = leftDriven / (1 + Math.abs(leftDriven));
      right[index] = rightDriven / (1 + Math.abs(rightDriven));
    }
    return { left: left, right: right, sampleRate: source.sampleRate };
  }

  function normalizePeak(audio, targetDbfs) {
    const source = validateStereo(audio);
    const dbfs = targetDbfs === undefined ? -3 : targetDbfs;
    if (typeof dbfs !== "number" || !Number.isFinite(dbfs) || dbfs < -96 || dbfs > 0) {
      throw new RangeError("targetDbfs must be finite and between -96 and 0");
    }

    let peak = 0;
    for (let index = 0; index < source.frames; index += 1) {
      peak = Math.max(peak, Math.abs(source.left[index]), Math.abs(source.right[index]));
    }
    const output = cloneStereo(source);
    if (peak === 0) {
      return output;
    }
    const gain = Math.pow(10, dbfs / 20) / peak;
    for (let index = 0; index < source.frames; index += 1) {
      output.left[index] *= gain;
      output.right[index] *= gain;
    }
    return output;
  }

  function roundHalfAwayFromZero(value) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new TypeError("value must be finite");
    }
    return value >= 0 ? Math.floor(value + 0.5) : Math.ceil(value - 0.5);
  }

  function quantizePcm(audio, bitDepth) {
    const source = validateStereo(audio);
    const depth = validateBitDepth(bitDepth);
    const positiveLimit = Math.pow(2, depth - 1) - 1;
    const pcm = new Int32Array(source.frames * 2);
    for (let frame = 0; frame < source.frames; frame += 1) {
      const left = Math.max(-1, Math.min(1, source.left[frame]));
      const right = Math.max(-1, Math.min(1, source.right[frame]));
      pcm[frame * 2] = roundHalfAwayFromZero(left * positiveLimit);
      pcm[frame * 2 + 1] = roundHalfAwayFromZero(right * positiveLimit);
    }
    return pcm;
  }

  function validatePcm(pcm, bitDepth, channels) {
    const depth = validateBitDepth(bitDepth);
    if (!(pcm instanceof Int32Array)) {
      throw new TypeError("pcm must be an Int32Array");
    }
    if (channels !== 1 && channels !== 2) {
      throw new RangeError("channels must be 1 or 2");
    }
    if (pcm.length < channels || pcm.length % channels !== 0) {
      throw new RangeError("pcm must contain at least one complete frame");
    }
    const limit = Math.pow(2, depth - 1) - 1;
    for (let index = 0; index < pcm.length; index += 1) {
      if (pcm[index] < -limit || pcm[index] > limit) {
        throw new RangeError("pcm sample outside the selected symmetric bit-depth range");
      }
    }
    return Object.freeze({
      bitDepth: depth,
      channels: channels,
      frames: pcm.length / channels,
      limit: limit,
      pcm: pcm,
    });
  }

  function pcmPayloadBytes(pcm, bitDepth, channels) {
    const channelCount = channels === undefined ? 2 : channels;
    const source = validatePcm(pcm, bitDepth, channelCount);
    const bytesPerSample = source.bitDepth / 8;
    const output = new Uint8Array(source.pcm.length * bytesPerSample);
    let offset = 0;
    for (let index = 0; index < source.pcm.length; index += 1) {
      const sample = source.pcm[index];
      output[offset] = sample & 0xff;
      output[offset + 1] = (sample >>> 8) & 0xff;
      if (source.bitDepth === 24) {
        output[offset + 2] = (sample >>> 16) & 0xff;
      }
      offset += bytesPerSample;
    }
    return output;
  }

  function writeAscii(bytes, offset, text) {
    for (let index = 0; index < text.length; index += 1) {
      bytes[offset + index] = text.charCodeAt(index);
    }
  }

  function wavBytesFromPcm(pcm, sampleRate, bitDepth, channels) {
    const channelCount = channels === undefined ? 2 : channels;
    const rate = validateSampleRate(sampleRate);
    const source = validatePcm(pcm, bitDepth, channelCount);
    const payload = pcmPayloadBytes(source.pcm, source.bitDepth, source.channels);
    const paddingLength = payload.length & 1;
    const riffSize = 36 + payload.length + paddingLength;
    if (riffSize > 0xffffffff) {
      throw new RangeError("WAV exceeds the RIFF uint32 size domain");
    }

    const wav = new Uint8Array(44 + payload.length + paddingLength);
    const view = new DataView(wav.buffer, wav.byteOffset, wav.byteLength);
    const blockAlign = source.channels * (source.bitDepth / 8);
    const byteRate = rate * blockAlign;
    writeAscii(wav, 0, "RIFF");
    view.setUint32(4, riffSize, true);
    writeAscii(wav, 8, "WAVE");
    writeAscii(wav, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, source.channels, true);
    view.setUint32(24, rate, true);
    view.setUint32(28, byteRate, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, source.bitDepth, true);
    writeAscii(wav, 36, "data");
    view.setUint32(40, payload.length, true);
    wav.set(payload, 44);
    // Uint8Array is zero-filled, so a required RIFF pad byte is canonical.

    return Object.freeze({ pcmBytes: payload, wavBytes: wav });
  }

  function encodeWav(audio, bitDepth) {
    const source = validateStereo(audio);
    const pcm = quantizePcm(source, bitDepth);
    const packed = wavBytesFromPcm(pcm, source.sampleRate, bitDepth, 2);
    return Object.freeze({
      bitDepth: bitDepth,
      channels: 2,
      frames: source.frames,
      pcm: pcm,
      pcmBytes: packed.pcmBytes,
      sampleRate: source.sampleRate,
      wavBytes: packed.wavBytes,
    });
  }

  Q.audio = Object.freeze({
    cloneStereo: cloneStereo,
    encodeWav: encodeWav,
    normalizePeak: normalizePeak,
    pcmPayloadBytes: pcmPayloadBytes,
    quantizePcm: quantizePcm,
    rationalSoftClip: rationalSoftClip,
    roundHalfAwayFromZero: roundHalfAwayFromZero,
    validateBitDepth: validateBitDepth,
    validatePcm: validatePcm,
    validateSampleRate: validateSampleRate,
    validateStereo: validateStereo,
    wavBytesFromPcm: wavBytesFromPcm,
  });

  Q.Audio = Object.freeze({
    quantize: quantizePcm,
    pcmPayload: pcmPayloadBytes,
    encodeWav: encodeWav,
    normalizePeak: normalizePeak,
    softClip: rationalSoftClip,
  });
})(globalThis);
