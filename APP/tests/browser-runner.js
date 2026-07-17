(function (root) {
  "use strict";
  const list = root.document.getElementById("results");
  const summary = root.document.getElementById("summary");
  root.QSOLIMC_TESTS(function report(outcome) {
    const item = root.document.createElement("li");
    if (!outcome.passed) item.className = "fail";
    const state = root.document.createElement("span");
    state.textContent = outcome.passed ? "PASS" : "FAIL";
    const detail = root.document.createElement("code");
    detail.textContent = outcome.passed ? outcome.name : outcome.name + "\n" + outcome.error;
    item.append(state, detail);
    list.appendChild(item);
  }).then(function finished(outcomes) {
    const failures = outcomes.filter(function failed(item) { return !item.passed; });
    summary.dataset.state = failures.length ? "fail" : "pass";
    summary.textContent = failures.length
      ? failures.length + " of " + outcomes.length + " checks failed."
      : outcomes.length + " of " + outcomes.length + " checks passed.";
  }).catch(function crashed(error) {
    summary.dataset.state = "fail";
    summary.textContent = "Test runner crashed: " + error.message;
  });
})(globalThis);
