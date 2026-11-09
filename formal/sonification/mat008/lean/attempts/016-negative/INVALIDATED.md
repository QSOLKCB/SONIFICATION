This original negative-control aggregate reported PASS after the checker input
closure was expanded, but its copy fixture omitted two newly required files.
Three mutations were rejected by missing inputs instead of their intended gates.
The original logs and aggregate are retained unchanged; their detection claims
are INVALID and must not support proof-audit coverage. Attempt 017 reruns with
complete fixtures and requires the exact intended error class for each mutation.
