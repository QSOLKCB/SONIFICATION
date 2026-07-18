# ETQ-101 v2 Ternary MIDI Mapping

**Version:** 2.0.0
**Mapping ID:** `centered-101-state-ternary-register-v1`
**Status:** Symbolic codebook implemented; dynamics-to-event mapping and MIDI
file exporter not yet implemented

## 1. Separation rule

The implemented v2 mapping path is

$$
\text{canonical basis identity}
\longrightarrow
\text{symbolic MIDI note-number code}.
$$

A future dynamic profile may add

$$
\text{model state}
\longrightarrow
\text{declared observable}
\longrightarrow
\text{scheduled MIDI events}
\longrightarrow
\text{external receiver}.
$$

That additional path is not yet specified or implemented. In either case, the
external receiver determines acoustic tuning, timbre, loudness, and rendered
sound. Those properties are not part of the canonical root contract.

Root ETQ workflows never construct PCM, render audio, or claim a canonical
sound. They may emit only `.mid`, `.csv`, and `.json` runtime artifacts.

## 2. Display task

The first v2 mapping has one deliberately narrow task: provide a reversible
symbolic note code for every state in the declared decomposition

$$
\mathcal H_{101}
=\mathbb C^2\oplus(\mathbb C^{33}\otimes\mathbb C^3).
$$

It is a **basis codebook**, not yet a dynamic auditory display. It does not map
state populations, time steps, graph spectra, or curvature magnitude to
velocity, onset, duration, or pitch. Those choices require separately named
profiles and perceptual evaluation.

## 3. Explicit parameter map

The mapping follows a parameter-mapping discipline: identify the data class,
target symbol, transfer function, polarity, quantization, and claim boundary.

| ETQ feature | MIDI field | Transfer | Status |
|---|---|---|---|
| Fixed-singlet index | Note number | Two codebook bookends | Authored identity code |
| Qutrit label \(q\in\{0,1,2\}\) | Register lane | `0→low`, `1→mid`, `2→high` | Authored linear display of a cyclic label |
| Orbit index \(m\in\{0,\ldots,32\}\) | Offset inside lane | One integer note-number step per canonical orbit index | Authored enumeration code |
| Receiver tuning | Acoustic pitch | Not defined | External and non-normative |
| Dynamics step | Onset/duration | Not defined | Future profile |
| Population or projector weight | Velocity | Not defined | Future profile |
| Timbre/program/channel | Receiver realization | Not defined | Future profile |

There is no clipping or rounding: the finite source set is mapped exactly to
integer note numbers.

## 4. Canonical basis indexing

The selected basis order is

$$
j=0,1
$$

for the two triality-fixed singlets, followed by

$$
j=2+3m+q,
\qquad
m=0,\ldots,32,
\quad
q=0,1,2.
$$

The orbit order is the same numeric lexicographic order used by the canonical
root selector. It is deterministic but not a physical magnitude.

## 5. Exact note codebook

MIDI note numbers occupy the integer domain \(0,\ldots,127\). A contiguous
101-note window can start at either 13 or 14 with margins differing by one.
The canonical lower-start tie break chooses notes 13–113.

The fixed singlets are

$$
M(s_0)=13,
\qquad
M(s_1)=113.
$$

For each qutrit-orbit state,

$$
\boxed{
M(m,q)=14+33q+m.
}
$$

| \(q\) | Centered value \(q-1\) | SCL value \(d_q\) | Display lane | MIDI range |
|---:|---:|---:|---|---:|
| 0 | -1 | +1 | low | 14–46 |
| 1 | 0 | -2 | mid | 47–79 |
| 2 | +1 | +1 | high | 80–112 |

The SCL values are recorded to keep the two ternary operators distinct.
`diag(-1,0,1)` supplies an ordered coordinate; `diag(1,-2,1)` supplies
curvature. The latter is not misrepresented as an ordered low/mid/high scale.

## 6. Exact inverse and triality action

For notes 14–112, set

$$
r=M-14,
\qquad
q=\left\lfloor\frac r{33}\right\rfloor,
\qquad
m=r\bmod33,
$$

then recover

$$
j=2+3m+q.
$$

Notes 13 and 113 recover fixed singlets 0 and 1. All other MIDI notes lie
outside this codebook.

Within the 99-note qutrit interior, triality \(q\mapsto q+1\pmod3\) becomes

$$
(M-14)\mapsto(M-14+33)\bmod99.
$$

This covariance is exact. Calling the three results low, mid, and high is
still an authored observation convention because a cyclic qutrit label set has
no intrinsic first-to-last energy order.

## 7. What MIDI means here

