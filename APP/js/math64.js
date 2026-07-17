/* Exact unsigned-64 seed and lattice arithmetic using JavaScript BigInt. */
(function installMath64(root) {
  "use strict";

  const Q = root.QSOLIMC;
  if (!Q) {
    throw new Error("namespace.js must be loaded before math64.js");
  }

  const UINT64_MASK = 0xffffffffffffffffn;
  const SPLITMIX_INCREMENT = 0x9e3779b97f4a7c15n;
  const MIX_MULTIPLIER_A = 0xbf58476d1ce4e5b9n;
  const MIX_MULTIPLIER_B = 0x94d049bb133111ebn;
  const TWO_POW_53 = 9007199254740992;

  function parseUint64(value, name) {
    const label = name || "value";
    let parsed;
    if (typeof value === "bigint") {
      parsed = value;
    } else if (typeof value === "number") {
      if (!Number.isSafeInteger(value)) {
        throw new TypeError(label + " must be a safe integer, bigint, or uint64 string");
      }
      parsed = BigInt(value);
    } else if (typeof value === "string") {
      const text = value.trim();
      if (!/^(?:0[xX][0-9a-fA-F]+|[0-9]+)$/.test(text)) {
        throw new TypeError(label + " must be an unsigned decimal or 0x-prefixed hexadecimal integer");
      }
      const digitCount = /^0[xX]/.test(text) ? text.length - 2 : text.length;
      const maximumDigits = /^0[xX]/.test(text) ? 16 : 20;
      if (digitCount > maximumDigits) {
        throw new RangeError(label + " exceeds the unsigned 64-bit lexical domain");
      }
      parsed = BigInt(text);
    } else {
      throw new TypeError(label + " must be a safe integer, bigint, or uint64 string");
    }

    if (parsed < 0n || parsed > UINT64_MASK) {
      throw new RangeError(label + " must be within the unsigned 64-bit domain");
    }
    return parsed;
  }

  function formatUint64Hex(value) {
    return "0x" + parseUint64(value).toString(16).padStart(16, "0");
  }

  function finalizeSplitMix64(word) {
    let mixed = word & UINT64_MASK;
    mixed = ((mixed ^ (mixed >> 30n)) * MIX_MULTIPLIER_A) & UINT64_MASK;
    mixed = ((mixed ^ (mixed >> 27n)) * MIX_MULTIPLIER_B) & UINT64_MASK;
    return (mixed ^ (mixed >> 31n)) & UINT64_MASK;
  }

  function splitMix64(value) {
    const state = (parseUint64(value) + SPLITMIX_INCREMENT) & UINT64_MASK;
    return finalizeSplitMix64(state);
  }

  function splitMix64At(seed, index) {
    const origin = parseUint64(seed, "seed");
    const position = parseUint64(index, "index");
    const state = (origin + ((position + 1n) * SPLITMIX_INCREMENT)) & UINT64_MASK;
    return finalizeSplitMix64(state);
  }

  function uint64ToUnitFloat(word) {
    return Number(parseUint64(word) >> 11n) / TWO_POW_53;
  }

  function uint64ToSignedFloat(word) {
    return uint64ToUnitFloat(word) * 2 - 1;
  }

  function SplitMix64(seed) {
    if (!(this instanceof SplitMix64)) {
      return new SplitMix64(seed);
    }
    this.state = parseUint64(seed, "seed");
  }

  SplitMix64.prototype.nextUint64 = function nextUint64() {
    this.state = (this.state + SPLITMIX_INCREMENT) & UINT64_MASK;
    return finalizeSplitMix64(this.state);
  };

  SplitMix64.prototype.nextFloat = function nextFloat() {
    return uint64ToUnitFloat(this.nextUint64());
  };

  SplitMix64.prototype.nextSignedFloat = function nextSignedFloat() {
    return this.nextFloat() * 2 - 1;
  };

  SplitMix64.prototype.clone = function clone() {
    return new SplitMix64(this.state);
  };

  function validateLatticeRightNeighbor(left) {
    const latticeIndex = parseUint64(left, "lattice index");
    if (latticeIndex >= UINT64_MASK) {
      throw new RangeError("lattice index has no representable uint64 right neighbor");
    }
    return Object.freeze({
      left: latticeIndex,
      right: latticeIndex + 1n,
    });
  }

  function latticeCoordinate(sampleIndex, periodSamples) {
    const sample = parseUint64(sampleIndex, "sample index");
    const period = parseUint64(periodSamples, "period samples");
    if (period === 0n) {
      throw new RangeError("period samples must be positive");
    }
    const left = sample / period;
    const neighbors = validateLatticeRightNeighbor(left);
    return Object.freeze({
      left: neighbors.left,
      right: neighbors.right,
      remainder: sample % period,
      period: period,
      fraction: Number(sample % period) / Number(period),
    });
  }

  Q.math64 = Object.freeze({
    UINT64_MASK: UINT64_MASK,
    SPLITMIX_INCREMENT: SPLITMIX_INCREMENT,
    SplitMix64: SplitMix64,
    formatUint64Hex: formatUint64Hex,
    latticeCoordinate: latticeCoordinate,
    parseSeed: function parseSeed(value) {
      return parseUint64(value, "seed");
    },
    parseUint64: parseUint64,
    splitMix64: splitMix64,
    splitMix64At: splitMix64At,
    uint64ToSignedFloat: uint64ToSignedFloat,
    uint64ToUnitFloat: uint64ToUnitFloat,
    validateLatticeRightNeighbor: validateLatticeRightNeighbor,
  });

  Q.Math64 = Object.freeze({
    MASK64: UINT64_MASK,
    parseSeed: function parseSeed(value) {
      return parseUint64(value, "seed");
    },
    seedHex: formatUint64Hex,
    splitmix64: splitMix64,
    splitmix64At: splitMix64At,
    uint64ToUnit: uint64ToUnitFloat,
    rightNeighbor: validateLatticeRightNeighbor,
  });
})(globalThis);
