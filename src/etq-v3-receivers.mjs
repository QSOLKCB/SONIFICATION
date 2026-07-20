// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

import {
  BASE_SITE_COUNT,
  EVENT_COUNT,
  FIBRE_DIMENSION,
  MODEL_ID,
  MODEL_VERSION,
  buildEventDocument,
  buildLiftedGraph,
  eventIndexFromAddress,
  tensorIndex,
} from "./etq-v3-core.mjs";
import { canonicalSerialize, utf8 } from "./etq-v3-canonical.mjs";

export const EVENT_DOCUMENT_FILENAME = "events.json";
export const ALLOWED_ROOT_ARTIFACT_EXTENSIONS = Object.freeze([".json", ".csv", ".mid"]);

function csvCell(value) {
  if (value === null) return "";
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export const EVENT_CSV_COLUMNS = Object.freeze([
  "sequence_index", "tensor_index", "site_index", "fibre_label",
  "base_state_type", "fixed_index", "orbit_index", "internal_triality_label",
  "root_0", "root_1", "root_2", "root_3", "root_4", "root_5", "root_6", "root_7",
  "base_degree", "lifted_degree", "degree_potential_numerator",
  "degree_potential_denominator", "transition_phase_gaussian_exponent",
  "transition_phase_symbol", "next_sequence_index", "next_tensor_index",
  "v2_midi_note", "midi_channel_zero_based",
]);

export function buildCsvReceiver(eventDocument = buildEventDocument()) {
  const rows = [EVENT_CSV_COLUMNS.join(",")];
  for (const event of eventDocument.events) {
    const site = eventDocument.siteRegistry[event.siteIndex];
    const row = [
      event.sequenceIndex, event.tensorIndex, event.siteIndex, event.fibreLabel,
      site.baseStateType, site.fixedIndex, site.orbitIndex, site.internalTrialityLabel,
      ...site.rootDoubled, site.baseDegree, site.liftedDegree,
      site.degreePotentialNumerator, site.degreePotentialDenominator,
      event.transitionPhaseGaussianExponent, event.transitionPhaseSymbol,
      event.nextSequenceIndex, event.nextTensorIndex, site.v2MidiNote, event.fibreLabel,
    ];
    rows.push(row.map(csvCell).join(","));
  }
  return `${rows.join("\n")}\n`;
}

export function buildGraphJsonReceiver(
  eventDocument = buildEventDocument(),
  liftedGraph = buildLiftedGraph(),
) {
  const nodes = [];
  for (let siteIndex = 0; siteIndex < BASE_SITE_COUNT; siteIndex += 1) {
    const site = eventDocument.siteRegistry[siteIndex];
    for (let fibreLabel = 0; fibreLabel < FIBRE_DIMENSION; fibreLabel += 1) {
      nodes.push({
        tensorIndex: tensorIndex(siteIndex, fibreLabel),
        eventIndex: eventIndexFromAddress(siteIndex, fibreLabel),
        siteIndex,
        fibreLabel,
        rootDoubled: [...site.rootDoubled],
        baseStateType: site.baseStateType,
        internalTrialityLabel: site.internalTrialityLabel,
        baseDegree: site.baseDegree,
        liftedDegree: site.liftedDegree,
      });
    }
  }
  return canonicalSerialize({
    schema: "qsol.etq-303.graph-receiver/v1",
    modelId: MODEL_ID,
    modelVersion: MODEL_VERSION,
    construction: liftedGraph.construction,
    vertexCount: liftedGraph.vertexCount,
    edgeCount: liftedGraph.edgeCount,
    connected: liftedGraph.connected,
    minimumDegree: liftedGraph.minimumDegree,
    maximumDegree: liftedGraph.maximumDegree,
    nodes,
    edges: liftedGraph.edges.map((edge) => ({ ...edge })),
    claimBoundary:
      "Exact Cartesian graph data for G_101 square C_3; the canonical event sequence is not claimed to be a graph walk.",
  });
}

export function buildEventAtlasJsonReceiver(eventDocument = buildEventDocument()) {
  const entries = [];
  for (let fibreLabel = 0; fibreLabel < FIBRE_DIMENSION; fibreLabel += 1) {
    for (let siteIndex = 0; siteIndex < BASE_SITE_COUNT; siteIndex += 1) {
      const site = eventDocument.siteRegistry[siteIndex];
      entries.push({
        x: siteIndex,
        y: fibreLabel,
        tensorIndex: tensorIndex(siteIndex, fibreLabel),
        eventIndex: eventIndexFromAddress(siteIndex, fibreLabel),
        siteIndex,
        fibreLabel,
        baseDegree: site.baseDegree,
        liftedDegree: site.liftedDegree,
      });
    }
  }
  return canonicalSerialize({
    schema: "qsol.etq-303.event-atlas/v1",
    modelId: MODEL_ID,
    modelVersion: MODEL_VERSION,
    coordinateSemantics: "x=siteIndex;y=fibreLabel",
    columns: BASE_SITE_COUNT,
    rows: FIBRE_DIMENSION,
    entryCount: EVENT_COUNT,
    entries,
  });
}

function encodeVariableLength(value) {
  if (!Number.isSafeInteger(value) || value < 0 || value > 0x0fffffff) {
    throw new RangeError("MIDI variable-length value outside supported range");
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
  return bytes;
}

function uint32be(value) {
  return [(value >>> 24) & 0xff, (value >>> 16) & 0xff, (value >>> 8) & 0xff, value & 0xff];
}

export function buildMidiReceiver(eventDocument = buildEventDocument()) {
  const track = [];
  const pushMetaText = (type, text) => {
    const bytes = [...Buffer.from(text, "utf8")];
    track.push(0, 0xff, type, ...encodeVariableLength(bytes.length), ...bytes);
  };
  pushMetaText(0x03, "ETQ-303 v3 exact event traversal");
  pushMetaText(0x01, "Symbolic only: channel=fibre, note=ETQ-101 v2 code; no canonical tempo or hertz");
  for (const event of eventDocument.events) {
    const site = eventDocument.siteRegistry[event.siteIndex];
    const channel = event.fibreLabel;
    const note = site.v2MidiNote;
    track.push(0, 0x90 | channel, note, 64);
    track.push(1, 0x80 | channel, note, 0);
  }
  track.push(0, 0xff, 0x2f, 0);
  const header = [
    ...Buffer.from("MThd", "ascii"), 0, 0, 0, 6, 0, 0, 0, 1, 0, 1,
  ];
  const trackHeader = [...Buffer.from("MTrk", "ascii"), ...uint32be(track.length)];
  return Buffer.from([...header, ...trackHeader, ...track]);
}

export function buildReceiverArtifacts(eventDocument = buildEventDocument()) {
  const liftedGraph = buildLiftedGraph();
  return [
    {
      receiverId: "canonical-json-v1",
      filename: EVENT_DOCUMENT_FILENAME,
      mediaType: "application/json",
      bytes: utf8(canonicalSerialize(eventDocument)),
      semantics: "canonical-core-event-document",
    },
    {
      receiverId: "csv-table-v1",
      filename: "events.csv",
      mediaType: "text/csv",
      bytes: utf8(buildCsvReceiver(eventDocument)),
      semantics: "lossless-tabular-event-projection",
    },
    {
      receiverId: "cartesian-graph-json-v1",
      filename: "graph.json",
      mediaType: "application/json",
      bytes: utf8(buildGraphJsonReceiver(eventDocument, liftedGraph)),
      semantics: "exact-G101-cartesian-C3-graph",
    },
    {
      receiverId: "event-atlas-json-v1",
      filename: "event-atlas.json",
      mediaType: "application/json",
      bytes: utf8(buildEventAtlasJsonReceiver(eventDocument)),
      semantics: "integer-grid-event-atlas-metadata",
    },
    {
      receiverId: "symbolic-midi-channel-v1",
      filename: "events.mid",
      mediaType: "audio/midi",
      bytes: buildMidiReceiver(eventDocument),
      semantics: "fibre-to-channel-and-preserved-v2-note-code",
    },
  ];
}
