// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

/**
 * D4-TIA-15 v2.0.0: evaluated-covariant orbit sonification profile.
 *
 * V2 is downstream of the exact covariant algebra engine and the S3
 * equivariance harness. It evaluates the 15 covariants on one exact authored
 * coefficient probe over six canonical quotient representatives, then maps
 * within-generator exact value order to a small MIDI pitch contour.
 *
 * Covariants of order omega=0 are true SL2 invariants. V2 requires their exact
 * evaluated values and audible-control tuples to remain identical across the
 * six orbit positions.
 */

import {
  buildCovariantBasis,
  rational,
  rationalToString,
  serializePolynomial,
} from "./d4-triality-covariant-engine.mjs";
import {
  S3_LABELS,
  buildModularS3QuotientRepresentatives,
  deriveCoefficientAction,
  substituteCoefficientVariables,
  substituteUv,
} from "./d4-triality-s3-equivariance.mjs";

export const PROFILE_ID = "D4-TIA-15";
export const PROFILE_VERSION = "2.0.0";
export const CONTRACT_SCHEMA_ID = "qsol.d4-tia-15.profile/v2";
export const EVENT_SCHEMA_ID = "qsol.d4-tia-15.events/v2";
export const EVALUATION_SCHEMA_ID = "qsol.d4-tia-15.evaluations/v2";
export const GENERATOR_COUNT = 15;
export const ORBIT_SIZE = 6;
export const EVENT_COUNT = GENERATOR_COUNT * ORBIT_SIZE;
export const MIDI_VELOCITY = 64;
export const MIDI_DIVISION = 1;

export const PROBE_COEFFICIENTS = Object.freeze({
  a0: 1,
  a1: 2,
  a2: 3,
  b0: 4,
  b1: 5,
  b2: 6,
  b3: 7,
});
export const ROBERTS_ANCHOR = Object.freeze({ u: 1, v: 0 });

const PROBE_VARIABLE_VALUES = Object.freeze([
  PROBE_COEFFICIENTS.a0,
  PROBE_COEFFICIENTS.a1,
  PROBE_COEFFICIENTS.a2,
  PROBE_COEFFICIENTS.b0,
  PROBE_COEFFICIENTS.b1,
  PROBE_COEFFICIENTS.b2,
  PROBE_COEFFICIENTS.b3,
  ROBERTS_ANCHOR.u,
  ROBERTS_ANCHOR.v,
]);

export const SOURCE_REFERENCE = Object.freeze({
  author: "Kazuhiro Sakai",
  title: "The ring of D4 triality invariants",
  arxiv: "2504.00546v2",
  year: 2026,
  basis: "Theorem 5.2",
  covariantLaw: "Definition 4.2, equation (4.5)",
  leadingCoefficient: "equations (4.10)-(4.12), Roberts isomorphism",
  grading: "Remark 4.17",
});

function parseRationalText(text) {
  if (typeof text !== "string" || text.length === 0) {
    throw new TypeError("rational text must be non-empty");
  }
  const parts = text.split("/");
  if (parts.length === 1) return rational(BigInt(parts[0]));
  if (parts.length === 2) return rational(BigInt(parts[0]), BigInt(parts[1]));
  throw new TypeError(`invalid rational text: ${text}`);
}

