// SPDX-License-Identifier: MPL-2.0
import { randomBytes } from "node:crypto";
import {
  closeSync,
  constants,
  existsSync,
  lstatSync,
  mkdirSync,
  openSync,
  readdirSync,
  renameSync,
  rmSync,
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

// The proc-fd path is bound to an open directory inode, not a pathname that
// can be replaced by a symlink between checking and writing. No new runtime
// dependencies and no generated PCM: root artifacts remain symbolic only.
function directoryPath(fd, name) {
  return "/proc/self/fd/" + fd + "/" + name;
}

function assertEmptyDirectoryOrMissing(path) {
  const entry = lstatSync(path, { throwIfNoEntry: false });
  if (entry) {
    if (entry.isSymbolicLink() || !entry.isDirectory()) {
      throw new Error("--output is not a real directory");
    }
    if (readdirSync(path).length !== 0) {
      throw new Error("--output already exists and is not empty");
    }
  }
}

/** Publish through directory handles; never open outputs through a mutable name. */
export function publishAnchored(output, files) {
  if (process.platform !== "linux" || !existsSync("/proc/self/fd")) {
    throw new Error("secure output publication requires Linux proc-fd support");
  }
  const relativeOutput = relative(OUTPUT_ROOT, output);
  if (
    relativeOutput === "" || relativeOutput === ".." ||
    relativeOutput.startsWith(".." + sep) || isAbsolute(relativeOutput)
  ) {
    throw new Error("--output must be a dedicated subdirectory of dist");
  }
  const components = relativeOutput.split(sep).filter(Boolean);
  const finalName = components.pop();

  // The initial pathname is trusted only to obtain the first descriptor.
  // Every subsequent component is opened through the preceding descriptor.
  mkdirSync(OUTPUT_ROOT, { recursive: true });
  const flags =
    constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW;
  const opened = [];
  let stagePath = null;
  try {
    let current = openSync(OUTPUT_ROOT, flags);
    opened.push(current);
    for (const component of components) {
      const child = directoryPath(current, component);
      try {
        mkdirSync(child);
      } catch (error) {
        if (error.code !== "EEXIST") throw error;
      }
      current = openSync(child, flags);
      opened.push(current);
    }
    const target = directoryPath(current, finalName);
    assertEmptyDirectoryOrMissing(target);

    // Private unpredictable sibling; after it is open, even a renamed stage
    // remains pinned by its file descriptor. Entries are exclusively created.
    const stageName = ".etq-v3-stage-" + randomBytes(16).toString("hex");
    stagePath = directoryPath(current, stageName);
    mkdirSync(stagePath, { mode: 0o700 });
    const stageFd = openSync(stagePath, flags);
    opened.push(stageFd);
    for (const [filename, bytes] of files) {
      assertAllowedFilename(filename);
      writeFileSync(directoryPath(stageFd, filename), bytes, { flag: "wx" });
    }

    // rename() does NOT follow a final-component symlink. A concurrently
    // substituted output symlink therefore fails instead of redirecting writes.
    assertEmptyDirectoryOrMissing(target);
    renameSync(stagePath, target);
    stagePath = null;
  } finally {
    // The stage pathname remains anchored to the original parent inode.
    if (stagePath !== null) {
      rmSync(stagePath, { recursive: true, force: true });
    }
    for (const fd of opened.reverse()) closeSync(fd);
  }
}

function main() {
  const output = outputArgument();
  assertDedicatedOutputPath(output);

  const bundle = buildReceiptAndManifest();
  const files = new Map([
    ["contract.json", bundle.contractBytes],
    ["contract.schema.json", bundle.contractSchemaBytes],
    ...bundle.receiverArtifacts.map((artifact) => [artifact.filename, artifact.bytes]),
    ["observation-receipt.json", bundle.receiptBytes],
    ["manifest.json", bundle.manifestBytes],
  ]);
  publishAnchored(
    output,
    [...files.entries()].sort(([left], [right]) => left.localeCompare(right))
  );

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
}

// Importing this module for the security regression does not publish files.
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
