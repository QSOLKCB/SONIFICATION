(function (root) {
  "use strict";

  function assertionError(message) {
    const error = new Error(message || "assertion failed");
    error.name = "AssertionError";
    return error;
  }

  function assert(condition, message) {
    if (!condition) throw assertionError(message);
  }

  function equal(actual, expected, message) {
    if (!Object.is(actual, expected)) {
      throw assertionError((message ? message + ": " : "") + "expected " + String(expected) + ", received " + String(actual));
    }
  }

  function deepEqual(actual, expected, message) {
    const left = JSON.stringify(actual);
    const right = JSON.stringify(expected);
    if (left !== right) throw assertionError((message ? message + ": " : "") + left + " !== " + right);
  }

  function close(actual, expected, tolerance, message) {
    if (Math.abs(actual - expected) > tolerance) {
      throw assertionError((message ? message + ": " : "") + "expected approximately " + expected + ", received " + actual);
    }
  }

  function bytesEqual(left, right, message) {
    assert(left instanceof Uint8Array && right instanceof Uint8Array, "byte comparison requires Uint8Array values");
    equal(left.length, right.length, message || "byte lengths differ");
    for (let index = 0; index < left.length; index += 1) {
      if (left[index] !== right[index]) throw assertionError((message || "bytes differ") + " at offset " + index);
    }
  }

  function throws(callback, pattern, message) {
    let caught = null;
    try { callback(); } catch (error) { caught = error; }
    assert(caught, message || "expected callback to throw");
    if (pattern) assert(pattern.test(String(caught.message)), "unexpected error: " + caught.message);
  }

  function hex(bytes) {
    return root.QSOLIMC.hash.bytesToHex(bytes);
  }

  root.QSOLIMC_TESTS = async function runTests(report) {
    const Q = root.QSOLIMC;
    const tests = [];
    function test(name, callback) { tests.push({ name, callback }); }

    test("SHA-256 standard vectors", function () {
      equal(Q.Hash.sha256Hex(Q.Hash.utf8("")), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
      equal(Q.Hash.sha256Hex(Q.Hash.utf8("abc")), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    });

    test("canonical JSON sorts recursively and terminates once", function () {
      equal(Q.Hash.canonicalJson({ b: 2, a: { z: true, a: null } }), '{"a":{"a":null,"z":true},"b":2}\n');
      equal(Q.Hash.sha256Hex(Q.Hash.utf8('{"a":1,"b":2}\n')), "e8d38819d39f705646bfb643368eca78f7db476c16471dbc33b941b27326410d");
      throws(function () { Q.Hash.canonicalJson({ value: Infinity }); }, /non-finite/);
      throws(function () { Q.Hash.canonicalJson({ value: Number.MAX_SAFE_INTEGER + 1 }); }, /unsafe JSON integer/);
      throws(function () { Q.Hash.canonicalJson({ value: "\ud800" }); }, /unpaired UTF-16/);
      const specialKey = JSON.parse('{"a":1,"__proto__":{"polluted":true}}');
      equal(Q.Hash.canonicalJson(specialKey), '{"__proto__":{"polluted":true},"a":1}\n');
    });

    test("SplitMix64 matches the published seed-zero vector", function () {
      const expected = [
        "e220a8397b1dcdaf", "6e789e6aa1b965f4", "06c45d188009454f", "f88bb8a8724c81ec", "1b39896a51a8749b"
      ];
      const actual = expected.map(function (_value, index) {
        return Q.Math64.splitmix64At(0n, BigInt(index)).toString(16).padStart(16, "0");
      });
      deepEqual(actual, expected);
    });

    test("uint64 seeds round-trip without Number", function () {
      equal(Q.Math64.seedHex(Q.Math64.parseSeed("18446744073709551615")), "0xffffffffffffffff");
      equal(Q.Math64.seedHex(Q.Math64.parseSeed("0x1")), "0x0000000000000001");
      throws(function () { Q.Math64.parseSeed("18446744073709551616"); }, /unsigned 64-bit/);
      throws(function () { Q.Math64.parseSeed("9".repeat(1000)); }, /lexical domain/);
    });

    test("lattice coordinates require a representable right neighbor", function () {
      const valid = Q.Math64.rightNeighbor(Q.Math64.MASK64 - 1n);
      equal(valid.right, Q.Math64.MASK64);
      throws(function () { Q.Math64.rightNeighbor(Q.Math64.MASK64); }, /right neighbor/);
    });

    test("PCM16 and PCM24 use signed little-endian packing", function () {
      const pcm16 = new Int32Array([-32767, -2, -1, 0, 1, 2, 32767, 17]);
      equal(hex(Q.Audio.pcmPayload(pcm16, 16, 2)), "0180feffffff000001000200ff7f1100");
      const pcm24 = new Int32Array([-8388607, -2, -1, 0, 1, 2, 8388607, 17]);
      equal(hex(Q.Audio.pcmPayload(pcm24, 24, 2)), "010080feffffffffff000000010000020000ffff7f110000");
    });

    test("odd PCM24 payload receives a RIFF pad outside data size", function () {
      const packed = Q.audio.wavBytesFromPcm(new Int32Array([1, 2, 3]), 8000, 24, 1);
      const view = new DataView(packed.wavBytes.buffer, packed.wavBytes.byteOffset, packed.wavBytes.byteLength);
      equal(packed.pcmBytes.length, 9);
      equal(view.getUint32(40, true), 9);
      equal(view.getUint32(4, true), 46);
      equal(packed.wavBytes.length, 54);
      equal(packed.wavBytes[53], 0);
    });

    test("one-frame fingerprint clamps a 32-bin request to one bin", function () {
      const pcm = new Int32Array([-32767, 32767]);
      const packed = Q.audio.wavBytesFromPcm(pcm, 8000, 16, 2);
      const fingerprint = Q.Provenance.buildFingerprint({
        pcm: pcm, pcmBytes: packed.pcmBytes, wavBytes: packed.wavBytes, sampleRate: 8000, bitDepth: 16, channels: 2
      });
      deepEqual(fingerprint.rms_envelope_ppm, [1000000]);
      equal(fingerprint.pcm_sha256, "a1720c76a3cf814fa07b8447523755be6bdc1f79283fbac227a1d5f3db480448");
      equal(fingerprint.wav_sha256, "95598f73aa50a360b5963caf7eae9226673d2cbc287c6851f3b7ee12d9ffbef6");
    });

    test("four-frame fingerprint clamps the default request to four bins", function () {
      const pcm = new Int32Array([-24575, 8192, -8192, 24575, 0, 0, 16384, -16384]);
      const packed = Q.audio.wavBytesFromPcm(pcm, 8000, 16, 2);
      const fingerprint = Q.Provenance.buildFingerprint({
        pcm: pcm, pcmBytes: packed.pcmBytes, wavBytes: packed.wavBytes, sampleRate: 8000, bitDepth: 16, channels: 2
      });
      equal(fingerprint.rms_envelope_ppm.length, 4);
      assert(fingerprint.rms_envelope_ppm.every(Number.isFinite), "envelope must remain finite");
    });

    test("all voice engines return finite deterministic audio", function () {
      ["additive", "fm", "karplus"].forEach(function (voice) {
        const options = { frequencyHz: 110, durationSeconds: 0.02, velocity: 0.8, sampleRate: 8000, seed: 42n };
        const first = Q.Synthesis.synthesize(voice, options);
        const second = Q.Synthesis.synthesize(voice, options);
        equal(first.length, second.length);
        for (let index = 0; index < first.length; index += 1) {
          assert(Number.isFinite(first[index]), voice + " emitted a non-finite sample");
          equal(first[index], second[index], voice + " replay differs at sample " + index);
        }
      });
    });

    test("instrument contracts cannot drift from frozen DSP constants", function () {
      const original = Q.Synthesis.contracts.additive.partial_ratios[0];
      throws(function () { Q.Synthesis.contracts.additive.partial_ratios[0] = 99; });
      equal(Q.Synthesis.contracts.additive.partial_ratios[0], original);
    });

    test("frame preflight uses positive decimal half-up duration", function () {
      const config = Q.Composition.normalizeConfig({
        voice: "additive", seed: "1", tempo: "128", bars: "4", tuning: "432", sampleRate: "44100", bitDepth: "24", peak: "-3"
      });
      equal(config.frameCount, 330750);
      equal(config.seedHex, "0x0000000000000001");

      const precise = Q.Composition.normalizeConfig({
        voice: "additive",
        seed: "1",
        tempo: "191.99040047997600119994000299985000749962511874906254687265636718164091795410229",
        bars: "1",
        tuning: "432.0000000000000000001",
        sampleRate: "8000",
        bitDepth: "16",
        peak: "-3"
      });
      const replayedPreflight = Q.Composition.normalizeConfig(precise);
      equal(precise.frameCount, 10000);
      equal(replayedPreflight.frameCount, precise.frameCount);
      equal(replayedPreflight.tempoText, precise.tempoText);
    });

    test("circular note tails fold across the loop boundary", function () {
      const left = new Float64Array(4);
      const right = new Float64Array(4);
      Q.Composition.addCircular(left, right, new Float64Array([1, 2, 3]), 3, 0, 1);
      const gain = Math.SQRT1_2;
      close(left[3], gain, 1e-15);
      close(left[0], 2 * gain, 1e-15);
      close(left[1], 3 * gain, 1e-15);
      close(right[0], 2 * gain, 1e-15);
    });

    test("manifest chain validates and detects tampering", function () {
      const audio = { left: new Float64Array([0, 0.25]), right: new Float64Array([0, -0.25]), sampleRate: 8000 };
      const encoded = Q.Audio.encodeWav(audio, 16);
      const fingerprint = Q.Provenance.buildFingerprint(Object.assign({}, encoded));
      const recipe = Q.Provenance.buildRecipe({ settings: { seed: "0x0000000000000001" } });
      const manifest = Q.Provenance.buildManifest({ recipe: recipe, fingerprint: fingerprint });
      equal(Q.Provenance.validateManifest(manifest), true);
      const tampered = JSON.parse(JSON.stringify(manifest));
      tampered.claim_boundary += " altered";
      throws(function () { Q.Provenance.validateManifest(tampered); }, /integrity/);

      const foreignFingerprint = Object.assign({}, fingerprint, { abi: "foreign.browser/v1" });
      const foreignCore = Object.assign({}, foreignFingerprint);
      delete foreignCore.fingerprint_sha256;
      foreignFingerprint.fingerprint_sha256 = Q.Hash.domainHash(Q.provenance.DOMAINS.FINGERPRINT, foreignCore);
      throws(
        function () { Q.Provenance.buildManifest({ recipe: recipe, fingerprint: foreignFingerprint }); },
        /schema or ABI/
      );
      const foreignRecipe = JSON.parse(JSON.stringify(recipe));
      foreignRecipe.engine.version = "9.9.9";
      throws(
        function () { Q.Provenance.buildManifest({ recipe: foreignRecipe, fingerprint: fingerprint }); },
        /schema or ABI/
      );
    });

    test("small browser renders replay to identical WAV bytes", async function () {
      const config = Q.Composition.normalizeConfig({
        voice: "additive", seed: "2026", tempo: "400", bars: "1", tuning: "432", sampleRate: "8000", bitDepth: "16", peak: "-6"
      });
      const first = await Q.Composition.renderLoop(config);
      const second = await Q.Composition.renderLoop(config);
      bytesEqual(first.wavBytes, second.wavBytes, "replayed WAV differs");
      equal(first.fingerprint.wav_sha256, second.fingerprint.wav_sha256);
      equal(Q.Provenance.validateManifest(first.manifest), true);
      const changedConfig = Object.assign({}, config, { seed: 2027n, seedHex: "0x00000000000007eb" });
      const changed = await Q.Composition.renderLoop(changedConfig);
      assert(changed.fingerprint.pcm_sha256 !== first.fingerprint.pcm_sha256, "changed seed must change PCM");
    });

    test("render allocation preflight cannot be bypassed by forged derived fields", async function () {
      let caught = null;
      try {
        await Q.Composition.renderLoop({
          frameCount: 1,
          voice: "additive",
          seed: "1",
          tempo: "1",
          bars: "1",
          tuning: "432",
          sampleRate: "8000",
          bitDepth: "16",
          peak: "-6"
        });
      } catch (error) {
        caught = error;
      }
      assert(caught && /tempo/.test(caught.message), "forged normalized configuration must be rejected");
    });

    const outcomes = [];
    for (const item of tests) {
      try {
        await item.callback();
        const outcome = { name: item.name, passed: true };
        outcomes.push(outcome);
        if (report) report(outcome);
      } catch (error) {
        const outcome = { name: item.name, passed: false, error: error && error.stack ? error.stack : String(error) };
        outcomes.push(outcome);
        if (report) report(outcome);
      }
    }
    return outcomes;
  };
})(globalThis);