function rationalAdd(left, right) {
  return rational(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

function rationalMultiply(left, right) {
  return rational(
    left.numerator * right.numerator,
    left.denominator * right.denominator,
  );
}

function rationalPower(value, exponent) {
  if (!Number.isSafeInteger(exponent) || exponent < 0) {
    throw new RangeError("rational exponent must be a non-negative safe integer");
  }
  if (exponent === 0) return rational(1n);
  let numerator = 1n;
  let denominator = 1n;
  for (let index = 0; index < exponent; index += 1) {
    numerator *= value.numerator;
    denominator *= value.denominator;
  }
  return rational(numerator, denominator);
}

function rationalCompare(left, right) {
  const difference =
    left.numerator * right.denominator -
    right.numerator * left.denominator;
  return difference < 0n ? -1 : difference > 0n ? 1 : 0;
}

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

export function evaluatePolynomialExact(polynomial, values = PROBE_VARIABLE_VALUES) {
  if (!Array.isArray(values) || values.length !== 9) {
    throw new RangeError("exact evaluation requires nine variable values");
  }
  const rationalValues = values.map((value) => {
    if (typeof value === "number") {
      if (!Number.isSafeInteger(value)) {
        throw new TypeError("numeric probe values must be safe integers");
      }
      return rational(BigInt(value));
    }
    if (
      value &&
      typeof value === "object" &&
      typeof value.numerator === "bigint" &&
      typeof value.denominator === "bigint"
    ) {
      return rational(value.numerator, value.denominator);
    }
    throw new TypeError("probe values must be safe integers or rationals");
  });

  let total = rational(0n);
  for (const term of serializePolynomial(polynomial)) {
    let termValue = parseRationalText(term.coefficient);
    for (let index = 0; index < term.exponents.length; index += 1) {
      const exponent = term.exponents[index];
      if (exponent > 0) {
        termValue = rationalMultiply(
          termValue,
          rationalPower(rationalValues[index], exponent),
        );
      }
    }
    total = rationalAdd(total, termValue);
  }
  return total;
}

function exactValueOrder(values) {
  const byText = new Map();
  for (const value of values) {
    byText.set(rationalToString(value), value);
  }
  return [...byText.entries()]
    .sort((left, right) => rationalCompare(left[1], right[1]))
    .map(([text]) => text);
}

function pitchOffsetForValue(valueText, orderedUniqueValues) {
  const rank = orderedUniqueValues.indexOf(valueText);
  if (rank < 0) throw new Error("evaluated value is absent from exact order");
  return {
    valueClassIndex: rank,
    pitchOffset: rank - Math.floor(orderedUniqueValues.length / 2),
  };
}

function generatorFamily(grade) {
  if (grade.quadraticDegree > 0 && grade.cubicDegree === 0) return "quadratic";
  if (grade.quadraticDegree === 0 && grade.cubicDegree > 0) return "cubic";
  if (grade.quadraticDegree > 0 && grade.cubicDegree > 0) return "joint";
  throw new Error("invalid covariant refined degree");
}

function audibleControlSignature(receiver) {
  return [
    receiver.midiNote,
    receiver.midiChannel,
    receiver.velocity,
    receiver.durationTicks,
  ].join(":");
}

export function buildEvaluatedOrbitMatrix() {
  const basis = buildCovariantBasis();
  if (basis.length !== GENERATOR_COUNT) {
    throw new Error("D4-TIA-15 v2 requires exactly 15 constructed covariants");
  }

  const modular = buildModularS3QuotientRepresentatives();
  const representatives = modular.representatives;
  if (
    representatives.length !== ORBIT_SIZE ||
    representatives.map((entry) => entry.label).join(",") !== S3_LABELS.join(",")
  ) {
    throw new Error("D4-TIA-15 v2 requires the frozen six-representative S3 order");
  }

  const actions = representatives.map((representative) => ({
    ...representative,
    substitutions: deriveCoefficientAction(representative.matrix),
  }));

  const generators = basis.map((generator) => {
    const values = actions.map((action) => {
      const transformedByCoefficients = substituteCoefficientVariables(
        generator.polynomial,
        action.substitutions,
      );
      const transformedByVariables = substituteUv(
        generator.polynomial,
        action.matrix,
      );
      const coefficientValue = evaluatePolynomialExact(
        transformedByCoefficients,
      );
      const variableValue = evaluatePolynomialExact(transformedByVariables);
      if (rationalCompare(coefficientValue, variableValue) !== 0) {
        throw new Error(
          `equivariance evaluation mismatch for ${generator.label} at ${action.label}`,
        );
      }
      return coefficientValue;
    });

    const valueOrder = exactValueOrder(values);
    const invariantExpected = generator.grade.covariantOrder === 0;
    if (invariantExpected && valueOrder.length !== 1) {
      throw new Error(
        `order-zero invariant changed across orbit: ${generator.label}`,
      );
    }

    return {
      generatorIndex: generator.index,
      label: generator.label,
      family: generatorFamily(generator.grade),
      grading: { ...generator.grade },
      invariantExpected,
      exactOrbitValueOrder: valueOrder,
      uniqueOrbitValueCount: valueOrder.length,
      orbitValues: actions.map((action, orbitIndex) => {
        const exactValue = rationalToString(values[orbitIndex]);
        const ranked = pitchOffsetForValue(exactValue, valueOrder);
        return {
          orbitIndex,
          orbitLabel: action.label,
          representativeMatrix: action.matrix.map((row) => [...row]),
          exactValue,
          ...ranked,
          equivarianceVerified: true,
        };
      }),
    };
  });

  return {
    schema: EVALUATION_SCHEMA_ID,
    profileId: PROFILE_ID,
    profileVersion: PROFILE_VERSION,
    probe: {
      coefficients: { ...PROBE_COEFFICIENTS },
      receiverAnchor: { ...ROBERTS_ANCHOR },
      status:
        "authored exact coefficient probe; u=1,v=0 is the leading-coefficient/Roberts anchor",
    },
    orbitOrder: [...S3_LABELS],
    representativeCount: representatives.length,
    generatorCount: generators.length,
    generators,
  };
}

function deriveOrbitStride(evaluation) {
  let maximumEnd = 0;
  for (const generator of evaluation.generators) {
    const grade = generator.grading;
    const end = grade.polynomialDegree + grade.covariantDegree;
    if (end > maximumEnd) maximumEnd = end;
  }
  const stride = maximumEnd + 1;
  if (!Number.isSafeInteger(stride) || stride <= 0) {
    throw new Error("derived orbit stride is invalid");
  }
  return stride;
}

export function buildEvaluatedOrbitEvents() {
  const evaluation = buildEvaluatedOrbitMatrix();
  const orbitStrideTicks = deriveOrbitStride(evaluation);
  const events = [];

  for (let orbitIndex = 0; orbitIndex < ORBIT_SIZE; orbitIndex += 1) {
    for (const generator of evaluation.generators) {
      const grade = generator.grading;
      const value = generator.orbitValues[orbitIndex];
      const onsetTick =
        orbitIndex * orbitStrideTicks + grade.polynomialDegree;
      const durationTicks = grade.covariantDegree;
      const baseMidiNote = requireMidiByte(
        grade.modularWeight,
        "modularWeight/baseMidiNote",
        127,
      );
      const midiNote = requireMidiByte(
        baseMidiNote + value.pitchOffset,
        "evaluated midiNote",
        127,
      );
      const midiChannel = requireMidiByte(
        grade.covariantOrder,
        "covariantOrder/midiChannel",
        15,
      );
      const receiverProjection = {
        onsetTick,
        orbitRelativeOnsetTick: grade.polynomialDegree,
        orbitStrideTicks,
        durationTicks,
        baseMidiNote,
        pitchOffset: value.pitchOffset,
        midiNote,
        midiChannel,
        velocity: MIDI_VELOCITY,
      };

      events.push({
        sequenceIndex: events.length,
        orbitIndex,
        orbitLabel: value.orbitLabel,
        generatorIndex: generator.generatorIndex,
        label: generator.label,
        family: generator.family,
        grading: { ...grade },
        evaluation: {
          exactValue: value.exactValue,
          valueClassIndex: value.valueClassIndex,
          uniqueOrbitValueCount: generator.uniqueOrbitValueCount,
          invariantExpected: generator.invariantExpected,
          equivarianceVerified: value.equivarianceVerified,
        },
        receiverProjection,
      });
    }
  }

  if (events.length !== EVENT_COUNT) {
    throw new Error("D4-TIA-15 v2 event count mismatch");
  }

  for (const generator of evaluation.generators.filter(
    (entry) => entry.invariantExpected,
  )) {
    const related = events.filter(
      (event) => event.generatorIndex === generator.generatorIndex,
    );
    const exactValues = new Set(
      related.map((event) => event.evaluation.exactValue),
    );
    const signatures = new Set(
      related.map((event) =>
        audibleControlSignature(event.receiverProjection),
      ),
    );
    if (exactValues.size !== 1 || signatures.size !== 1) {
      throw new Error(
        `invariant receiver projection changed across orbit: ${generator.label}`,
      );
    }
  }

  return { evaluation, orbitStrideTicks, events };
}

export function buildInvariantProjectionSummary() {
  const { evaluation, events } = buildEvaluatedOrbitEvents();
  const invariantGenerators = evaluation.generators.filter(
    (generator) => generator.invariantExpected,
  );
  const varyingCovariants = evaluation.generators.filter(
    (generator) => !generator.invariantExpected && generator.uniqueOrbitValueCount > 1,
  );

  return {
    invariantGeneratorIndices: invariantGenerators.map(
      (generator) => generator.generatorIndex,
    ),
    invariantGeneratorCount: invariantGenerators.length,
    exactValueInvariantAcrossOrbit: invariantGenerators.every(
      (generator) => generator.uniqueOrbitValueCount === 1,
    ),
    audibleControlInvariantAcrossOrbit: invariantGenerators.every((generator) => {
      const signatures = new Set(
        events
          .filter((event) => event.generatorIndex === generator.generatorIndex)
          .map((event) =>
            audibleControlSignature(event.receiverProjection),
          ),
      );
      return signatures.size === 1;
    }),
    varyingNonInvariantGeneratorCount: varyingCovariants.length,
  };
}

export function buildEventDocumentV2() {
  const { evaluation, orbitStrideTicks, events } = buildEvaluatedOrbitEvents();
  return {
    schema: EVENT_SCHEMA_ID,
    profileId: PROFILE_ID,
    profileVersion: PROFILE_VERSION,
    source: { ...SOURCE_REFERENCE },
    eventCount: events.length,
    generatorCount: GENERATOR_COUNT,
    orbitSize: ORBIT_SIZE,
    eventOrder: "orbit-major-then-published-generator-order",
    orbitOrder: [...S3_LABELS],
    orbitStrideTicks,
    probe: evaluation.probe,
    invariantProjection: buildInvariantProjectionSummary(),
    events,
    claimBoundary:
      "D4-TIA-15 v2 is a deterministic symbolic MIDI sonification of exact evaluated covariant values under six canonical S3 quotient representatives. The exact coefficient probe and the conversion of within-generator exact value rank to MIDI pitch offset are authored receiver conventions. Order-zero covariants are required to keep identical exact values and identical MIDI note/channel/velocity/duration controls across the orbit. MIDI remains symbolic; rendered audio, tempo, tuning, timbre, and listener audibility are external and noncanonical.",
  };
}

export function buildCanonicalProfileContractV2() {
  const { evaluation, orbitStrideTicks } = buildEvaluatedOrbitEvents();
  const invariantProjection = buildInvariantProjectionSummary();
  return {
    schema: CONTRACT_SCHEMA_ID,
    profileId: PROFILE_ID,
    profileVersion: PROFILE_VERSION,
    status: "separate-noncanonical-research-profile",
    lineage: {
      predecessor: "D4-TIA-15@1.0.0",
      algebraEngine: "D4-TIA-COV@0.1.0",
      equivarianceHarness: "D4-TIA-S3-EQUIV@0.1.0",
      relationToEtq:
        "independent profile; does not modify ETQ-101 v2 or ETQ-303 v3 protocol identity",
    },
    source: { ...SOURCE_REFERENCE },
    exactEvaluation: {
      probe: evaluation.probe,
      orbitOrder: [...S3_LABELS],
      representativePolicy:
        "canonical SL2(Z) representatives of the six SL2(Z)/Gamma(2) quotient classes",
      evaluationPoint:
        "transformed coefficients evaluated at authored integer probe; covariant receiver variables fixed at u=1,v=0",
      equivarianceRequirement:
        "Psi(alpha';u,v)=Psi(alpha;u',v') checked exactly before receiver mapping",
    },
    receiverMapping: {
      eventOrder: "orbit-major-then-published-generator-order",
      orbitStrideTicks: {
        value: orbitStrideTicks,
        derivation:
          "1 + max_over_generators(polynomialDegree + covariantDegree)",
      },
      orbitRelativeOnsetTick: {
        source: "polynomial degree m",
        transfer: "identity",
      },
      durationTicks: {
        source: "covariant degree d=d_a+d_b",
        transfer: "identity",
      },
      baseMidiNote: {
        source: "modular weight k",
        transfer: "identity",
      },
      pitchOffset: {
        source:
          "exact evaluated value order within each generator's six-point orbit",
        rule:
          "valueClassIndex - floor(uniqueOrbitValueCount/2), with exact rational equality preserving ties",
        status:
          "authored symbolic receiver mapping; no floating normalization or global cross-generator scale",
      },
      midiNote: "baseMidiNote + pitchOffset",
      midiChannel: {
        source: "covariant order omega",
        transfer: "identity",
      },
      velocity: MIDI_VELOCITY,
      midiDivision: MIDI_DIVISION,
      tempoMicrosecondsPerQuarter: null,
      absoluteFrequencyHz: null,
      renderedAudioStatus: "permanently-disabled-in-root-profile",
    },
    invariantProjection: {
      definition: "covariantOrder omega = 0",
      ...invariantProjection,
      requiredReceiverInvariantFields: [
        "midiNote",
        "midiChannel",
        "velocity",
        "durationTicks",
      ],
      note:
        "orbit block onset changes because the six group positions occur sequentially; the invariant audible-control tuple itself does not change",
    },
    determinism: {
      numericEvaluation: "exact reduced rational arithmetic",
      ranking: "exact rational ascending order; equal values share one class",
      eventCount: EVENT_COUNT,
      runtimeArtifactExtensions: [".json", ".csv", ".mid"],
      noFloatingPointIdentity: true,
    },
    claimBoundary:
      "The algebra, quotient representatives, and covariant transformation law are mathematically grounded. The coefficient probe, temporal layout, and conversion of exact within-orbit value rank to MIDI pitch are authored sonification choices. Receiver invariance for order-zero generators is exact at the symbolic MIDI-control level, not a guarantee about any external synthesizer, room, listener, or physical interpretation.",
  };
}