A MIDI note number is a symbolic key in the ETQ contract. It is not a hertz
value. A receiving synthesizer may apply equal temperament, another tuning,
pitch bend, a tuning table, transposition, or instrument-specific behavior.

Consequently, v2 defines no:

- A4 reference;
- acoustic frequency;
- pitch-bend range;
- MIDI Tuning Standard table;
- soundfont or instrument program;
- loudness calibration; or
- rendered-audio hash.

A listening experiment must freeze and report those receiver settings as a
**noncanonical observation setup**. They never become E8-derived constants.

## 8. Perceptual boundary

The codebook is mathematically reversible, but reversibility does not establish
perceptual effectiveness. In particular:

- adjacent lane boundaries may fuse into fewer perceived streams;
- listener interpretation of ascending polarity cannot be assumed;
- timbre and loudness vary across receivers;
- velocity is not a calibrated loudness scale;
- playback rate and simultaneous note density affect masking and cognition;
- the designer's familiarity can make distinctions seem more obvious than
  they are to a naive listener.

These issues follow established parameter-mapping sonification practice. A
future perceptual profile should first pilot the display, then freeze its
mapping and test it with listeners rather than continually tuning it against
the evaluation set.

## 9. Recommended listener evaluation

A confirmatory study should preregister at least:

1. isolated low/mid/high identification;
2. balanced accuracy and a three-class confusion matrix;
3. reaction time;
4. short ternary-sequence reconstruction or edit distance;
5. held-out motif or same/different detection;
6. delayed recall, confidence, and workload; and
7. musician status only as a prespecified subgroup.

Useful counterbalanced ablations include ascending versus inverted polarity,
register spacing, reference phrase present versus absent, tempo, sequential
versus simultaneous presentation, and receiver/instrument choice.

The study would establish task performance for a specific playback setup. It
would not validate E8, qutrit ontology, or a physical theory.

## 10. Dynamics-to-event extension requirements

A later dynamic mapping must define, hash, and test:

- the observed state or projector quantity;
- dimensionless model-step traversal;
- onset tick, duration, and note-off convention;
- velocity transfer function and clipping;
- channel allocation and overlapping-note policy;
- tempo and pulses per quarter note;
- program changes or the decision to omit them;
- deterministic event ordering at equal ticks;
- CSV and JSON field schemas;
- Standard MIDI format and byte serialization; and
- event-table, MIDI, and manifest SHA-256 receipts.

The ternary phase in \(|\Omega_{3,\theta}\rangle\) affects only complex
amplitudes initially. A dynamic sonification may claim an audible phase effect
only after a noncommuting evolution produces a tested change in the mapped
observable. The static codebook makes no such claim.

## 11. Required provenance

Every codebook or future MIDI artifact must identify:

```json
{
  "model": "ETQ-101@2.0.0",
  "profile": "compact-101-ternary-midi",
  "mapping_id": "centered-101-state-ternary-register-v1",
  "basis_sha256": "97cfd1f087745422fd66d3640c7b86c3209593c4b53741018c08a5e9cdb15f6f",
  "adjacency_sha256": "29ae0af5b1090c9de30f1efc25789060fb1791eb175d2afcd6888847f7fe6324",
  "midi_codebook_sha256": "9a3196255e92bbc6857576e410a852dc66cd0354f27185fb2bede5b99f76e304",
  "absolute_frequency_hz": null,
  "receiver_tuning": "external-and-nonnormative",
  "rendered_audio_status": "permanently-disabled"
}
```

The canonical codebook hash covers the 101 entries in basis-index order using
compact `JSON.stringify` UTF-8 bytes with no BOM or trailing newline.

## 12. Claim boundary

Supported:

- the codebook is an exact bijection of the declared 101 basis states;
- the three qutrit labels occupy explicitly declared register lanes;
- triality acts as the stated modular note-offset transformation;
- the mapping and its inverse are deterministic and hashable; and
- receiver assumptions are excluded from ETQ structural identity.

Not supported:

- low/mid/high is an intrinsic qutrit energy order;
- the singlet notes are spectral extrema;
- MIDI note number is an E8-predicted frequency;
- a pleasant realization validates the mapping; or
- listener success validates a physical ETQ theory.

## 13. Method references

- Florian Grond and Jonathan Berger, “Parameter Mapping Sonification,” in
  Thomas Hermann, Andy Hunt, and John G. Neuhoff (eds.), *The Sonification
  Handbook*, Chapter 15, pp. 363–397, Logos, 2011.
- Elvira Pirondini et al., “A Spectral Method for Generating Surrogate Graph
  Signals,” *IEEE Signal Processing Letters* 23 (2016), 1275–1278,
  DOI: `10.1109/LSP.2016.2594072`.
