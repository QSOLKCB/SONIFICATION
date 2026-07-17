# ETQ-101 Sonification Mapping

**Version:** 1.0.0  
**Status:** Normative mapping specification; reference PCM renderer not yet implemented

## 1. Separation rule

The mathematical dynamics and the audio renderer are separate layers:

$$
\text{model state}
\longrightarrow
\text{declared observables}
\longrightarrow
\text{audio parameters}
\longrightarrow
\text{WAV samples}.
$$

Audio does not feed back into the mathematical state unless a later model version explicitly defines that coupling. A sonification is an observation of a declared model run; it is not evidence that the model is physically realized.

The canonical `generator-spectrum-v1` profile is a **static spectral
fingerprint of the continuous generator \(K\)**. It does not sonify a Floquet
trajectory or the eigenphases of \(U_F\). Those would require a separately
named time-series or Floquet-render profile.

## 2. Required inputs

A conforming render records:

- the ETQ model version and profile;
- the canonical 101 root-label hash;
- the canonical adjacency hash;
- all generator coefficients;
- the initial density operator or a reproducible state recipe;
- the phase \(\theta\), golden ratio parameter \(\varphi\), and reference frequency \(f_0\);
- the generator coefficients and the fact that this profile uses the static spectrum of \(K\);
- numerical tolerances and eigensolver identity when spectral rendering is used;
- sample rate, duration, channel count, window, limiter, and quantizer; and
- a hash of the final PCM byte sequence.

## 3. Spectral coordinates

Let the dimensionless Hermitian generator have the spectral resolution

$$
K=\sum_\ell\lambda_\ell P_\ell,
$$

where \(P_\ell\) projects onto the full eigenspace of \(\lambda_\ell\). For an initial state \(\rho_0\), define

$$
\mu_\ell=\mathrm{Tr}(\rho_0P_\ell).
$$

Then

$$
\mu_\ell\ge0,
\qquad
\sum_\ell\mu_\ell=1.
$$

Projector weights are normative because they do not depend on an arbitrary choice of eigenvectors inside a degenerate eigenspace.

Let

$$
\lambda_{\min}=\min\sigma(K),
\qquad
\lambda_{\max}=\max\sigma(K),
$$

over the complete 101-dimensional spectrum, including eigenspaces whose
projector weight is at or below the activity threshold. This keeps a mode's
pitch independent of which initial state is observed. Normalize by

$$
\xi_\ell=
2\frac{\lambda_\ell-\lambda_{\min}}
{\lambda_{\max}-\lambda_{\min}}-1.
$$

Thus \(\xi_\ell\in[-1,1]\). If \(\lambda_{\max}=\lambda_{\min}\), set every \(\xi_\ell=0\).

## 4. Golden-band pitch map

The canonical pitch map is

$$
\boxed{
f_\ell
=f_0\,2^{\varphi\xi_\ell},
\qquad
f_0=432\ \mathrm{Hz},
\qquad
\varphi=\frac{1+\sqrt5}{2}.
}
$$

For \(\xi_\ell\in[-1,1]\), the frequencies lie approximately between 141 Hz and 1.33 kHz. This range is an authored musical mapping. It is not an E8-predicted energy spectrum and does not make 432 Hz physically privileged.

Alternative pitch maps are allowed only when assigned a different mapping identifier and fully recorded. A render using another map is not byte-equivalent to the canonical mapping.

## 5. Amplitude map

Use

$$
a_\ell=\sqrt{\mu_\ell}.
$$

For a finite active set \(\mathcal A=\{\ell:\mu_\ell>\varepsilon_\mu\}\), define the safe normalization

$$
C_A=\max\left(1,\sum_{\ell\in\mathcal A}a_\ell\right).
$$

This gives the unwindowed mono signal

$$
x(t)=\frac1{C_A}
\sum_{\ell\in\mathcal A}
a_\ell\cos(2\pi f_\ell t).
$$

Negative entries of `[1, -2, 1]` are never interpreted as negative loudness. Audible amplitude remains nonnegative.

## 6. SCL contribution in the canonical profile

