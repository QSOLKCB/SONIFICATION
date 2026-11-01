// SPDX-License-Identifier: MPL-2.0
import {
  existsSync,
  lstatSync,
  mkdirSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import { fileURLToPath } from "node:url";
import {
  basename,
  dirname,
  extname,
  isAbsolute,
  relative,
  resolve,
  sep,
} from "node:path";

import { buildReceiptAndManifest } from "../src/etq-v3-artifacts.mjs";
import { ALLOWED_ROOT_ARTIFACT_EXTENSIONS } from "../src/etq-v3-receivers.mjs";

const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const OUTPUT_ROOT = resolve(PROJECT_ROOT, "dist");
const ALLOWED_EXTENSIONS = new Set(ALLOWED_ROOT_ARTIFACT_EXTENSIONS);

const RENDERED_AUDIO_OPTION =
  /^--(?:wav|pcm|aiff|flac|mp3|ogg|audio|render-audio)(?:=|$)/i;

function outputArgument(argv = process.argv.slice(2)) {
  let output = resolve(OUTPUT_ROOT, "etq-303-v3.0.0");
  let sawOutput = false;
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (RENDERED_AUDIO_OPTION.test(arg)) {
      throw new Error("rendered-audio request is prohibited in root ETQ: " + arg);
    }
    if (arg === "--output") {
      if (sawOutput) throw new Error("--output may be specified only once");
      const value = argv[i + 1];
      if (!value || value.startsWith("--")) {
        throw new Error("--output requires a path");
      }
      output = resolve(value);
      sawOutput = true;
      i += 1;
      continue;
    }
    throw new Error("unknown option: " + arg);
  }
  return output;
}

function assertNoSymlinkedAncestors(output, relativeOutput) {
  if (!existsSync(OUTPUT_ROOT)) mkdirSync(OUTPUT_ROOT, { recursive: true });
  const root = lstatSync(OUTPUT_ROOT);
  if (root.isSymbolicLink() || !root.isDirectory()) {
    throw new Error("dist output root must be a real directory");
  }
  let current = OUTPUT_ROOT;
  for (const component of relativeOutput.split(sep).filter(Boolean)) {
    current = resolve(current, component);
    if (!existsSync(current)) break;
    const stat = lstatSync(current);
    if (stat.isSymbolicLink()) {
      throw new Error("--output path contains symbolic link: " + current);
    }
    if (!stat.isDirectory()) {
      throw new Error("--output path component is not a directory: " + current);
    }
  }
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
  assertNoSymlinkedAncestors(output, relativeOutput);
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
    throw new Error(`root ETQ artifact extension is not allowed: ${filename}`);
  }
}

const output = outputArgument();
assertDedicatedOutputPath(output);
mkdirSync(output, { recursive: true });
assertDedicatedOutputPath(output);

const bundle = buildReceiptAndManifest();
const files = new Map([
  ["contract.json", bundle.contractBytes],
  ["contract.schema.json", bundle.contractSchemaBytes],
  ...bundle.receiverArtifacts.map((artifact) => [artifact.filename, artifact.bytes]),
  ["observation-receipt.json", bundle.receiptBytes],
  ["manifest.json", bundle.manifestBytes],
]);
for (const [filename, bytes] of [...files.entries()].sort(([left], [right]) => left.localeCompare(right))) {
  assertAllowedFilename(filename);
  writeFileSync(resolve(output, filename), bytes, { flag: "wx" });
}

console.log(
  JSON.stringify(
    {
      status: "PASS",
      output,
      fileCount: files.size,
      allowedArtifactExtensions: [...ALLOWED_EXTENSIONS].sort(),
      manifestCoreSha256: bundle.manifest.manifestCoreSha256,
      receiptCoreSha256: bundle.receipt.receiptCoreSha256,
      contractPayloadSha256: bundle.contract.determinism.contractPayloadSha256,
      implementationSourceBundleSha256:
        bundle.contract.lineage.implementation.sourceBundleSha256,
    },
    null,
    2,
  ),
);
