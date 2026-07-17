(function (root) {
  "use strict";

  const Q = root.QSOLIMC = root.QSOLIMC || {};

  function canvasContext(canvas) {
    if (!canvas || typeof canvas.getContext !== "function") {
      throw new TypeError("a canvas element is required");
    }
    const context = canvas.getContext("2d");
    if (!context) throw new Error("2D canvas rendering is unavailable");
    return context;
  }

  function clear(context, canvas) {
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "#0b0d0e";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.strokeStyle = "rgba(197,255,103,.08)";
    context.lineWidth = 1;
    for (let x = 0; x <= canvas.width; x += 80) {
      context.beginPath();
      context.moveTo(x + 0.5, 0);
      context.lineTo(x + 0.5, canvas.height);
      context.stroke();
    }
    for (let y = 0; y <= canvas.height; y += 60) {
      context.beginPath();
      context.moveTo(0, y + 0.5);
      context.lineTo(canvas.width, y + 0.5);
      context.stroke();
    }
  }

  function drawChannel(context, samples, width, center, height, color) {
    const framesPerPixel = samples.length / width;
    context.strokeStyle = color;
    context.lineWidth = 1;
    context.beginPath();
    for (let x = 0; x < width; x += 1) {
      const start = Math.floor(x * framesPerPixel);
      const stop = Math.max(start + 1, Math.floor((x + 1) * framesPerPixel));
      let minimum = 1;
      let maximum = -1;
      for (let index = start; index < stop && index < samples.length; index += 1) {
        minimum = Math.min(minimum, samples[index]);
        maximum = Math.max(maximum, samples[index]);
      }
      const upper = center - maximum * height;
      const lower = center - minimum * height;
      context.moveTo(x + 0.5, upper);
      context.lineTo(x + 0.5, lower);
    }
    context.stroke();
  }

  function drawWaveform(canvas, left, right) {
    if (!(left instanceof Float64Array) || !(right instanceof Float64Array) || left.length !== right.length || left.length < 1) {
      throw new TypeError("waveform channels must be equal non-empty Float64Array values");
    }
    const context = canvasContext(canvas);
    clear(context, canvas);
    const quarter = canvas.height / 4;
    context.strokeStyle = "rgba(238,233,220,.18)";
    for (const y of [quarter, quarter * 3]) {
      context.beginPath();
      context.moveTo(0, y + 0.5);
      context.lineTo(canvas.width, y + 0.5);
      context.stroke();
    }
    drawChannel(context, left, canvas.width, quarter, quarter * 0.8, "rgba(197,255,103,.92)");
    drawChannel(context, right, canvas.width, quarter * 3, quarter * 0.8, "rgba(198,168,106,.82)");
    context.fillStyle = "rgba(238,233,220,.48)";
    context.font = "12px ui-monospace, monospace";
    context.fillText("L", 14, 22);
    context.fillText("R", 14, canvas.height / 2 + 22);
  }

  function nextPowerOfTwo(value) {
    let result = 1;
    while (result * 2 <= value && result < 4096) result *= 2;
    return result;
  }

  function fftMagnitudes(left, right) {
    const size = nextPowerOfTwo(Math.min(left.length, right.length, 4096));
    const real = new Float64Array(size);
    const imaginary = new Float64Array(size);
    for (let index = 0; index < size; index += 1) {
      const window = size > 1 ? 0.5 - 0.5 * Math.cos(2 * Math.PI * index / (size - 1)) : 1;
      real[index] = 0.5 * (left[index] + right[index]) * window;
    }

    let reverse = 0;
    for (let index = 1; index < size; index += 1) {
      let bit = size >> 1;
      while (reverse & bit) {
        reverse ^= bit;
        bit >>= 1;
      }
      reverse ^= bit;
      if (index < reverse) {
        const temporary = real[index];
        real[index] = real[reverse];
        real[reverse] = temporary;
      }
    }

    for (let length = 2; length <= size; length *= 2) {
      const angle = -2 * Math.PI / length;
      const stepReal = Math.cos(angle);
      const stepImaginary = Math.sin(angle);
      for (let offset = 0; offset < size; offset += length) {
        let twiddleReal = 1;
        let twiddleImaginary = 0;
        for (let inner = 0; inner < length / 2; inner += 1) {
          const even = offset + inner;
          const odd = even + length / 2;
          const oddReal = real[odd] * twiddleReal - imaginary[odd] * twiddleImaginary;
          const oddImaginary = real[odd] * twiddleImaginary + imaginary[odd] * twiddleReal;
          real[odd] = real[even] - oddReal;
          imaginary[odd] = imaginary[even] - oddImaginary;
          real[even] += oddReal;
          imaginary[even] += oddImaginary;
          const nextReal = twiddleReal * stepReal - twiddleImaginary * stepImaginary;
          twiddleImaginary = twiddleReal * stepImaginary + twiddleImaginary * stepReal;
          twiddleReal = nextReal;
        }
      }
    }

    const magnitudes = new Float64Array(size / 2);
    for (let index = 0; index < magnitudes.length; index += 1) {
      magnitudes[index] = Math.hypot(real[index], imaginary[index]) / size;
    }
    return magnitudes;
  }

  function drawSpectrum(canvas, left, right, sampleRate) {
    const context = canvasContext(canvas);
    clear(context, canvas);
    const magnitudes = fftMagnitudes(left, right);
    const nyquist = sampleRate / 2;
    const minimumFrequency = 20;
    const maximumFrequency = Math.max(minimumFrequency * 2, nyquist);
    const logSpan = Math.log(maximumFrequency / minimumFrequency);
    context.strokeStyle = "rgba(197,255,103,.95)";
    context.fillStyle = "rgba(197,255,103,.12)";
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(0, canvas.height);
    for (let x = 0; x < canvas.width; x += 1) {
      const frequency = minimumFrequency * Math.exp(logSpan * x / Math.max(1, canvas.width - 1));
      const bin = Math.min(magnitudes.length - 1, Math.round(frequency / nyquist * magnitudes.length));
      const db = 20 * Math.log10(Math.max(1e-7, magnitudes[bin]));
      const normalized = Math.max(0, Math.min(1, (db + 100) / 100));
      const y = canvas.height - normalized * (canvas.height - 24);
      context.lineTo(x, y);
    }
    context.lineTo(canvas.width, canvas.height);
    context.closePath();
    context.fill();
    context.stroke();
    context.fillStyle = "rgba(238,233,220,.48)";
    context.font = "12px ui-monospace, monospace";
    context.fillText("20 Hz", 12, canvas.height - 10);
    const label = Math.round(nyquist / 1000) + " kHz";
    context.fillText(label, canvas.width - context.measureText(label).width - 12, canvas.height - 10);
  }

  Q.Visualization = Object.freeze({ drawWaveform, drawSpectrum, fftMagnitudes });
})(globalThis);
