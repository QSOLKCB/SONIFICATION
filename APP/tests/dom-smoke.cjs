"use strict";

const fs = require("node:fs");
const path = require("node:path");

class ElementStub {
  constructor(id) {
    this.id = id;
    this.value = "";
    this.textContent = "";
    this.hidden = false;
    this.disabled = false;
    this.checked = false;
    this.tabIndex = 0;
    this.dataset = {};
    this.style = {};
    this.listeners = Object.create(null);
  }

  addEventListener(type, listener) {
    this.listeners[type] = listener;
  }

  setAttribute(name, value) {
    this[name] = String(value);
  }

  querySelector(selector) {
    if (this.id === "config-form" && selector === 'input[name="voice"]:checked') {
      return { value: "hybrid" };
    }
    if (this.id === "render-button" && selector === "span") return this.label;
    return null;
  }

  querySelectorAll() {
    return [];
  }

  reset() {}
}

const appRoot = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(appRoot, "index.html"), "utf8");
const elements = Object.create(null);
for (const match of html.matchAll(/\bid="([^"]+)"/g)) {
  elements[match[1]] = new ElementStub(match[1]);
}

Object.assign(elements.seed, { value: "2026" });
Object.assign(elements.tempo, { value: "128" });
Object.assign(elements.bars, { value: "4" });
Object.assign(elements.tuning, { value: "432" });
Object.assign(elements["sample-rate"], { value: "44100" });
Object.assign(elements["bit-depth"], { value: "24" });
Object.assign(elements.peak, { value: "-3" });
elements["render-button"].label = new ElementStub("render-label");

globalThis.document = {
  body: new ElementStub("body"),
  createElement: function createElement(id) { return new ElementStub(id); },
  getElementById: function getElementById(id) {
    if (!elements[id]) throw new Error("app requested missing DOM id: " + id);
    return elements[id];
  }
};
globalThis.addEventListener = function addEventListener() {};
globalThis.requestAnimationFrame = function requestAnimationFrame(callback) { callback(0); return 1; };
globalThis.cancelAnimationFrame = function cancelAnimationFrame() {};

for (const script of [
  "namespace.js", "sha256.js", "math64.js", "audio.js", "provenance.js",
  "synthesis.js", "composition.js", "visualization.js", "app.js"
]) {
  require(path.join(appRoot, "js", script));
}

if (!elements.preflight.textContent.includes("330,750") && !elements.preflight.textContent.includes("330750")) {
  throw new Error("initial preflight did not calculate the default frame count");
}
if (!elements["config-form"].listeners.submit) throw new Error("render submit handler is missing");
if (!elements["play-button"].disabled) throw new Error("play should be disabled before a render");
if (elements["status-pill"].textContent !== "Ready") throw new Error("initial status is not Ready");

process.stdout.write("PASS direct-file DOM wiring smoke test\n");
