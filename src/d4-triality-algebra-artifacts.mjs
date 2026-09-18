// SPDX-License-Identifier: MPL-2.0

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  MIDI_DIVISION,
  MIDI_VELOCITY,
  PROFILE_ID,
  PROFILE_VERSION,
  buildCanonicalProfileContract,
  buildEventDocument,
} from "./d4-triality-algebra-profile.mjs";
import {
  canonicalObjectSha256,
  canonicalSerialize,
  sha256Bytes,
  utf8,
} from "./etq-v3-canonical.mjs";

const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));

export const ALLOWED_ROOT_ARTIFACT_EXTENSIONS = Object.freeze([
  ".json",
  ".csv",
  ".mid",
]);

export const IMPLEMENTATION_SOURCE_PATHS = Object.freeze([
  "src/d4-triality-reference.mjs",
  "src/d4-triality-algebra-profile.mjs",
  "src/d4-triality-algebra-artifacts.mjs",
  "src/etq-v3-canonical.mjs",
  "scripts/build-d4-tia-artifacts.mjs",
]);

export const EVENT_CSV_COLUMNS = Object.freeze([
  "sequence_index",
  "generator_index",
  "label",
  "family",
  "d_a",
  "d_b",
  "d",
  "m",
  "k",
  "omega",
  "onset_tick",
  "duration_ticks",
  "midi_note",
  "midi_channel",
  "velocity",
]);

