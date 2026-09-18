// SPDX-License-Identifier: MPL-2.0

import {
  existsSync,
  lstatSync,
  mkdirSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import {
  basename,
  dirname,
  extname,
  isAbsolute,
  relative,
  resolve,
  sep,
} from "node:path";
import { fileURLToPath } from "node:url";

import {
  ALLOWED_ROOT_ARTIFACT_EXTENSIONS,
  buildArtifactBundle,
} from "../src/d4-triality-algebra-artifacts.mjs";

const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const OUTPUT_ROOT = resolve(PROJECT_ROOT, "dist");
const ALLOWED_EXTENSIONS = new Set(ALLOWED_ROOT_ARTIFACT_EXTENSIONS);
const RENDERED_AUDIO_OPTION =
  /^--(?:wav|pcm|aiff|flac|mp3|ogg|audio|render-audio)(?:=|$)/i;

function parseArguments(argv = process.argv.slice(2)) {
  let output = resolve(OUTPUT_ROOT, "d4-tia-15-v1.0.0");
  let sawOutput = false;

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];

    if (RENDERED_AUDIO_OPTION.test(argument)) {
      throw new Error(
        `rendered-audio request is prohibited in the root D4-TIA profile: ${argument}`,
      );
    }

    if (argument === "--output") {
      if (sawOutput) throw new Error("--output may be specified only once");
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) {
        throw new Error("--output requires a path");
      }
      output = resolve(value);
      sawOutput = true;
      index += 1;
      continue;
    }

    throw new Error(`unknown option: ${argument}`);
  }

  return output;
}

function assertLexicallyInsideOutputRoot(output) {
  const relativeOutput = relative(OUTPUT_ROOT, output);
  if (
    relativeOutput === "" ||
    relativeOutput === ".." ||
    relativeOutput.startsWith(`..${sep}`) ||
    isAbsolute(relativeOutput)
  ) {
    throw new Error(`--output must be a dedicated subdirectory of ${OUTPUT_ROOT}`);
  }
  return relativeOutput;
}

function assertNoSymlinkedAncestors(output, relativeOutput) {
  if (!existsSync(OUTPUT_ROOT)) {
    mkdirSync(OUTPUT_ROOT, { recursive: true });
  }

  const rootStat = lstatSync(OUTPUT_ROOT);
  if (rootStat.isSymbolicLink()) {
    throw new Error("dist output root must not be a symbolic link");
  }
  if (!rootStat.isDirectory()) {
    throw new Error("dist output root exists and is not a directory");
  }

  let current = OUTPUT_ROOT;
  for (const component of relativeOutput.split(sep).filter(Boolean)) {
    current = resolve(current, component);
    if (!existsSync(current)) break;

    const stat = lstatSync(current);
    if (stat.isSymbolicLink()) {
      throw new Error(`--output path contains symbolic link: ${current}`);
    }
    if (current !== output && !stat.isDirectory()) {
      throw new Error(`--output ancestor is not a directory: ${current}`);
    }
  }
}

function assertDedicatedOutputPath(output) {
  const relativeOutput = assertLexicallyInsideOutputRoot(output);
  assertNoSymlinkedAncestors(output, relativeOutput);

  if (existsSync(output)) {
    const stat = lstatSync(output);
    if (stat.isSymbolicLink()) {
      throw new Error("--output must not be a symbolic link");
    }
    if (!stat.isDirectory()) {
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

const output = parseArguments();
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

for (const [filename, bytes] of [...files.entries()].sort(([a], [b]) =>
  a.localeCompare(b),
)) {
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
