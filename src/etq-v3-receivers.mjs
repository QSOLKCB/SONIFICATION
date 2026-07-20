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

function csvCell(value) {
  if (value === null) return "";
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export const EVENT_CSV_COLUMNS = Object.freeze([
  "sequence_index",
  "tensor_index",
  "site_index",
  "fibre_label",
  "base_state_type",
  "fixed_index",
  "orbit_index",
  "internal_triality_label",
  "root_0",
  "root_1",
  "root_2",
  "root_3",
  "root_4",
  "root_5",
  "root_6",
  "root_7",
  "base_degree",
  "lifted_degree",
  "degree_potential_numerator",
  "degree_potential_denominator",
  "transition_phase_gaussian_exponent",
  "transition_phase_symbol",
  "next_sequence_index",
  "next_tensor_index",
  "v2_midi_note",
  "midi_channel_zero_based",
]);

export function buildCsvReceiver(eventDocument = buildEventDocument()) {
  const sites = eventDocument.siteRegistry;
  const rows = [EVENT_CSV_COLUMNS.join(",")];
  for (const event of eventDocument.events) {
    const site = sites[event.siteIndex];
    const row = [
      event.sequenceIndex,
      event.tensorIndex,
      event.siteIndex,
      event.fibreLabel,
      site.baseStateType,
      site.fixedIndex,
      site.orbitIndex,
      site.internalTrialityLabel,
      ...site.rootDoubled,
      site.baseDegree,
      site.liftedDegree,
      site.degreePotentialNumerator,
      site.degreePotentialDenominator,
      event.transitionPhaseGaussianExponent,
      event.transitionPhaseSymbol,
      event.nextSequenceIndex,
      event.nextTensorIndex,
      site.v2MidiNote,
      event.fibreLabel,
    ];
    rows.push(row.map(csvCell).join(","));
  }
  return `${rows.join("\n")}\n`;
}

export function buildNdjsonReceiver(eventDocument = buildEventDocument()) {
  return `${eventDocument.events
    .map((event) => {
      const site = eventDocument.siteRegistry[event.siteIndex];
      return canonicalSerialize({
        modelId: MODEL_ID,
        modelVersion: MODEL_VERSION,
        ...event,
        site,
      });
    })
    .join("\n")}\n`;
}

function xmlEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export function buildGraphmlReceiver(
  eventDocument = buildEventDocument(),
  liftedGraph = buildLiftedGraph(),
) {
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
    '  <key id="site" for="node" attr.name="site_index" attr.type="int"/>',
    '  <key id="fibre" for="node" attr.name="fibre_label" attr.type="int"/>',
    '  <key id="event" for="node" attr.name="event_index" attr.type="int"/>',
    '  <key id="root" for="node" attr.name="root_doubled" attr.type="string"/>',
    '  <key id="degree" for="node" attr.name="lifted_degree" attr.type="int"/>',
    '  <key id="kind" for="edge" attr.name="edge_kind" attr.type="string"/>',
    '  <graph id="ETQ-303" edgedefault="undirected">',
  ];
  for (let siteIndex = 0; siteIndex < BASE_SITE_COUNT; siteIndex += 1) {
    const site = eventDocument.siteRegistry[siteIndex];
    for (let fibreLabel = 0; fibreLabel < FIBRE_DIMENSION; fibreLabel += 1) {
      const index = tensorIndex(siteIndex, fibreLabel);
      const eventIndex = eventIndexFromAddress(siteIndex, fibreLabel);
      lines.push(
        `    <node id="n${String(index).padStart(3, "0")}">`,
        `      <data key="site">${siteIndex}</data>`,
        `      <data key="fibre">${fibreLabel}</data>`,
        `      <data key="event">${eventIndex}</data>`,
        `      <data key="root">${xmlEscape(site.rootDoubled.join(","))}</data>`,
        `      <data key="degree">${site.liftedDegree}</data>`,
        "    </node>",
      );
    }
  }
  liftedGraph.edges.forEach((edge, edgeIndex) => {
    lines.push(
      `    <edge id="e${String(edgeIndex).padStart(4, "0")}" ` +
        `source="n${String(edge.source).padStart(3, "0")}" ` +
        `target="n${String(edge.target).padStart(3, "0")}">`,
      `      <data key="kind">${edge.kind}</data>`,
      "    </edge>",
    );
  });
  lines.push("  </graph>", "</graphml>", "");
  return lines.join("\n");
}

