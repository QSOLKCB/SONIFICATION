// SPDX-License-Identifier: MPL-2.0
// Evidence-only security regressions for SONIFICATION root ETQ and publication.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  chmodSync, copyFileSync, existsSync, lstatSync, mkdirSync, mkdtempSync,
  readFileSync, renameSync, rmSync, symlinkSync, writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  IMPLEMENTATION_SOURCE_PATHS,
  buildImplementationIdentity,
} from "../src/etq-v3-artifacts.mjs";
import {
  IMPLEMENTATION_SOURCE_PATHS_V2,
  buildImplementationIdentityV2,
} from "../src/d4-triality-algebra-v2-artifacts.mjs";

import { publishAnchored } from "../scripts/build-v3-artifacts.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const V3 = "scripts/build-v3-artifacts.mjs";

test("provenance ledgers cover the previously missing output-defining modules", () => {
  const a = buildImplementationIdentity();
  const b = buildImplementationIdentityV2();
  assert.ok(IMPLEMENTATION_SOURCE_PATHS.includes("src/etq-model.mjs"));
  assert.ok(IMPLEMENTATION_SOURCE_PATHS_V2.includes("src/d4-triality-reference.mjs"));
  assert.deepEqual(a.sourceFiles.map((x) => x.path), IMPLEMENTATION_SOURCE_PATHS);
  assert.deepEqual(b.sourceFiles.map((x) => x.path), IMPLEMENTATION_SOURCE_PATHS_V2);
  assert.equal(a.sourceFiles.length, new Set(a.sourceFiles.map((x) => x.path)).size);
  assert.equal(b.sourceFiles.length, new Set(b.sourceFiles.map((x) => x.path)).size);
});

test("v3 builder fails explicitly on prohibited audio and every unknown option", () => {
  for (const extra of ["--wav", "--render-audio", "--pcm=bad", "--unknown"]) {
    const result = spawnSync(process.execPath, [V3, extra], {
      cwd: ROOT, encoding: "utf8",
    });
    assert.notEqual(result.status, 0, "accepted forbidden option " + extra);
    assert.match(result.stderr, /rendered-audio request|unknown option/);
  }
  const duplicate = spawnSync(
    process.execPath, [V3, "--output", "first", "--output", "second"],
    { cwd: ROOT, encoding: "utf8" }
  );
  assert.notEqual(duplicate.status, 0);
  assert.match(duplicate.stderr, /only once/);
  const missing = spawnSync(process.execPath, [V3, "--output", "--wav"], {
    cwd: ROOT, encoding: "utf8",
  });
  assert.notEqual(missing.status, 0);
  assert.match(missing.stderr, /requires a path/);
});

test("v3 build refuses symlinked output ancestors without touching outside files", () => {
  const dist = resolve(ROOT, "dist");
  mkdirSync(dist, { recursive: true });
  const parent = mkdtempSync(resolve(dist, "security-v3-"));
  const outside = mkdtempSync(resolve(tmpdir(), "security-outside-"));
  try {
    const link = resolve(parent, "escape");
    symlinkSync(outside, link, "dir");
    const output = resolve(link, "new-bundle");
    const result = spawnSync(process.execPath, [V3, "--output", output], {
      cwd: ROOT, encoding: "utf8",
    });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /symbolic link/);
    assert.equal(existsSync(resolve(outside, "new-bundle")), false);
  } finally {
    rmSync(parent, { recursive: true, force: true });
    rmSync(outside, { recursive: true, force: true });
  }
});