The canonical generator commutes with triality, so each spectral projector
\(P_\ell\) commutes with \(U_\tau\). With
\(D_a=U_\tau^aDU_\tau^{-a}\) and \(D_0+D_1+D_2=0\),

$$
\mathrm{Tr}(P_\ell D)
=\frac13\sum_{a=0}^2\mathrm{Tr}(P_\ell D_a)
=0.
$$

Consequently, a projector-trace SCL phase would be identically zero and is
**not** used.

Instead, SCL curvature and \(\theta=\pi/2\) enter the phase-prepared initial
state

$$
|\Omega_{\varphi,\theta}\rangle
=\frac1{\sqrt{101}}\sum_{j=0}^{100}
e^{2\pi i j/\varphi-i\theta d_j}|j\rangle,
$$

so they influence the projector weights

$$
\mu_\ell
=\langle\Omega_{\varphi,\theta}|P_\ell|
\Omega_{\varphi,\theta}\rangle.
$$

All canonical oscillator phases are zero after this state-to-weight reduction.
A later time-dependent profile may use
\(\kappa(t)=\mathrm{Tr}(\rho(t)D)\) only after declaring a normalization,
modulation depth, and a distinct mapping identifier.

## 7. Stereo mapping

Let the triality-sector projectors be

$$
P_r=\frac13\sum_{a=0}^2\zeta^{-ra}U_\tau^a,
\qquad r=0,1,2.
$$

Define the sector weights for mode \(\ell\):

$$
t_{\ell,r}=
\frac{\mathrm{Tr}(P_\ell P_r)}
{\mathrm{Tr}(P_\ell)}.
$$

The canonical pan coordinate is

$$
p_\ell=\mathrm{clip}
\left(t_{\ell,2}-t_{\ell,0},-1,1\right).
$$

Use equal-power stereo gains

$$
g_{L,\ell}=\cos\left(\frac\pi4(p_\ell+1)\right),
\qquad
g_{R,\ell}=\sin\left(\frac\pi4(p_\ell+1)\right).
$$

The \(r=1\) sector is centered. The mapping is deterministic but is still a sonification convention.

## 8. Window and sampling

For duration \(T\), the canonical edge window uses a raised cosine over \(T_f\) seconds at each edge:

$$
w(t)=
\begin{cases}
\tfrac12\left[1-\cos(\pi t/T_f)\right],&0\le t<T_f,\\
1,&T_f\le t\le T-T_f,\\
\tfrac12\left[1-\cos(\pi(T-t)/T_f)\right],&T-T_f<t\le T.
\end{cases}
$$

The canonical example uses:

| Parameter | Value |
|---|---:|
| Renderer profile | `generator-spectrum-v1` |
| Duration | 20 s |
| Sample rate | 48,000 Hz |
| Channels | 2 |
| Edge fade | 20 ms |
| PCM format | signed 16-bit little-endian |
| Peak ceiling | 0.98 |
| Dither | none |

For sample index \(n\), evaluate at

$$
t_n=\frac{n}{f_s},
\qquad n=0,\ldots,N-1,
\qquad N=Tf_s=960000.
$$

For channel \(c\in\{L,R\}\), the canonical pre-normalization sample is

$$
x_c[n]
=\frac{w(t_n)}{C_A}
\sum_{\ell\in\mathcal A}
a_\ell g_{c,\ell}\cos(2\pi f_\ell t_n).
$$

All oscillator phases are zero in this mapping profile. These two equations,
together with the definitions of \(a_\ell\), \(g_{c,\ell}\), \(w\), and
\(f_\ell\), fully specify the floating-point stereo signal before peak
normalization.

Do not use the wall clock, browser animation frames, or an unseeded random generator.

## 9. Quantization

Flatten both output channels to compute the global pre-normalization peak
\(M=\max_{c,n}|x_c[n]|\). If \(M=0\), emit zero-valued PCM. Otherwise set
\(y_c[n]=0.98x_c[n]/M\), then quantize with round-to-nearest, ties away from
zero:

$$
q_c[n]=\mathrm{clip}
\left(
\mathrm{sgn}(y_c[n])
\left\lfloor32767|y_c[n]|+\frac12\right\rfloor,
-32768,
32767
\right).
$$

