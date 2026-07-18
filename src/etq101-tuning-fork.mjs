// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

import {
  MODEL_ID,
  MODEL_VERSION,
  buildGraphLaplacian,
  buildRootAdjacency,
  graphSummary,
  selectEtq101Basis,
} from "./etq-model.mjs";
import { deriveLaplacianClockTuning } from "./tanner-tuning-fork.mjs";

/**
 * Auxiliary E8-root-graph calibration experiment. It derives ratios from the
 * ETQ-101 selected root graph but does not replace the v2 symbolic MIDI
 * codebook, introduce a root-model clock, or define canonical ETQ events.
 */
export const ETQ101_CLOCK_TUNING_PROFILE = Object.freeze({
  profileId: "etq101-e8-root-laplacian-frame-bin-v1",
  status: "auxiliary-noncanonical-calibration",
  sourceModel: `${MODEL_ID}@${MODEL_VERSION}`,
  semanticScope: "auxiliary-e8-root-graph-calibration-experiment",
  canonicalEtq101Mapping: false,
  replacesCanonicalEtq101GeneratorSpectrum: false,
  replacesCanonicalEtq101MidiCodebook: false,
  rootEtq101Clock: "none-symbolic-midi-v2",
  pitchOperator: "etq101-selected-e8-root-graph-laplacian-v1",
  pitchRatioMap: "sqrt-positive-eigenvalue-v1",
  zeroModePolicy: "omit-dc-v1",
  absoluteUnit: "declared-nominal-frame-bin-auxiliary-v1",
});

/** Derive an auxiliary selected-root spectrum and clock-bin calibration. */
export function deriveEtq101ClockTuning({
  sampleRateHz,
  calibrationFrameCount,
  playbackBandHz,
  nyquistGuard = 0.95,
  eigensolver = {},
  grouping = {},
  zeroModeClassification = {},
}) {
  const basis = selectEtq101Basis();
  const adjacency = buildRootAdjacency(basis);
  const laplacian = buildGraphLaplacian(adjacency);
  const spectralTuning = deriveLaplacianClockTuning({
    laplacian,
    sampleRateHz,
    calibrationFrameCount,
    playbackBandHz,
    nyquistGuard,
    eigensolver,
    grouping,
    zeroModeClassification,
  });
  return {
    profile: ETQ101_CLOCK_TUNING_PROFILE,
    graph: graphSummary(adjacency),
    ...spectralTuning,
  };
}
