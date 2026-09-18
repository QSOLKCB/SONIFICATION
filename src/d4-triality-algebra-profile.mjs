// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

/**
 * D4-TIA-15 v1.0.0: triality-invariant algebra sonification profile.
 *
 * This is a separately versioned, receiver-neutral research profile over the
 * 15-generator minimal basis recorded from Sakai's 2026 D4 triality-invariant
 * ring. It does not modify ETQ-101 or ETQ-303 identity.
 */

import { D4_TRIALITY_INVARIANT_GENERATORS } from "./d4-triality-reference.mjs";

export const PROFILE_ID = "D4-TIA-15";
export const PROFILE_VERSION = "1.0.0";
export const CONTRACT_SCHEMA_ID = "qsol.d4-tia-15.profile/v1";
export const EVENT_SCHEMA_ID = "qsol.d4-tia-15.events/v1";
export const GENERATOR_COUNT = 15;
export const MIDI_VELOCITY = 64;
export const MIDI_DIVISION = 1;

export const SOURCE_REFERENCE = Object.freeze({
  author: "Kazuhiro Sakai",
  title: "The ring of D4 triality invariants",
  arxiv: "2504.00546v2",
  year: 2026,
  theorem: "Theorem 5.2 / equation (5.23) minimal 15-generator basis",
  grading: "Theorem 4.10 and Remark 4.17",
});

function requireSafeNonnegative(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new RangeError(`${name} must be a non-negative safe integer`);
  }
  return value;
}

function requireMidiByte(value, name, maximum) {
  requireSafeNonnegative(value, name);
  if (value > maximum) {
    throw new RangeError(`${name} exceeds MIDI range ${maximum}`);
  }
  return value;
}

export function generatorFamily(generator) {
  const da = requireSafeNonnegative(generator.quadraticDegree, "quadraticDegree");
  const db = requireSafeNonnegative(generator.cubicDegree, "cubicDegree");
  if (da > 0 && db === 0) return "quadratic";
  if (da === 0 && db > 0) return "cubic";
  if (da > 0 && db > 0) return "joint";
  throw new RangeError("generator must have positive quadratic or cubic degree");
}

export function buildGeneratorEvents() {
  if (D4_TRIALITY_INVARIANT_GENERATORS.length !== GENERATOR_COUNT) {
    throw new Error("D4-TIA-15 requires the published 15-generator ledger");
  }

  return D4_TRIALITY_INVARIANT_GENERATORS.map((generator, sequenceIndex) => {
    const da = requireSafeNonnegative(generator.quadraticDegree, "quadraticDegree");
    const db = requireSafeNonnegative(generator.cubicDegree, "cubicDegree");
    const m = requireSafeNonnegative(generator.polynomialDegree, "polynomialDegree");
    const k = requireSafeNonnegative(generator.modularWeight, "modularWeight");
    const omega = requireSafeNonnegative(generator.covariantOrder, "covariantOrder");
    const covariantDegree = da + db;

    if (!Number.isSafeInteger(covariantDegree) || covariantDegree <= 0) {
      throw new RangeError("covariant degree must be a positive safe integer");
    }
    if (k !== 4 * da + 6 * db + m) {
      throw new Error("published modular-weight grading relation failed");
    }
    if (omega !== 2 * da + 3 * db - m) {
      throw new Error("published covariant-order grading relation failed");
    }
    if (omega !== (k - 3 * m) / 2) {
      throw new Error("published weight/order relation failed");
    }

    const onsetTick = m;
    const durationTicks = covariantDegree;
    const midiNote = requireMidiByte(k, "modularWeight/midiNote", 127);
    const midiChannel = requireMidiByte(omega, "covariantOrder/midiChannel", 15);

    return Object.freeze({
      sequenceIndex,
      generatorIndex: generator.index,
      label: generator.label,
      family: generatorFamily(generator),
      grading: Object.freeze({
        quadraticDegree: da,
        cubicDegree: db,
        covariantDegree,
        polynomialDegree: m,
        modularWeight: k,
        covariantOrder: omega,
      }),
      receiverProjection: Object.freeze({
        onsetTick,
        durationTicks,
        midiNote,
        midiChannel,
        velocity: MIDI_VELOCITY,
      }),
    });
  });
}

export function buildEventDocument() {
  return {
    schema: EVENT_SCHEMA_ID,
    profileId: PROFILE_ID,
    profileVersion: PROFILE_VERSION,
    source: { ...SOURCE_REFERENCE },
    generatorCount: GENERATOR_COUNT,
    eventOrder: "published-minimal-generator-basis-order",
    events: buildGeneratorEvents(),
    claimBoundary:
      "D4-TIA-15 is a deterministic symbolic sonification profile over a published 15-generator D4 triality-invariant covariant basis. The grading data are preserved exactly; assignment of grades to MIDI fields is an authored identity-transfer receiver convention, not a theorem, physical model, or empirical validation.",
  };
}

export function buildCanonicalProfileContract() {
  return {
    schema: CONTRACT_SCHEMA_ID,
    profileId: PROFILE_ID,
    profileVersion: PROFILE_VERSION,
    status: "separate-noncanonical-research-profile",
    source: { ...SOURCE_REFERENCE },
    publishedStructure: {
      generatorCount: GENERATOR_COUNT,
      refinedDegrees: ["d_a", "d_b"],
      covariantDegree: "d=d_a+d_b",
      polynomialDegree: "m",
      modularWeight: "k",
      covariantOrder: "omega",
      gradingRelations: [
        "k=4*d_a+6*d_b+m",
        "omega=2*d_a+3*d_b-m",
        "omega=(k-3*m)/2",
      ],
    },
    mapping: {
      eventOrder: {
        source: "published 15-generator basis order",
        transfer: "identity",
      },
      onsetTick: {
        source: "polynomial degree m",
        transfer: "identity",
      },
      durationTicks: {
        source: "covariant degree d=d_a+d_b",
        transfer: "identity",
      },
      midiNote: {
        source: "modular weight k",
        transfer: "identity",
      },
      midiChannel: {
        source: "covariant order omega",
        transfer: "identity",
      },
      quadraticDegree: {
        source: "refined degree d_a",
        transfer: "preserved as event metadata",
      },
      cubicDegree: {
        source: "refined degree d_b",
        transfer: "preserved as event metadata",
      },
      velocity: {
        value: MIDI_VELOCITY,
        status: "authored receiver constant; not grading data",
      },
      midiDivision: {
        value: MIDI_DIVISION,
        status: "symbolic tick resolution; no canonical tempo",
      },
      tempoMicrosecondsPerQuarter: null,
      absoluteFrequencyHz: null,
      receiverTuning: "external-and-nonnormative",
      renderedAudioStatus: "permanently-disabled-in-root-profile",
    },
    determinism: {
      numericAbi: "safe-integers-only",
      eventCount: GENERATOR_COUNT,
      runtimeArtifactExtensions: [".json", ".csv", ".mid"],
    },
    lineage: {
      relationToEtq:
        "independent profile; does not modify ETQ-101 v2 or ETQ-303 v3 protocol identity",
      referenceBridge: "docs/D4_TRIALITY_REFERENCE_BRIDGE.md",
    },
    claimBoundary:
      "The 15 source generators and their grading ledger are literature-derived. Their direct placement into MIDI note/channel/tick fields is an authored sonification convention chosen to avoid scaling, normalization, or invented latent quantities. MIDI is symbolic; tempo, tuning, timbre, loudness, and rendered audio are outside profile identity.",
  };
}