The canonical profile uses no dither. Trigonometric evaluation,
eigendecomposition, and floating-point reduction can vary across runtimes, so a
PCM hash is a replay guarantee only when the manifest also records the numeric
runtime and eigensolver. Cross-runtime byte identity is not claimed merely from
the model version.

## 10. Degeneracy and ordering

Numerical eigensolvers may rotate eigenvectors inside a degenerate eigenspace.
Let the solver output, after ascending sort, be
\(\widehat\lambda_0,\ldots,\widehat\lambda_{100}\). Adjacent values are linked
when

$$
|\widehat\lambda_{i+1}-\widehat\lambda_i|
\le
\varepsilon_{\mathrm{abs}}
+\varepsilon_{\mathrm{rel}}
\max(|\widehat\lambda_i|,|\widehat\lambda_{i+1}|).
$$

The eigenspaces are the maximal contiguous connected groups under this rule,
identified as sorted-adjacent-connected-v1. For each group, use the arithmetic
mean of its raw eigenvalues as \(\lambda_\ell\) and the sum of its numerical
eigenvector outer products as \(P_\ell\). A conforming renderer therefore:

1. sorts eigenvalues in ascending order;
2. groups values within a declared absolute and relative tolerance;
3. constructs or accumulates the projector for each group;
4. derives weights from the projector, not a single arbitrary eigenvector; and
5. orders groups by ascending arithmetic-mean eigenvalue.

The canonical grouping tolerances are absolute \(10^{-10}\) and relative
\(10^{-10}\). The eigensolver name, version, numeric precision, and runtime
belong in the completed render manifest.

## 11. Canonical render manifest

A render manifest should contain at least:

```json
{
  "model": "ETQ-101@1.0.0",
  "profile": "compact-101",
  "mapping_id": "generator-spectrum-v1",
  "render_status": "specified-not-implemented",
  "basis_sha256": "97cfd1f087745422fd66d3640c7b86c3209593c4b53741018c08a5e9cdb15f6f",
  "adjacency_sha256": "29ae0af5b1090c9de30f1efc25789060fb1791eb175d2afcd6888847f7fe6324",
  "theta_rad": 1.5707963267948966,
  "golden_ratio": 1.618033988749895,
  "reference_hz": 432,
  "pitch_map": "golden-band-v1",
  "amplitude_map": "spectral-projector-sqrt-v1",
  "initial_state_recipe": "ouroboros-golden-scl-v1",
  "oscillator_phase_map": "zero-v1",
  "stereo_map": "triality-equal-power-v1",
  "epsilon_mu": 1e-12,
  "eigenvalue_absolute_tolerance": 1e-10,
  "eigenvalue_relative_tolerance": 1e-10,
  "eigenvalue_grouping_id": "sorted-adjacent-connected-v1",
  "group_eigenvalue_id": "arithmetic-mean-v1",
  "sample_rate_hz": 48000,
  "duration_seconds": 20,
  "channels": 2,
  "edge_fade_seconds": 0.02,
  "peak_ceiling": 0.98,
  "silence_policy": "emit-zero-pcm",
  "pcm": "s16le",
  "quantizer": "nearest-ties-away-from-zero-v1",
  "dither": "none",
  "numeric_runtime_id": null,
  "eigensolver_id": null,
  "render_manifest_payload_sha256": null,
  "pcm_sha256": null
}
```

The `null` hash and `specified-not-implemented` status are deliberate: this
repository version specifies the renderer contract but does not claim to ship a
completed spectral eigensolver or WAV artifact. A conforming implementation
replaces those placeholders and records its provenance.

## 12. Interpretation boundary

The renderer supports these statements:

- the sound is a deterministic mapping of declared ETQ observables;
- the E8 root labels and graph are reproducible from exact coordinates;
- qutrit/triality and SCL quantities influence declared audio parameters; and
- two artifacts rendered with the same fully recorded numeric environment can be checked by hash.

It does not support these statements:

- the sound is the literal sound of E8, a qutrit, or a quantum system;
- 432 Hz is selected by E8 mathematics;
- a pleasing or stable sound validates the mathematical model; or
- a sonification alone establishes a physical theory.
