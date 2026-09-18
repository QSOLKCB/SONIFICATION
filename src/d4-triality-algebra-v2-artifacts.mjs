// SPDX-License-Identifier: MPL-2.0

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  MIDI_DIVISION,
  MIDI_VELOCITY,
  PROFILE_ID,
  PROFILE_VERSION,
  buildCanonicalProfileContractV2,
  buildEvaluatedOrbitMatrix,
  buildEventDocumentV2,
} from "./d4-triality-algebra-v2-profile.mjs";
import {
  canonicalObjectSha256,
  canonicalSerialize,
  sha256Bytes,
  utf8,
} from "./etq-v3-canonical.mjs";

const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));

export const ALLOWED_ROOT_ARTIFACT_EXTENSIONS_V2 = Object.freeze([
  ".json",
  ".csv",
  ".mid",
]);

export const IMPLEMENTATION_SOURCE_PATHS_V2 = Object.freeze([
  "src/d4-triality-covariant-engine.mjs",
  "src/d4-triality-s3-equivariance.mjs",
  "src/d4-triality-algebra-v2-profile.mjs",
  "src/d4-triality-algebra-v2-artifacts.mjs",
  "src/etq-v3-canonical.mjs",
  "scripts/build-d4-tia-v2-artifacts.mjs",
]);

export const EVENT_CSV_COLUMNS_V2 = Object.freeze([
  "sequence_index",
  "orbit_index",
  "orbit_label",
  "generator_index",
  "label",
  "family",
  "d_a",
  "d_b",
  "d",
  "m",
  "k",
  "omega",
  "exact_value",
  "value_class_index",
  "unique_orbit_value_count",
  "invariant_expected",
  "onset_tick",
  "orbit_relative_onset_tick",
  "orbit_stride_ticks",
  "duration_ticks",
  "base_midi_note",
  "pitch_offset",
  "midi_note",
  "midi_channel",
  "velocity",
]);

function normalizedSourceBytes(path) {
  const text = readFileSync(resolve(PROJECT_ROOT, path), "utf8")
    .replaceAll("\r\n", "\n")
    .replaceAll("\r", "\n");
  return utf8(text);
}

export function buildImplementationIdentityV2() {
  const sourceFiles = IMPLEMENTATION_SOURCE_PATHS_V2.map((path) => {
    const bytes = normalizedSourceBytes(path);
    return {
      path,
      byteLength: bytes.length,
      sha256: sha256Bytes(bytes),
    };
  });
  const core = {
    sourceNormalization: "UTF-8-text;CRLF-and-CR-normalized-to-LF",
    sourceFiles,
  };
  return {
    ...core,
    sourceBundleSha256: canonicalObjectSha256(
      "qsol.d4-tia-15.source-bundle/v2",
      core,
    ),
  };
}