test("paper publication never follows symlinked PDF or predictable checksum temp", () => {
  if (process.platform !== "linux") return;
  const root = mkdtempSync(resolve(tmpdir(), "heresy-paper-"));
  try {
    const scripts = resolve(root, "scripts");
    const paper = resolve(root, "docs/etq-303/v3.0.1");
    const bin = resolve(root, "bin");
    mkdirSync(scripts, { recursive: true });
    mkdirSync(paper, { recursive: true });
    mkdirSync(bin, { recursive: true });
    const original = resolve(ROOT, "scripts/build-etq303-paper.sh");
    const script = resolve(scripts, "build-etq303-paper.sh");
    copyFileSync(original, script);
    const prefix = "ETQ-303_formal_model_v3.0.1";
    writeFileSync(resolve(paper, prefix + ".tex"), "mock TeX source");
    writeFileSync(resolve(paper, "ETQ-303_references.bib"), "mock bibliography");
    const fake = resolve(bin, "latexmk");
    writeFileSync(fake, [
      "#!/bin/sh",
      "for arg in \"$@\"; do",
      "  case \"$arg\" in -outdir=*) out=\"$(printf '%s' \"$arg\" | sed 's/^-outdir=//')\" ;; esac",
      "done",
      "printf 'fixture PDF bytes' > \"$out/ETQ-303_formal_model_v3.0.1.pdf\"",
      ": > \"$out/ETQ-303_formal_model_v3.0.1.log\"",
      "",
    ].join("\n"));
    chmodSync(fake, 0o755);
    for (const name of ["pdflatex", "biber"]) {
      const binary = resolve(bin, name);
      writeFileSync(binary, "#!/bin/sh\nexit 0\n");
      chmodSync(binary, 0o755);
    }
    const env = { ...process.env, PATH: bin + ":" + process.env.PATH };
    const outside = resolve(root, "outside-sentinel");
    writeFileSync(outside, "do not overwrite");
    const pdf = resolve(paper, prefix + ".pdf");
    symlinkSync(outside, pdf);
    const refused = spawnSync("bash", [script], { env, encoding: "utf8" });
    assert.notEqual(refused.status, 0);
    assert.equal(readFileSync(outside, "utf8"), "do not overwrite");
    rmSync(pdf);
    // The original predictable temporary checksum name can be attacker-owned.
    symlinkSync(outside, resolve(paper, "UPLOAD_SHA256SUMS.txt.tmp"));
    const accepted = spawnSync("bash", [script], { env, encoding: "utf8" });
    assert.equal(accepted.status, 0, accepted.stderr);
    assert.equal(readFileSync(outside, "utf8"), "do not overwrite");
    assert.equal(readFileSync(pdf, "utf8"), "fixture PDF bytes");
    assert.ok(!lstatSync(pdf).isSymbolicLink());
    assert.match(
      readFileSync(resolve(paper, "UPLOAD_SHA256SUMS.txt"), "utf8"),
      /ETQ-303_formal_model_v3\.0\.1\.pdf/,
    );
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("a directory replaced with a symlink DURING bundle writing cannot redirect files", () => {
  if (process.platform !== "linux") return;
  const parent = mkdtempSync(resolve(ROOT, "dist", "race-"));
  const outside = mkdtempSync(resolve(tmpdir(), "etq-race-outside-"));
  const output = resolve(parent, "bundle");
  const moved = resolve(parent, "old-bundle");
  try {
    mkdirSync(output);
    function* switchedFiles() {
      // This mutation occurs after publishAnchored has opened its private
      // staging directory, before it attempts the first artifact write.
      renameSync(output, moved);
      symlinkSync(outside, output, "dir");
      yield ["contract.json", Buffer.from('{"fixture":true}', "utf8")];
    }
    assert.throws(
      () => publishAnchored(output, switchedFiles()),
      /ENOTDIR|EEXIST|not a real directory|not empty|EISDIR/,
    );
    assert.deepEqual(readdirSync(outside), []);
    assert.equal(existsSync(resolve(outside, "contract.json")), false);
    assert.equal(lstatSync(output).isSymbolicLink(), true);
  } finally {
    rmSync(parent, { recursive: true, force: true });
    rmSync(outside, { recursive: true, force: true });
  }
});

test("anchored publication permits an ordinary dedicated nested bundle", () => {
  if (process.platform !== "linux") return;
  const parent = mkdtempSync(resolve(ROOT, "dist", "pinned-"));
  try {
    const output = resolve(parent, "nested", "bundle");
    publishAnchored(output, [
      ["contract.json", Buffer.from('{"ok":true}', "utf8")],
      ["events.csv", Buffer.from("test\n", "utf8")],
    ]);
    assert.deepEqual(readdirSync(output).sort(), ["contract.json", "events.csv"]);
    assert.equal(readFileSync(resolve(output, "contract.json"), "utf8"), '{"ok":true}');
  } finally {
    rmSync(parent, { recursive: true, force: true });
  }
});
