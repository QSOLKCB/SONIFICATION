// SPDX-License-Identifier: MPL-2.0
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

import {
  CONTRACT_PATH,
  buildCanonicalContract,
  buildContractSchema,
  canonicalSerialize,
} from "../src/etq-v3-artifacts.mjs";

const contract = buildCanonicalContract();
const schema = buildContractSchema(contract);
const outputs = [
  [resolve(CONTRACT_PATH), contract],
  [resolve("spec/etq-303.v3.schema.json"), schema],
];
for (const [path, value] of outputs) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, canonicalSerialize(value), "utf8");
}
console.log(JSON.stringify({ status: "PASS", outputs: outputs.map(([path]) => path) }, null, 2));
