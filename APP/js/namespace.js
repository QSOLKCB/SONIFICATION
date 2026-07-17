/* QSOL-IMC Offline App shared namespace.
 *
 * This is a classic script on purpose: the complete app can be opened from a
 * local file without a web server, module loader, package manager, or network.
 */
(function initialiseQSOLIMC(root) {
  "use strict";

  if (!root || (typeof root !== "object" && typeof root !== "function")) {
    throw new Error("QSOL-IMC requires a global object");
  }

  const current = root.QSOLIMC;
  if (current !== undefined && (current === null || typeof current !== "object")) {
    throw new Error("globalThis.QSOLIMC is already occupied by a non-object value");
  }

  const Q = current || {};
  root.QSOLIMC = Q;

  function installConstant(name, value) {
    if (Object.prototype.hasOwnProperty.call(Q, name)) {
      if (Q[name] !== value) {
        throw new Error("incompatible QSOL-IMC script versions were loaded");
      }
      return;
    }
    Object.defineProperty(Q, name, {
      configurable: false,
      enumerable: true,
      writable: false,
      value: value,
    });
  }

  installConstant("APP_NAME", "QSOL-IMC Offline App");
  installConstant("VERSION", "1.0.0");
  installConstant("ABI", "qsol-imc.browser-float64/v1");
  installConstant(
    "DETERMINISM_SCOPE",
    "same-app-version-same-browser-runtime-bit-identical; cross-runtime-float64-not-guaranteed"
  );
  installConstant(
    "ABI_NOTE",
    "The browser ABI fixes algorithm order, seeded integer sources, PCM quantization, and file packing. Transcendental DSP uses the host JavaScript runtime, so exact PCM identity is promised only for replay with the same app version and browser runtime."
  );

  if (!Object.prototype.hasOwnProperty.call(Q, "util")) {
    Q.util = Object.create(null);
  }

  Q.util.assertFiniteNumber = function assertFiniteNumber(value, name) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new TypeError((name || "value") + " must be a finite number");
    }
    return value;
  };

  Q.util.assertInteger = function assertInteger(value, name, minimum, maximum) {
    if (!Number.isInteger(value)) {
      throw new TypeError((name || "value") + " must be an integer");
    }
    if (minimum !== undefined && value < minimum) {
      throw new RangeError((name || "value") + " is below its minimum");
    }
    if (maximum !== undefined && value > maximum) {
      throw new RangeError((name || "value") + " exceeds its maximum");
    }
    return value;
  };
})(globalThis);
