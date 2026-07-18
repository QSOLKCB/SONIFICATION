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
 * Forward E8-root-graph tuning profile. It derives ratios from the immutable
 * ETQ-101 selected root graph while keeping absolute clock calibration out of
 * the legacy ETQ-101 v1 model contract.
 */
export const ETQ101_CLOCK_TUNING_PROFILE = Object.freeze({
  profileId: "etq101-e8-root-laplacian-frame-bin-v1",
  status: "candidate-kernel",
  sourceModel: `${MODEL_ID}@${MODEL_VERSION}`,
  semanticScope: "derived-e8-root-graph-observation-profile",
  replacesCanonicalEtq101GeneratorSpectrum: false,
  pitchOperator: "etq101-selected-e8-root-graph-laplacian-v1",
  pitchRatioMap: "sqrt-positive-eigenvalue-v1",
  zeroModePolicy: "omit-dc-v1",
  absoluteUnit: "declared-nominal-audio-frame-bin-v1",
});

/** Derive the ETQ-101 E8 root-graph spectrum and its clock-bin calibration. */
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