export function buildSvgReceiver(eventDocument = buildEventDocument()) {
  const cellWidth = 10;
  const rowHeight = 36;
  const marginLeft = 24;
  const marginTop = 32;
  const width = marginLeft * 2 + BASE_SITE_COUNT * cellWidth;
  const height = marginTop * 2 + FIBRE_DIMENSION * rowHeight;
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    "  <title>ETQ-303 v3 exact event atlas</title>",
    "  <desc>Three fibre rows over the preserved 101-site ETQ-101 selector order. Rectangle metadata identifies the exact 303-event traversal.</desc>",
    "  <style>text{font-family:monospace;font-size:9px}.node{fill:none;stroke:currentColor;stroke-width:1}.label{font-size:10px}</style>",
    `  <text class="label" x="${marginLeft}" y="16">ETQ-303 v3 · 101 × 3 exact tensor-state atlas</text>`,
  ];
  for (let fibreLabel = 0; fibreLabel < FIBRE_DIMENSION; fibreLabel += 1) {
    const y = marginTop + fibreLabel * rowHeight;
    lines.push(`  <text x="2" y="${y + 8}">a=${fibreLabel}</text>`);
    for (let siteIndex = 0; siteIndex < BASE_SITE_COUNT; siteIndex += 1) {
      const x = marginLeft + siteIndex * cellWidth;
      const index = tensorIndex(siteIndex, fibreLabel);
      const eventIndex = eventIndexFromAddress(siteIndex, fibreLabel);
      const site = eventDocument.siteRegistry[siteIndex];
      lines.push(
        `  <rect class="node" x="${x}" y="${y}" width="7" height="12" ` +
          `data-tensor-index="${index}" data-event-index="${eventIndex}" ` +
          `data-site-index="${siteIndex}" data-fibre-label="${fibreLabel}" ` +
          `data-base-degree="${site.baseDegree}">` +
          `<title>event ${eventIndex}; tensor ${index}; site ${siteIndex}; fibre ${fibreLabel}; root ${xmlEscape(site.rootDoubled.join(","))}</title></rect>`,
      );
    }
  }
  lines.push("</svg>", "");
  return lines.join("\n");
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

/**
 * Deterministic symbolic MIDI receiver.
 *
 * Channel = independent v3 fibre label; note = preserved v2 symbolic codebook.
 * One integer tick is assigned per event. No tempo meta-event is emitted, so
 * seconds remain receiver-defined and noncanonical.
 */
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
    ...Buffer.from("MThd", "ascii"),
    0, 0, 0, 6,
    0, 0,
    0, 1,
    0, 1,
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
      receiverId: "ndjson-stream-v1",
      filename: "events.ndjson",
      mediaType: "application/x-ndjson",
      bytes: utf8(buildNdjsonReceiver(eventDocument)),
      semantics: "one-lossless-enriched-event-per-line",
    },
    {
      receiverId: "cartesian-graphml-v1",
      filename: "graph.graphml",
      mediaType: "application/graphml+xml",
      bytes: utf8(buildGraphmlReceiver(eventDocument, liftedGraph)),
      semantics: "exact-G101-cartesian-C3-graph",
    },
    {
      receiverId: "svg-event-atlas-v1",
      filename: "events.svg",
      mediaType: "image/svg+xml",
      bytes: utf8(buildSvgReceiver(eventDocument)),
      semantics: "integer-grid-event-atlas",
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
