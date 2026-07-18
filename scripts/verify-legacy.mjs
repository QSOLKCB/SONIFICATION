// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

import {
  buildRootAdjacency,
  selectEtq101Basis,
} from "../src/etq-model.mjs";

const contractBytes = readFileSync(
  new URL("../examples/etq-101.canonical.json", import.meta.url),
  "utf8",
);
const schemaBytes = readFileSync(
  new URL("../spec/etq-101.schema.json", import.meta.url),
  "utf8",
);
const contract = JSON.parse(contractBytes);
const schema = JSON.parse(schemaBytes);

function sha256Utf8(value) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function stableSerialize(value) {
  if (Array.isArray(value)) return `[${value.map(stableSerialize).join(",")}]`;
  if (value !== null && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

const payload = structuredClone(contract);
delete payload.$schema;
delete payload.determinism.contractPayloadSha256;

assert.equal(
  sha256Utf8(contractBytes),
  "7979308580ea443245da456b2356e176a79d8ba1c703b7b163c7d3e421f1d0e0",
);
assert.equal(
  sha256Utf8(schemaBytes),
  "463696338f8ea5db2ff712cfe5fe6f50a2617009dc00ddd93edefc3ca2e566bf",
);
assert.equal(contract.modelVersion, "1.0.0");
assert.equal(contract.constants.goldenRatio, (1 + Math.sqrt(5)) / 2);
assert.equal(contract.constants.referenceFrequencyHz, 432);
assert.equal(
  contract.determinism.contractPayloadSha256,
  "6577443641be02609c045ee0afc423c2be37bbe5ae83f671cbae304c0e9cb930",
);
assert.equal(
  sha256Utf8(stableSerialize(payload)),
  contract.determinism.contractPayloadSha256,
);

const basis = selectEtq101Basis();
const adjacency = buildRootAdjacency(basis);
assert.equal(
  sha256Utf8(JSON.stringify(basis)),
  contract.determinism.basisSha256,
);
assert.equal(
  sha256Utf8(JSON.stringify(adjacency)),
  contract.determinism.adjacencySha256,
);
assert.equal(schema.properties.modelVersion.const, "1.0.0");
assert.equal(schema.properties.constants.properties.referenceFrequencyHz.const, 432);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      validation: "Immutable ETQ-101 v1.0.0 legacy contract and structural hashes",
      contractFileSha256:
        "7979308580ea443245da456b2356e176a79d8ba1c703b7b163c7d3e421f1d0e0",
      schemaFileSha256:
        "463696338f8ea5db2ff712cfe5fe6f50a2617009dc00ddd93edefc3ca2e566bf",
      contractPayloadSha256: contract.determinism.contractPayloadSha256,
    },
    null,
    2,
  ),
);
