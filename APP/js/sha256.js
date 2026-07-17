/* Dependency-free SHA-256 for exact offline artifact identity. */
(function installSHA256(root) {
  "use strict";

  const Q = root.QSOLIMC;
  if (!Q) {
    throw new Error("namespace.js must be loaded before sha256.js");
  }

  const ROUND_CONSTANTS = new Uint32Array([
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
  ]);

  function requireBytes(value, name) {
    if (!(value instanceof Uint8Array)) {
      throw new TypeError((name || "input") + " must be a Uint8Array");
    }
    return value;
  }

  function rotateRight(word, count) {
    return ((word >>> count) | (word << (32 - count))) >>> 0;
  }

  function utf8Bytes(text) {
    if (typeof text !== "string") {
      throw new TypeError("text must be a string");
    }

    const output = [];
    for (let index = 0; index < text.length; index += 1) {
      let codePoint = text.charCodeAt(index);
      if (codePoint >= 0xd800 && codePoint <= 0xdbff) {
        if (index + 1 < text.length) {
          const following = text.charCodeAt(index + 1);
          if (following >= 0xdc00 && following <= 0xdfff) {
            codePoint = 0x10000 + ((codePoint - 0xd800) << 10) + (following - 0xdc00);
            index += 1;
          } else {
            codePoint = 0xfffd;
          }
        } else {
          codePoint = 0xfffd;
        }
      } else if (codePoint >= 0xdc00 && codePoint <= 0xdfff) {
        codePoint = 0xfffd;
      }

      if (codePoint <= 0x7f) {
        output.push(codePoint);
      } else if (codePoint <= 0x7ff) {
        output.push(0xc0 | (codePoint >>> 6));
        output.push(0x80 | (codePoint & 0x3f));
      } else if (codePoint <= 0xffff) {
        output.push(0xe0 | (codePoint >>> 12));
        output.push(0x80 | ((codePoint >>> 6) & 0x3f));
        output.push(0x80 | (codePoint & 0x3f));
      } else {
        output.push(0xf0 | (codePoint >>> 18));
        output.push(0x80 | ((codePoint >>> 12) & 0x3f));
        output.push(0x80 | ((codePoint >>> 6) & 0x3f));
        output.push(0x80 | (codePoint & 0x3f));
      }
    }
    return Uint8Array.from(output);
  }

  function concatenateBytes(parts) {
    if (!Array.isArray(parts)) {
      throw new TypeError("parts must be an array of Uint8Array values");
    }
    let length = 0;
    for (const part of parts) {
      requireBytes(part, "byte part");
      length += part.length;
      if (!Number.isSafeInteger(length)) {
        throw new RangeError("combined byte length exceeds the safe integer domain");
      }
    }
    const output = new Uint8Array(length);
    let offset = 0;
    for (const part of parts) {
      output.set(part, offset);
      offset += part.length;
    }
    return output;
  }

  function sha256Bytes(input) {
    const bytes = requireBytes(input);
    const paddedLength = Math.ceil((bytes.length + 9) / 64) * 64;
    const padded = new Uint8Array(paddedLength);
    padded.set(bytes);
    padded[bytes.length] = 0x80;

    const bitLength = BigInt(bytes.length) * 8n;
    for (let byteIndex = 0; byteIndex < 8; byteIndex += 1) {
      padded[paddedLength - 1 - byteIndex] = Number(
        (bitLength >> BigInt(byteIndex * 8)) & 0xffn
      );
    }

    let h0 = 0x6a09e667;
    let h1 = 0xbb67ae85;
    let h2 = 0x3c6ef372;
    let h3 = 0xa54ff53a;
    let h4 = 0x510e527f;
    let h5 = 0x9b05688c;
    let h6 = 0x1f83d9ab;
    let h7 = 0x5be0cd19;
    const schedule = new Uint32Array(64);

    for (let block = 0; block < padded.length; block += 64) {
      for (let word = 0; word < 16; word += 1) {
        const offset = block + word * 4;
        schedule[word] = (
          (padded[offset] << 24) |
          (padded[offset + 1] << 16) |
          (padded[offset + 2] << 8) |
          padded[offset + 3]
        ) >>> 0;
      }
      for (let word = 16; word < 64; word += 1) {
        const x = schedule[word - 15];
        const y = schedule[word - 2];
        const sigma0 = rotateRight(x, 7) ^ rotateRight(x, 18) ^ (x >>> 3);
        const sigma1 = rotateRight(y, 17) ^ rotateRight(y, 19) ^ (y >>> 10);
        schedule[word] = (
          schedule[word - 16] + sigma0 + schedule[word - 7] + sigma1
        ) >>> 0;
      }

      let a = h0;
      let b = h1;
      let c = h2;
      let d = h3;
      let e = h4;
      let f = h5;
      let g = h6;
      let h = h7;

      for (let round = 0; round < 64; round += 1) {
        const sum1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
        const choose = (e & f) ^ (~e & g);
        const temporary1 = (h + sum1 + choose + ROUND_CONSTANTS[round] + schedule[round]) >>> 0;
        const sum0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
        const majority = (a & b) ^ (a & c) ^ (b & c);
        const temporary2 = (sum0 + majority) >>> 0;

        h = g;
        g = f;
        f = e;
        e = (d + temporary1) >>> 0;
        d = c;
        c = b;
        b = a;
        a = (temporary1 + temporary2) >>> 0;
      }

      h0 = (h0 + a) >>> 0;
      h1 = (h1 + b) >>> 0;
      h2 = (h2 + c) >>> 0;
      h3 = (h3 + d) >>> 0;
      h4 = (h4 + e) >>> 0;
      h5 = (h5 + f) >>> 0;
      h6 = (h6 + g) >>> 0;
      h7 = (h7 + h) >>> 0;
    }

    const digest = new Uint8Array(32);
    const words = [h0, h1, h2, h3, h4, h5, h6, h7];
    for (let index = 0; index < words.length; index += 1) {
      digest[index * 4] = words[index] >>> 24;
      digest[index * 4 + 1] = words[index] >>> 16;
      digest[index * 4 + 2] = words[index] >>> 8;
      digest[index * 4 + 3] = words[index];
    }
    return digest;
  }

  function bytesToHex(bytes) {
    requireBytes(bytes);
    let output = "";
    for (let index = 0; index < bytes.length; index += 1) {
      output += bytes[index].toString(16).padStart(2, "0");
    }
    return output;
  }

  function sha256Hex(input) {
    return bytesToHex(sha256Bytes(input));
  }

  function sha256Utf8(text) {
    return sha256Hex(utf8Bytes(text));
  }

  function requireDomain(domain) {
    if (typeof domain !== "string" || !domain.endsWith("\0")) {
      throw new TypeError("hash domain must be a NUL-terminated string");
    }
    return domain;
  }

  function domainHashBytes(domain, payload) {
    return sha256Hex(
      concatenateBytes([utf8Bytes(requireDomain(domain)), requireBytes(payload, "payload")])
    );
  }

  function domainHashText(domain, text) {
    return domainHashBytes(domain, utf8Bytes(text));
  }

  Q.hash = Object.freeze({
    bytesToHex: bytesToHex,
    concatenateBytes: concatenateBytes,
    domainHashBytes: domainHashBytes,
    domainHashText: domainHashText,
    sha256Bytes: sha256Bytes,
    sha256Hex: sha256Hex,
    sha256Utf8: sha256Utf8,
    utf8Bytes: utf8Bytes,
  });

  // Concise public facade used by the application scripts. Provenance adds
  // canonical JSON helpers after it has loaded.
  Q.Hash = {
    utf8: utf8Bytes,
    sha256Hex: sha256Hex,
  };
})(globalThis);