function sha256File(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

export function buildImplementationIdentity() {
  const sourceFiles = IMPLEMENTATION_SOURCE_PATHS.map((path) => ({
    path,
    sha256: sha256File(resolve(PROJECT_ROOT, path)),
  }));
  return {
    sourceFiles,
    sourceBundleSha256: canonicalObjectSha256(
      "qsol.d4-tia-15.source-bundle/v1",
      sourceFiles,
    ),
  };
}

function csvCell(value) {
  const text = String(value);
  return /[",\n\r]/.test(text)
    ? `"${text.replaceAll('"', '""')}"`
    : text;
}

export function buildCsvReceiver(document = buildEventDocument()) {
  const rows = [EVENT_CSV_COLUMNS.join(",")];
  for (const event of document.events) {
    const g = event.grading;
    const r = event.receiverProjection;
    rows.push(
      [
        event.sequenceIndex,
        event.generatorIndex,
        event.label,
        event.family,
        g.quadraticDegree,
        g.cubicDegree,
        g.covariantDegree,
        g.polynomialDegree,
        g.modularWeight,
        g.covariantOrder,
        r.onsetTick,
        r.durationTicks,
        r.midiNote,
        r.midiChannel,
        r.velocity,
      ]
        .map(csvCell)
        .join(","),
    );
  }
  return `${rows.join("\n")}\n`;
}

function variableLengthQuantity(value) {
  if (!Number.isSafeInteger(value) || value < 0 || value > 0x0fffffff) {
    throw new RangeError("MIDI delta-time must be a 28-bit non-negative integer");
  }
  let buffer = value & 0x7f;
  const bytes = [];
  while ((value >>= 7) > 0) {
    buffer <<= 8;
    buffer |= (value & 0x7f) | 0x80;
  }
  while (true) {
    bytes.push(buffer & 0xff);
    if (buffer & 0x80) buffer >>= 8;
    else break;
  }
  return Buffer.from(bytes);
}

function metaEvent(delta, type, text = "") {
  const payload = Buffer.from(text, "utf8");
  return Buffer.concat([
    variableLengthQuantity(delta),
    Buffer.from([0xff, type]),
    variableLengthQuantity(payload.length),
    payload,
  ]);
}

function channelEvent(delta, status, data1, data2) {
  return Buffer.concat([
    variableLengthQuantity(delta),
    Buffer.from([status, data1, data2]),
  ]);
}

function trackChunk(payload) {
  const header = Buffer.alloc(8);
  header.write("MTrk", 0, 4, "ascii");
  header.writeUInt32BE(payload.length, 4);
  return Buffer.concat([header, payload]);
}

export function buildMidiReceiver(document = buildEventDocument()) {
  if (document.events.length !== 15) {
    throw new Error("D4-TIA-15 MIDI receiver requires 15 generator events");
  }

  const conductor = trackChunk(
    Buffer.concat([
      metaEvent(0, 0x03, `${PROFILE_ID} v${PROFILE_VERSION}`),
      metaEvent(
        0,
        0x01,
        "symbolic receiver; tempo omitted; tuning, timbre and loudness external",
      ),
      metaEvent(0, 0x2f),
    ]),
  );

  const generatorTracks = document.events.map((event) => {
    const g = event.grading;
    const r = event.receiverProjection;
    const metadata =
      `index=${event.generatorIndex};da=${g.quadraticDegree};db=${g.cubicDegree};` +
      `d=${g.covariantDegree};m=${g.polynomialDegree};k=${g.modularWeight};` +
      `omega=${g.covariantOrder}`;
    const noteOnStatus = 0x90 | r.midiChannel;
    const noteOffStatus = 0x80 | r.midiChannel;

    return trackChunk(
      Buffer.concat([
        metaEvent(0, 0x03, event.label),
        metaEvent(0, 0x01, metadata),
        channelEvent(r.onsetTick, noteOnStatus, r.midiNote, MIDI_VELOCITY),
        channelEvent(r.durationTicks, noteOffStatus, r.midiNote, 0),
        metaEvent(0, 0x2f),
      ]),
    );
  });

  const header = Buffer.alloc(14);
  header.write("MThd", 0, 4, "ascii");
  header.writeUInt32BE(6, 4);
  header.writeUInt16BE(1, 8);
  header.writeUInt16BE(1 + generatorTracks.length, 10);
  header.writeUInt16BE(MIDI_DIVISION, 12);

  return Buffer.concat([header, conductor, ...generatorTracks]);
}

function artifactRecord(filename, mediaType, bytes, semantics) {
  return {
    filename,
    mediaType,
    semantics,
    byteLength: bytes.length,
    sha256: sha256Bytes(bytes),
  };
}

export function buildArtifactBundle() {
  const contract = buildCanonicalProfileContract();
  const eventDocument = buildEventDocument();

  const contractBytes = utf8(canonicalSerialize(contract));
  const eventBytes = utf8(canonicalSerialize(eventDocument));
  const csvBytes = utf8(buildCsvReceiver(eventDocument));
  const midiBytes = buildMidiReceiver(eventDocument);

  const artifacts = [
    artifactRecord(
      "contract.json",
      "application/json",
      contractBytes,
      "versioned mapping contract",
    ),
    artifactRecord(
      "events.json",
      "application/json",
      eventBytes,
      "lossless 15-generator event document",
    ),
    artifactRecord(
      "events.csv",
      "text/csv",
      csvBytes,
      "auditable grading/event table",
    ),
    artifactRecord(
      "events.mid",
      "audio/midi",
      midiBytes,
      "symbolic MIDI projection with no canonical tempo or tuning",
    ),
  ].sort((left, right) => left.filename.localeCompare(right.filename));

  const implementation = buildImplementationIdentity();
  const manifestCore = {
    schema: "qsol.d4-tia-15.manifest/v1",
    profileId: PROFILE_ID,
    profileVersion: PROFILE_VERSION,
    implementation,
    sourceLedgerSha256: canonicalObjectSha256(
      "qsol.d4-tia-15.ledger/v1",
      eventDocument.events.map((event) => ({
        generatorIndex: event.generatorIndex,
        label: event.label,
        grading: event.grading,
      })),
    ),
    mappingContractSha256: sha256Bytes(contractBytes),
    eventDocumentSha256: sha256Bytes(eventBytes),
    artifacts,
    claimBoundary: contract.claimBoundary,
  };
  const manifest = {
    ...manifestCore,
    manifestCoreSha256: canonicalObjectSha256(
      "qsol.d4-tia-15.manifest-core/v1",
      manifestCore,
    ),
  };
  const manifestBytes = utf8(canonicalSerialize(manifest));

  return {
    contract,
    contractBytes,
    eventDocument,
    eventBytes,
    csvBytes,
    midiBytes,
    manifest,
    manifestBytes,
  };
}