function csvCell(value) {
  const text = String(value);
  return /[",\n\r]/.test(text)
    ? `"${text.replaceAll('"', '""')}"`
    : text;
}

export function buildCsvReceiverV2(document = buildEventDocumentV2()) {
  const rows = [EVENT_CSV_COLUMNS_V2.join(",")];
  for (const event of document.events) {
    const g = event.grading;
    const e = event.evaluation;
    const r = event.receiverProjection;
    rows.push(
      [
        event.sequenceIndex,
        event.orbitIndex,
        event.orbitLabel,
        event.generatorIndex,
        event.label,
        event.family,
        g.quadraticDegree,
        g.cubicDegree,
        g.covariantDegree,
        g.polynomialDegree,
        g.modularWeight,
        g.covariantOrder,
        e.exactValue,
        e.valueClassIndex,
        e.uniqueOrbitValueCount,
        e.invariantExpected,
        r.onsetTick,
        r.orbitRelativeOnsetTick,
        r.orbitStrideTicks,
        r.durationTicks,
        r.baseMidiNote,
        r.pitchOffset,
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

export function buildMidiReceiverV2(document = buildEventDocumentV2()) {
  if (document.events.length !== 90) {
    throw new Error("D4-TIA-15 v2 MIDI receiver requires 90 orbit events");
  }

  const conductor = trackChunk(
    Buffer.concat([
      metaEvent(0, 0x03, `${PROFILE_ID} v${PROFILE_VERSION}`),
      metaEvent(
        0,
        0x01,
        "evaluated-covariant orbit receiver; no tempo; invariant order-zero controls remain constant across orbit",
      ),
      metaEvent(0, 0x2f),
    ]),
  );

  const generatorTracks = Array.from({ length: 15 }, (_, index) => {
    const generatorIndex = index + 1;
    const related = document.events
      .filter((event) => event.generatorIndex === generatorIndex)
      .sort((left, right) => left.orbitIndex - right.orbitIndex);
    if (related.length !== 6) {
      throw new Error(`generator ${generatorIndex} does not have six orbit events`);
    }

    const first = related[0];
    const g = first.grading;
    const chunks = [
      metaEvent(0, 0x03, first.label),
      metaEvent(
        0,
        0x01,
        `generator=${generatorIndex};omega=${g.covariantOrder};invariant=${first.evaluation.invariantExpected}`,
      ),
    ];

    let previousAbsoluteTick = 0;
    for (const event of related) {
      const r = event.receiverProjection;
      const deltaToOnset = r.onsetTick - previousAbsoluteTick;
      if (deltaToOnset < 0) {
        throw new Error("MIDI generator track events overlap out of order");
      }
      chunks.push(
        metaEvent(
          deltaToOnset,
          0x01,
          `orbit=${event.orbitLabel};value=${event.evaluation.exactValue};class=${event.evaluation.valueClassIndex};offset=${r.pitchOffset}`,
        ),
      );
      chunks.push(
        channelEvent(
          0,
          0x90 | r.midiChannel,
          r.midiNote,
          MIDI_VELOCITY,
        ),
      );
      chunks.push(
        channelEvent(
          r.durationTicks,
          0x80 | r.midiChannel,
          r.midiNote,
          0,
        ),
      );
      previousAbsoluteTick = r.onsetTick + r.durationTicks;
    }
    chunks.push(metaEvent(0, 0x2f));
    return trackChunk(Buffer.concat(chunks));
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

export function buildArtifactBundleV2() {
  const contract = buildCanonicalProfileContractV2();
  const evaluationDocument = buildEvaluatedOrbitMatrix();
  const eventDocument = buildEventDocumentV2();

  const contractBytes = utf8(canonicalSerialize(contract));
  const evaluationBytes = utf8(canonicalSerialize(evaluationDocument));
  const eventBytes = utf8(canonicalSerialize(eventDocument));
  const csvBytes = utf8(buildCsvReceiverV2(eventDocument));
  const midiBytes = buildMidiReceiverV2(eventDocument);

  const artifacts = [
    artifactRecord(
      "contract.json",
      "application/json",
      contractBytes,
      "D4-TIA-15 v2 evaluated-orbit receiver contract",
    ),
    artifactRecord(
      "evaluations.json",
      "application/json",
      evaluationBytes,
      "exact 15-by-6 evaluated covariant orbit matrix",
    ),
    artifactRecord(
      "events.json",
      "application/json",
      eventBytes,
      "lossless 90-event evaluated-orbit document",
    ),
    artifactRecord(
      "events.csv",
      "text/csv",
      csvBytes,
      "auditable exact-value and symbolic-receiver table",
    ),
    artifactRecord(
      "events.mid",
      "audio/midi",
      midiBytes,
      "16-track symbolic MIDI orbit receiver with no tempo event",
    ),
  ].sort((left, right) => left.filename.localeCompare(right.filename));

  const implementation = buildImplementationIdentityV2();
  const manifestCore = {
    schema: "qsol.d4-tia-15.manifest/v2",
    profileId: PROFILE_ID,
    profileVersion: PROFILE_VERSION,
    implementation,
    evaluationDocumentSha256: sha256Bytes(evaluationBytes),
    mappingContractSha256: sha256Bytes(contractBytes),
    eventDocumentSha256: sha256Bytes(eventBytes),
    invariantProjection: eventDocument.invariantProjection,
    artifacts,
    claimBoundary: contract.claimBoundary,
  };
  const manifest = {
    ...manifestCore,
    manifestCoreSha256: canonicalObjectSha256(
      "qsol.d4-tia-15.manifest-core/v2",
      manifestCore,
    ),
  };
  const manifestBytes = utf8(canonicalSerialize(manifest));

  return {
    contract,
    contractBytes,
    evaluationDocument,
    evaluationBytes,
    eventDocument,
    eventBytes,
    csvBytes,
    midiBytes,
    manifest,
    manifestBytes,
  };
}
