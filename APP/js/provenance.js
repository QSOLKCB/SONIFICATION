/* Canonical JSON, signal fingerprints, and acyclic browser provenance. */
(function installProvenance(root) {
  "use strict";

  const Q = root.QSOLIMC;
  if (!Q || !Q.hash || !Q.audio) {
    throw new Error("namespace.js, sha256.js, and audio.js must load before provenance.js");
  }

  const DOMAINS = Object.freeze({
    CONTRACT: "QSOL-IMC/CONTRACT/v1\0",
    FINGERPRINT: "QSOL-IMC/FINGERPRINT/v1\0",
    MANIFEST_CORE: "QSOL-IMC/MANIFEST-CORE/v1\0",
    RECIPE: "QSOL-IMC/RECIPE/v1\0",
    RMS_ENVELOPE: "QSOL-IMC/RMS-ENVELOPE/v1\0",
  });

  function requireUnicodeScalarString(value, path) {
    for (let index = 0; index < value.length; index += 1) {
      const unit = value.charCodeAt(index);
      if (unit >= 0xd800 && unit <= 0xdbff) {
        const following = value.charCodeAt(index + 1);
        if (!(following >= 0xdc00 && following <= 0xdfff)) {
          throw new TypeError("unpaired UTF-16 surrogate at " + path);
        }
        index += 1;
      } else if (unit >= 0xdc00 && unit <= 0xdfff) {
        throw new TypeError("unpaired UTF-16 surrogate at " + path);
      }
    }
    return value;
  }

  function canonicalValue(value, path, ancestors) {
    const location = path || "$";
    if (value === null || typeof value === "boolean") {
      return value;
    }
    if (typeof value === "string") {
      return requireUnicodeScalarString(value, location);
    }
    if (typeof value === "number") {
      if (!Number.isFinite(value)) {
        throw new RangeError("non-finite number at " + location);
      }
      if (Number.isInteger(value) && !Number.isSafeInteger(value)) {
        throw new RangeError("unsafe JSON integer at " + location);
      }
      return Object.is(value, -0) ? 0 : value;
    }
    if (typeof value !== "object") {
      throw new TypeError("unsupported canonical JSON value at " + location);
    }
    if (ancestors.has(value)) {
      throw new TypeError("cyclic canonical JSON value at " + location);
    }

    ancestors.add(value);
    let output;
    if (Array.isArray(value)) {
      output = new Array(value.length);
      for (let index = 0; index < value.length; index += 1) {
        if (!Object.prototype.hasOwnProperty.call(value, index)) {
          ancestors.delete(value);
          throw new TypeError("sparse canonical JSON array at " + location);
        }
        output[index] = canonicalValue(value[index], location + "[" + index + "]", ancestors);
      }
    } else {
      const prototype = Object.getPrototypeOf(value);
      if (prototype !== Object.prototype && prototype !== null) {
        ancestors.delete(value);
        throw new TypeError("canonical JSON objects must be plain objects at " + location);
      }
      const symbols = Object.getOwnPropertySymbols(value);
      if (symbols.length !== 0) {
        ancestors.delete(value);
        throw new TypeError("symbol keys are not supported at " + location);
      }
      // A null prototype keeps special keys such as "__proto__" as ordinary
      // identity-bearing JSON data instead of mutating this temporary object.
      output = Object.create(null);
      const keys = Object.keys(value).sort();
      for (const key of keys) {
        requireUnicodeScalarString(key, location + " object key");
        output[key] = canonicalValue(value[key], location + "." + key, ancestors);
      }
    }
    ancestors.delete(value);
    return output;
  }

  function canonicalJson(value) {
    const normalized = canonicalValue(value, "$", new Set());
    return JSON.stringify(normalized) + "\n";
  }

  function canonicalJsonBytes(value) {
    return Q.hash.utf8Bytes(canonicalJson(value));
  }

  function canonicalClone(value) {
    return JSON.parse(canonicalJson(value));
  }

  function domainHash(domain, value) {
    return Q.hash.domainHashBytes(domain, canonicalJsonBytes(value));
  }

  function bytesEqual(left, right) {
    if (!(left instanceof Uint8Array) || !(right instanceof Uint8Array)) {
      return false;
    }
    if (left.length !== right.length) {
      return false;
    }
    let difference = 0;
    for (let index = 0; index < left.length; index += 1) {
      difference |= left[index] ^ right[index];
    }
    return difference === 0;
  }

  function requirePositiveInteger(value, name, maximum) {
    if (!Number.isSafeInteger(value) || value < 1) {
      throw new RangeError(name + " must be a positive safe integer");
    }
    if (maximum !== undefined && value > maximum) {
      throw new RangeError(name + " exceeds its supported maximum of " + maximum);
    }
    return value;
  }

  function roundFloat(value, digits) {
    if (!Number.isFinite(value)) {
      throw new RangeError("fingerprint metric is non-finite");
    }
    const rounded = Number(value.toFixed(digits === undefined ? 12 : digits));
    return Object.is(rounded, -0) ? 0 : rounded;
  }

  function buildFingerprint(options) {
    if (options === null || typeof options !== "object") {
      throw new TypeError("fingerprint options must be an object");
    }
    const pcm = options.pcm;
    const channels = options.channels === undefined ? 2 : options.channels;
    const bitDepth = Q.audio.validateBitDepth(options.bitDepth);
    const sampleRate = Q.audio.validateSampleRate(options.sampleRate);
    const pcmInfo = Q.audio.validatePcm(pcm, bitDepth, channels);
    const pcmBytes = options.pcmBytes;
    const wavBytes = options.wavBytes;
    if (!(pcmBytes instanceof Uint8Array) || !(wavBytes instanceof Uint8Array)) {
      throw new TypeError("pcmBytes and wavBytes must be Uint8Array values");
    }
    const expected = Q.audio.wavBytesFromPcm(pcm, sampleRate, bitDepth, channels);
    if (!bytesEqual(pcmBytes, expected.pcmBytes)) {
      throw new Error("pcmBytes do not match the PCM samples");
    }
    if (!bytesEqual(wavBytes, expected.wavBytes)) {
      throw new Error("wavBytes do not match the PCM samples and format");
    }

    const requestedEnvelopeBins = options.envelopeBins === undefined ? 32 : options.envelopeBins;
    const chunkCount = options.chunkCount === undefined ? 16 : options.chunkCount;
    requirePositiveInteger(requestedEnvelopeBins, "envelopeBins", 65536);
    requirePositiveInteger(chunkCount, "chunkCount", 4096);

    const frames = pcmInfo.frames;
    const limit = pcmInfo.limit;
    const channelSums = new Float64Array(channels);
    let absolutePeak = 0;
    let squareSum = 0;
    let zeroCrossings = 0;
    let clippingSampleCount = 0;
    for (let frame = 0; frame < frames; frame += 1) {
      for (let channel = 0; channel < channels; channel += 1) {
        const index = frame * channels + channel;
        const sample = pcm[index];
        const normalized = sample / limit;
        const magnitude = Math.abs(normalized);
        absolutePeak = Math.max(absolutePeak, magnitude);
        squareSum += normalized * normalized;
        channelSums[channel] += normalized;
        if (Math.abs(sample) >= limit) {
          clippingSampleCount += 1;
        }
        if (frame > 0) {
          const previous = pcm[(frame - 1) * channels + channel];
          if ((sample >= 0) !== (previous >= 0)) {
            zeroCrossings += 1;
          }
        }
      }
    }

    const rms = Math.sqrt(squareSum / pcm.length);
    const dcOffset = Array.from(channelSums, function average(sum) {
      return roundFloat(sum / frames);
    });
    let stereoCorrelation = channels === 2 ? 0 : 1;
    if (channels === 2) {
      const leftMean = channelSums[0] / frames;
      const rightMean = channelSums[1] / frames;
      let cross = 0;
      let leftEnergy = 0;
      let rightEnergy = 0;
      for (let frame = 0; frame < frames; frame += 1) {
        const left = pcm[frame * 2] / limit - leftMean;
        const right = pcm[frame * 2 + 1] / limit - rightMean;
        cross += left * right;
        leftEnergy += left * left;
        rightEnergy += right * right;
      }
      const denominator = Math.sqrt(leftEnergy * rightEnergy);
      stereoCorrelation = denominator > 0 ? cross / denominator : 0;
    }

    // The requested value is an upper bound. With bins <= frames, every
    // [start, stop) slice below contains at least one frame, including a
    // one-frame input with the default request for 32 bins.
    const effectiveEnvelopeBins = Math.min(requestedEnvelopeBins, frames);
    const envelopePpm = new Array(effectiveEnvelopeBins);
    for (let bin = 0; bin < effectiveEnvelopeBins; bin += 1) {
      const start = Math.floor((bin * frames) / effectiveEnvelopeBins);
      const stop = Math.floor(((bin + 1) * frames) / effectiveEnvelopeBins);
      let segmentSquareSum = 0;
      for (let frame = start; frame < stop; frame += 1) {
        for (let channel = 0; channel < channels; channel += 1) {
          const normalized = pcm[frame * channels + channel] / limit;
          segmentSquareSum += normalized * normalized;
        }
      }
      const segmentRms = Math.sqrt(segmentSquareSum / ((stop - start) * channels));
      envelopePpm[bin] = Math.round(segmentRms * 1000000);
    }

    const chunkHashes = new Array(chunkCount);
    for (let chunk = 0; chunk < chunkCount; chunk += 1) {
      const start = Math.floor((chunk * pcmBytes.length) / chunkCount);
      const stop = Math.floor(((chunk + 1) * pcmBytes.length) / chunkCount);
      chunkHashes[chunk] = Q.hash.sha256Hex(pcmBytes.subarray(start, stop));
    }

    const core = {
      schema: "qsol-imc.audio-fingerprint/v1",
      abi: Q.ABI,
      sample_rate: sampleRate,
      bit_depth: bitDepth,
      frames: frames,
      channels: channels,
      pcm_sha256: Q.hash.sha256Hex(pcmBytes),
      wav_sha256: Q.hash.sha256Hex(wavBytes),
      peak: roundFloat(absolutePeak),
      rms: roundFloat(rms),
      dc_offset: dcOffset,
      crest_factor: rms > 0 ? roundFloat(absolutePeak / rms) : 0,
      zero_crossings: zeroCrossings,
      stereo_correlation: roundFloat(stereoCorrelation),
      clipping_sample_count: clippingSampleCount,
      rms_envelope_ppm: envelopePpm,
      rms_envelope_sha256: domainHash(DOMAINS.RMS_ENVELOPE, envelopePpm),
      pcm_chunk_sha256: chunkHashes,
    };
    return Object.assign({}, core, {
      fingerprint_sha256: domainHash(DOMAINS.FINGERPRINT, core),
    });
  }

  function buildRecipe(options) {
    if (options === null || typeof options !== "object" || Array.isArray(options)) {
      throw new TypeError("recipe options must be an object");
    }
    const settings = options.settings === undefined ? {} : options.settings;
    const arrangement = options.arrangement === undefined ? [] : options.arrangement;
    const metadata = options.metadata === undefined ? {} : options.metadata;
    const core = {
      schema: "qsol-imc.browser-recipe/v1",
      engine: {
        name: Q.APP_NAME,
        version: Q.VERSION,
        abi: Q.ABI,
      },
      settings: canonicalClone(settings),
      arrangement: canonicalClone(arrangement),
      metadata: canonicalClone(metadata),
    };
    // Canonicalization here is validation as well as a stable deep copy.
    return canonicalClone(core);
  }

  function requireHash(value, name) {
    if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value)) {
      throw new TypeError(name + " must be a lowercase SHA-256 hex string");
    }
    return value;
  }

  function validateArtifactContracts(recipe, fingerprint) {
    if (
      recipe === null ||
      typeof recipe !== "object" ||
      recipe.schema !== "qsol-imc.browser-recipe/v1" ||
      recipe.engine === null ||
      typeof recipe.engine !== "object" ||
      recipe.engine.abi !== Q.ABI ||
      recipe.engine.name !== Q.APP_NAME ||
      recipe.engine.version !== Q.VERSION
    ) {
      throw new Error("recipe schema or ABI is incompatible with this application");
    }
    if (
      fingerprint === null ||
      typeof fingerprint !== "object" ||
      fingerprint.schema !== "qsol-imc.audio-fingerprint/v1" ||
      fingerprint.abi !== Q.ABI
    ) {
      throw new Error("fingerprint schema or ABI is incompatible with this application");
    }
    Q.audio.validateSampleRate(fingerprint.sample_rate);
    Q.audio.validateBitDepth(fingerprint.bit_depth);
    if (fingerprint.channels !== 1 && fingerprint.channels !== 2) {
      throw new Error("fingerprint channel contract is invalid");
    }
    requirePositiveInteger(fingerprint.frames, "fingerprint.frames");
  }

  function buildManifest(options) {
    if (options === null || typeof options !== "object") {
      throw new TypeError("manifest options must be an object");
    }
    const applicationVersion = options.applicationVersion === undefined
      ? Q.VERSION
      : options.applicationVersion;
    if (typeof applicationVersion !== "string" || applicationVersion.length < 1) {
      throw new TypeError("applicationVersion must be a non-empty string");
    }
    if (applicationVersion !== Q.VERSION) {
      throw new Error("applicationVersion is incompatible with this application");
    }
    const recipe = canonicalClone(options.recipe);
    const fingerprint = canonicalClone(options.fingerprint);
    validateArtifactContracts(recipe, fingerprint);
    const lineage = canonicalClone(options.lineage === undefined ? [] : options.lineage);
    if (!Array.isArray(lineage)) {
      throw new TypeError("lineage must be an array");
    }

    const recipeSha256 = domainHash(DOMAINS.RECIPE, recipe);
    const fingerprintCore = Object.assign({}, fingerprint);
    const recordedFingerprintSha256 = fingerprintCore.fingerprint_sha256;
    delete fingerprintCore.fingerprint_sha256;
    const calculatedFingerprintSha256 = domainHash(DOMAINS.FINGERPRINT, fingerprintCore);
    if (recordedFingerprintSha256 !== calculatedFingerprintSha256) {
      throw new Error("fingerprint integrity check failed");
    }
    requireHash(fingerprint.pcm_sha256, "fingerprint.pcm_sha256");
    requireHash(fingerprint.wav_sha256, "fingerprint.wav_sha256");

    const contractCore = {
      schema: "qsol-imc.render-contract/v1",
      abi: Q.ABI,
      recipe_sha256: recipeSha256,
      fingerprint_sha256: calculatedFingerprintSha256,
      pcm_sha256: fingerprint.pcm_sha256,
      wav_sha256: fingerprint.wav_sha256,
      sample_format: "pcm_s" + fingerprint.bit_depth + "le",
      determinism_scope: Q.DETERMINISM_SCOPE,
    };
    const contract = Object.assign({}, contractCore, {
      contract_sha256: domainHash(DOMAINS.CONTRACT, contractCore),
    });
    const manifestCore = {
      schema: "qsol-imc.manifest/v1",
      application: {
        name: Q.APP_NAME,
        version: applicationVersion,
        abi: Q.ABI,
      },
      phase: "offline-browser-1",
      recipe: recipe,
      recipe_sha256: recipeSha256,
      fingerprint: fingerprint,
      contract: contract,
      lineage: lineage,
      claim_boundary: (
        "This artifact is mathematical composition and audible geometry. " +
        "It is not evidence that E8 or another sonified structure is physically present in nature."
      ),
    };
    return Object.assign({}, manifestCore, {
      manifest_core_sha256: domainHash(DOMAINS.MANIFEST_CORE, manifestCore),
    });
  }

  function validateManifestIntegrity(manifest) {
    if (manifest === null || typeof manifest !== "object" || Array.isArray(manifest)) {
      throw new TypeError("manifest must be an object");
    }
    const manifestCore = canonicalClone(manifest);
    const manifestSha256 = manifestCore.manifest_core_sha256;
    delete manifestCore.manifest_core_sha256;
    requireHash(manifestSha256, "manifest_core_sha256");
    if (domainHash(DOMAINS.MANIFEST_CORE, manifestCore) !== manifestSha256) {
      throw new Error("manifest core integrity check failed");
    }

    if (
      manifestCore.schema !== "qsol-imc.manifest/v1" ||
      manifestCore.application === null ||
      typeof manifestCore.application !== "object" ||
      manifestCore.application.abi !== Q.ABI ||
      manifestCore.application.name !== Q.APP_NAME ||
      manifestCore.application.version !== Q.VERSION
    ) {
      throw new Error("manifest schema or application ABI is incompatible");
    }

    const recipe = manifestCore.recipe;
    validateArtifactContracts(recipe, manifestCore.fingerprint);
    const recipeSha256 = requireHash(manifestCore.recipe_sha256, "recipe_sha256");
    if (domainHash(DOMAINS.RECIPE, recipe) !== recipeSha256) {
      throw new Error("recipe integrity check failed");
    }

    const fingerprint = canonicalClone(manifestCore.fingerprint);
    const fingerprintSha256 = fingerprint.fingerprint_sha256;
    delete fingerprint.fingerprint_sha256;
    requireHash(fingerprintSha256, "fingerprint.fingerprint_sha256");
    if (domainHash(DOMAINS.FINGERPRINT, fingerprint) !== fingerprintSha256) {
      throw new Error("fingerprint integrity check failed");
    }

    const contract = canonicalClone(manifestCore.contract);
    const contractSha256 = contract.contract_sha256;
    delete contract.contract_sha256;
    requireHash(contractSha256, "contract.contract_sha256");
    if (domainHash(DOMAINS.CONTRACT, contract) !== contractSha256) {
      throw new Error("contract integrity check failed");
    }
    const expectedSampleFormat = "pcm_s" + manifestCore.fingerprint.bit_depth + "le";
    if (
      contract.schema !== "qsol-imc.render-contract/v1" ||
      contract.recipe_sha256 !== recipeSha256 ||
      contract.fingerprint_sha256 !== fingerprintSha256 ||
      contract.pcm_sha256 !== manifestCore.fingerprint.pcm_sha256 ||
      contract.wav_sha256 !== manifestCore.fingerprint.wav_sha256 ||
      contract.abi !== Q.ABI ||
      contract.sample_format !== expectedSampleFormat
    ) {
      throw new Error("manifest hash links are inconsistent");
    }
    return true;
  }

  function validateArtifactHashes(manifest, pcmBytes, wavBytes) {
    validateManifestIntegrity(manifest);
    if (!(pcmBytes instanceof Uint8Array) || !(wavBytes instanceof Uint8Array)) {
      throw new TypeError("pcmBytes and wavBytes must be Uint8Array values");
    }
    if (Q.hash.sha256Hex(pcmBytes) !== manifest.fingerprint.pcm_sha256) {
      throw new Error("PCM payload hash does not match the manifest");
    }
    if (Q.hash.sha256Hex(wavBytes) !== manifest.fingerprint.wav_sha256) {
      throw new Error("WAV file hash does not match the manifest");
    }
    return true;
  }

  Q.provenance = Object.freeze({
    DOMAINS: DOMAINS,
    buildFingerprint: buildFingerprint,
    buildManifest: buildManifest,
    buildRecipe: buildRecipe,
    bytesEqual: bytesEqual,
    canonicalClone: canonicalClone,
    canonicalJson: canonicalJson,
    canonicalJsonBytes: canonicalJsonBytes,
    domainHash: domainHash,
    validateArtifactHashes: validateArtifactHashes,
    validateManifestIntegrity: validateManifestIntegrity,
  });

  Q.Hash.canonicalJson = canonicalJson;
  Q.Hash.canonicalBytes = canonicalJsonBytes;
  Q.Hash.domainHash = domainHash;
  Q.Hash = Object.freeze(Q.Hash);

  Q.Provenance = Object.freeze({
    buildFingerprint: buildFingerprint,
    buildRecipe: buildRecipe,
    buildManifest: buildManifest,
    validateManifest: validateManifestIntegrity,
  });
})(globalThis);
