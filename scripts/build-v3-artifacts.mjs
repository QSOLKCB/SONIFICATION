// SPDX-License-Identifier: MPL-2.0
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  buildReceiptAndManifest,
} from "../src/etq-v3-artifacts.mjs";

function outputArgument() {
  const index = process.argv.indexOf("--output");
  if (index === -1) return resolve("dist/etq-303-v3.0.0");
  const value = process.argv[index + 1];
  if (!value) throw new Error("--output requires a path");
  return resolve(value);
}

const output = outputArgument();
rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });

const bundle = buildReceiptAndManifest();
const files = new Map([
  ["contract.json", bundle.contractBytes],
  ["contract.schema.json", bundle.contractSchemaBytes],
  ...bundle.receiverArtifacts.map((artifact) => [artifact.filename, artifact.bytes]),
  ["observation-receipt.json", bundle.receiptBytes],
  ["manifest.json", bundle.manifestBytes],
]);
for (const [filename, bytes] of [...files.entries()].sort(([left], [right]) => left.localeCompare(right))) {
  writeFileSync(resolve(output, filename), bytes);
}

console.log(
  JSON.stringify(
    {
      status: "PASS",
      output,
      fileCount: files.size,
      manifestCoreSha256: bundle.manifest.manifestCoreSha256,
      receiptCoreSha256: bundle.receipt.receiptCoreSha256,
      contractPayloadSha256: bundle.contract.determinism.contractPayloadSha256,
    },
    null,
    2,
  ),
);
