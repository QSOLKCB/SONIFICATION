// SPDX-License-Identifier: MPL-2.0

import {
  existsSync,
  lstatSync,
  mkdirSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { basename, dirname, extname, isAbsolute, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import {
  ALLOWED_ROOT_ARTIFACT_EXTENSIONS,
  buildArtifactBundle,
} from "../src/d4-triality-algebra-artifacts.mjs";

const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const OUTPUT_ROOT = resolve(PROJECT_ROOT, "dist");
const ALLOWED_EXTENSIONS = new Set(ALLOWED_ROOT_ARTIFACT_EXTENSIONS);

function outputArgument() {
  const index = process.argv.indexOf("--output");
  if (index === -1) return resolve(OUTPUT_ROOT, "d4-tia-15-v1.0.0");
  const value = process.argv[index + 1];
  if (!value) throw new Error("--output requires a path");
  return resolve(value);
}

function assertDedicatedOutputPath(output) {
  const relativeOutput = relative(OUTPUT_ROOT, output);
  if (
    relativeOutput === "" ||
    relativeOutput === ".." ||
    relativeOutput.startsWith(`..${sep}`) ||
    isAbsolute(relativeOutput)
  ) {
    throw new Error(`--output must be a dedicated subdirectory of ${OUTPUT_ROOT}`);
  }
  if (existsSync(output)) {
    if (!lstatSync(output).isDirectory()) {
      throw new Error("--output already exists and is not a directory");
    }
    if (readdirSync(output).length !== 0) {
      throw new Error(
        "--output already exists and is not empty; no recursive deletion is performed",
      );
    }
  }
}

function assertAllowedFilename(filename) {
  if (filename !== basename(filename) || dirname(filename) !== ".") {
    throw new Error(`artifact filename must be a basename: ${filename}`);
  }
  if (!ALLOWED_EXTENSIONS.has(extname(filename))) {
    throw new Error(`root artifact extension is not allowed: ${filename}`);
  }
}

const output = outputArgument();
assertDedicatedOutputPath(output);
mkdirSync(output, { recursive: true });

const bundle = buildArtifactBundle();
const files = new Map([
  ["contract.json", bundle.contractBytes],
  ["events.json", bundle.eventBytes],
  ["events.csv", bundle.csvBytes],
  ["events.mid", bundle.midiBytes],
  ["manifest.json", bundle.manifestBytes],
]);

for (const [filename, bytes] of [...files.entries()].sort(([a], [b]) => a.localeCompare(b))) {
  assertAllowedFilename(filename);
  writeFileSync(resolve(output, filename), bytes, { flag: "wx" });
}

console.log(
  JSON.stringify(
    {
      status: "PASS",
      profile: "D4-TIA-15@1.0.0",
      output,
      fileCount: files.size,
      allowedArtifactExtensions: [...ALLOWED_EXTENSIONS].sort(),
      eventDocumentSha256: bundle.manifest.eventDocumentSha256,
      mappingContractSha256: bundle.manifest.mappingContractSha256,
      manifestCoreSha256: bundle.manifest.manifestCoreSha256,
      implementationSourceBundleSha256:
        bundle.manifest.implementation.sourceBundleSha256,
    },
    null,
    2,
  ),
);
