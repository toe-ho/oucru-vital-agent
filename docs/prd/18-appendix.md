# 18. Appendix

[← Back to Index](00-index.md)

---

## A. Glossary

| Term / Acronym | Definition |
|---|---|
| **ECG** | Electrocardiogram. A recording of the electrical activity of the heart over time, captured via electrodes placed on the skin. Used to detect cardiac arrhythmias and other heart conditions. |
| **PPG** | Photoplethysmogram. An optically obtained plethysmogram that detects volumetric changes in blood in peripheral circulation. Commonly measured by pulse oximeters and smartwatches. |
| **SQI** | Signal Quality Index. A scalar metric (or set of metrics) that quantifies how clean, reliable, and clinically usable a segment of physiological signal is. |
| **EDC** | Electronic Data Capture. A computerized system used in clinical trials to collect clinical trial data electronically, replacing paper-based data entry. |
| **EHR** | Electronic Health Record. A digital version of a patient's paper chart, containing medical history, diagnoses, medications, treatment plans, and test results. |
| **DBMS** | Database Management System. Software for creating and managing databases (e.g., PostgreSQL). |
| **HRV** | Heart Rate Variability. The variation in time intervals between consecutive heartbeats (RR intervals). Higher HRV generally indicates better cardiovascular health. |
| **SDNN** | Standard Deviation of NN intervals. A time-domain HRV metric calculated as the standard deviation of all normal-to-normal RR intervals in a recording. |
| **RMSSD** | Root Mean Square of Successive Differences. A time-domain HRV metric reflecting short-term beat-to-beat variability. Calculated as the square root of the mean of squared differences between successive NN intervals. |
| **CVSD** | Coefficient of Variation of Successive Differences. RMSSD normalized by the mean NN interval; dimensionless measure of short-term HRV. |
| **CVNN** | Coefficient of Variation of NN intervals. SDNN normalized by the mean NN interval; dimensionless measure of overall HRV. |
| **DTW** | Dynamic Time Warping. An algorithm for measuring similarity between two time sequences that may vary in speed or phase. Used as an SQI metric by comparing a signal segment to a clean template. |
| **SNR** | Signal-to-Noise Ratio. A measure of signal strength relative to background noise. Higher SNR indicates a cleaner signal. Expressed in decibels (dB). |
| **LLM** | Large Language Model. A deep learning model trained on large text corpora capable of generating and understanding natural language. Examples: GPT-4o, Claude 3.5 Sonnet, Llama 3.1. |
| **LangGraph** | A Python framework for building stateful, multi-step AI agent workflows as directed graphs. Built on top of LangChain. Enables cycles, conditional branching, and persistent state in agent loops. |
| **LangChain** | A Python/TypeScript framework providing abstractions for building LLM-powered applications, including chains, memory, tools, and retrieval-augmented generation (RAG). |
| **Agent (AI)** | An autonomous software entity that uses an LLM to perceive inputs, reason about actions, invoke tools, and iteratively work toward a goal without step-by-step human instruction. |
| **Orchestration** | The coordination and sequencing of multiple agent steps, tool calls, and sub-processes to accomplish a complex task. LangGraph handles orchestration in this project. |
| **Pipeline** | An automated sequence of data processing steps executed in order: load → preprocess → segment → compute SQI → classify → report. |
| **Monorepo** | A single version-controlled repository containing multiple distinct projects or packages (e.g., frontend + backend + shared types), enabling unified versioning and cross-package refactoring. |
| **REST API** | Representational State Transfer Application Programming Interface. An architectural style for distributed hypermedia systems using HTTP methods (GET, POST, PUT, DELETE) with stateless requests. |
| **FastAPI** | A modern, high-performance Python web framework for building REST APIs with automatic OpenAPI documentation, built-in data validation via Pydantic, and async support. |
| **Docker** | A platform for packaging applications and their dependencies into portable, isolated containers that run consistently across different environments. |
| **Docker Compose** | A tool for defining and running multi-container Docker applications using a YAML configuration file (`docker-compose.yml`). Enables starting the full stack with a single `docker compose up` command. |
| **Waveform** | A graphical representation of a signal's amplitude over time. In this context, refers to ECG or PPG time-series data. |
| **Segment** | A fixed-duration time window extracted from a longer recording for individual quality assessment. Default segment length: 30 seconds. |
| **R-peak** | The sharp upward spike in an ECG waveform corresponding to ventricular depolarization. R-peak detection is the basis for computing RR intervals and HRV metrics. |
| **Bandpass filter** | A signal processing filter that passes frequencies within a specified range and attenuates frequencies outside it. Used to remove baseline wander (low frequency) and high-frequency noise from ECG/PPG signals. |
| **ReAct pattern** | Reasoning + Acting. An agent design pattern where the LLM alternates between reasoning steps (Thought) and action steps (Action/Observation) in a loop until a final answer is reached. |
| **Tool (agent)** | A callable function exposed to an LLM agent. The agent selects tools by name, provides typed arguments, and receives structured results. Examples: `compute_sqi_tool`, `classify_segments_tool`. |
| **OUCRU** | Oxford University Clinical Research Unit. A research unit affiliated with the University of Oxford, conducting clinical and epidemiological research in Southeast Asia, headquartered in Ho Chi Minh City, Vietnam. |
| **Token-Encoding** | A privacy layer that pseudonymizes patient identifiers and sensitive metadata before data is passed to external or local LLM services. Each real identifier is mapped to a generated token (e.g., a UUID); the mapping is stored in a dedicated database table to allow authorized re-identification. Encoding is applied at the boundary between the internal data store and any outbound LLM prompt. |
| **Pseudonymization** | A data de-identification technique in which directly identifying fields (e.g., patient names, file names containing IDs) are replaced with artificial identifiers (pseudonyms). Unlike anonymization, pseudonymization is reversible given access to the mapping table. Used in this project as part of the token-encoding privacy layer. |
| **Chatbot Interface** | Screen 6 of the web dashboard. Provides a conversational interface allowing users to ask natural-language questions about a specific recording's quality assessment results. Backed by the `POST /chat` API endpoint, which invokes the LangGraph agent with the recording's stored SQI results and agent logs as grounding context. |

---

## B. External Links

| Resource | URL |
|---|---|
| vital_sqi GitHub | https://github.com/Oucru-Innovations/vital_sqi |
| vital_sqi pip install | `pip install vitalSQI-toolkit` |
| vital-DSP GitHub | https://github.com/Oucru-Innovations/vital-DSP (Key dependency of vital_sqi — provides the DEFAULT PPG peak detector and DSP utilities; installed automatically via vitalSQI-toolkit) |
| OUCRU Innovations GitHub | https://github.com/Oucru-Innovations |
| LangGraph Documentation | https://langchain-ai.github.io/langgraph/ |
| FastAPI Documentation | https://fastapi.tiangolo.com/ |
| PhysioNet (public ECG/PPG datasets) | https://physionet.org/ |

---

## C. vital_sqi Package Structure

The complete module tree of the `vital_sqi` library, which serves as the core signal processing engine for this project.

```
vital_sqi/
├── app/
│   └── ...                   → Application-level utilities and helpers
│
├── data/
│   ├── signal_io.py          → Reads/writes ECG (EDF, MIT/WFDB, CSV) & PPG (CSV) files
│   └── signal_sqi_class.py   → Core SignalSQI object (holds signal + SQI results + rules)
│
├── dataset/
│   └── ...                   → Sample datasets and dataset loading utilities
│
├── preprocess/
│   ├── preprocess_signal.py  → Trimming, tapering, smoothing, bandpass filtering
│   ├── removal_utilities.py  → Noise/artifact removal
│   └── segment_split.py      → Splits signal into fixed-duration or beat-based windows
│
├── sqi/
│   ├── standard_sqi.py       → Statistical SQIs (kurtosis, skewness, entropy, SNR, zero-crossing)
│   ├── hrv_sqi.py            → HRV metrics (SDNN, RMSSD, CVSD, CVNN, Poincaré)
│   ├── rpeaks_sqi.py         → R-peak / RR interval quality metrics
│   ├── waveform_sqi.py       → Waveform shape metrics (QRS energy, band energy)
│   └── dtw_sqi.py            → Dynamic Time Warping quality metric
│
├── rule/
│   ├── rule_class.py         → Single Rule: operator + threshold + label
│   └── ruleset_class.py      → RuleSet: collection of rules; all-or-nothing evaluation
│
├── common/
│   ├── band_filter.py        → Bandpass filtering
│   ├── rpeak_detection.py    → R-peak/peak detection (14 algorithms: 7 PPG + 7 ECG)
│   ├── power_spectrum.py     → Frequency domain analysis
│   ├── generate_template.py  → Template generation for DTW
│   └── utils.py              → Shared utilities
│
├── pipeline/
│   ├── pipeline_functions.py → Low-level: extract_sqi, classify_segments, get_reject_segments
│   └── pipeline_highlevel.py → HIGH-LEVEL ENTRY POINTS
│
└── resource/
    ├── sqi_dict.json          → 47+ SQI definitions with parameters
    └── rule_dict.json         → 51 rule definitions (accept/reject thresholds)
```

### Key Entry Points

| Function | Module | Description |
|---|---|---|
| `get_ecg_sqis()` | `pipeline_highlevel.py` | Full ECG pipeline: load → preprocess → segment → SQI → classify |
| `get_ppg_sqis()` | `pipeline_highlevel.py` | Full PPG pipeline: load → preprocess → segment → SQI → classify |
| `SignalSQI` | `data/signal_sqi_class.py` | Core data container passed between all pipeline stages |
| `extract_sqi()` | `pipeline_functions.py` | Compute all SQI metrics for a list of segments |
| `classify_segments()` | `pipeline_functions.py` | Apply ruleset to SQI values; return ACCEPT/REJECT per segment |

---

## D. Complete SQI Metrics Reference

The `sqi_dict.json` resource file defines 47+ SQI metrics across 8 categories.

| Category | Metrics |
|---|---|
| **Statistical** | Kurtosis, skewness, entropy, SNR (signal-to-noise ratio), zero-crossing rate, mean-crossing rate, and per-beat variants of each (kurtosis_beat, skewness_beat, entropy_beat) |
| **Signal Processing** | SNR variants, zero-crossing rate, mean-crossing rate, correlogram-based metrics |
| **Cardiac-Specific** | QRS energy, ectopic beat fraction, MSQ (mean signal quality), interpolation quality score |
| **Frequency/Energy** | Band energy (LFE, QRSE, HFE, VHFP), peak frequency |
| **HRV Time Domain** | SDNN, RMSSD, CVSD, CVNN, NN mean, NN median, NN count |
| **Heart Rate** | HR mean, HR median, HR min, HR max, HR range |
| **Power Spectral** | LF/HF ratio, absolute power (LF, HF, VLF, total), relative power (LF, HF), normalized power (LFnu, HFnu) |
| **Nonlinear** | Poincaré SD1, Poincaré SD2, SD1/SD2 ratio, DTW distance (vs. clean template) |

---

## E. Rule System

The `rule_dict.json` resource file defines 51 rule definitions applied to SQI metric values. Rules use comparison operators (`<`, `>`, `<=`, `>=`, `==`) with scalar thresholds.

### Rule Evaluation Logic

```
RuleSet evaluation (all-or-nothing):
  For each segment:
    For each Rule in RuleSet:
      if rule.operator(sqi_value, rule.threshold) fails:
        return "reject"   → any single rule failure causes rejection
    return "accept"       → segment must pass ALL rules to be accepted
```

### Example Rules from `rule_dict.json`

| Metric | Operator | Threshold | Label | Notes |
|---|---|---|---|---|
| `mean_hr` | `>=` | 58 | accept | Minimum physiologically plausible HR |
| `mean_hr` | `<=` | 144 | accept | Maximum physiologically plausible HR |
| `mean_hr` | `<` | 58 | reject | Below physiological range → likely noise or detection failure |
| `mean_hr` | `>` | 144 | reject | Above physiological range → likely noise or tachycardia artifact |
| `sdnn` | `>=` | 7.93 | accept | Minimum expected HRV for a healthy adult |
| `sdnn` | `<=` | 676.0 | accept | Maximum expected HRV; above this is likely noise |
| `rmssd` | `>=` | 11.31 | accept | Minimum expected short-term HRV |
| `rmssd` | `<=` | 832.0 | accept | Maximum expected short-term HRV |

### Customization

The agent can override default thresholds by constructing custom `Rule` and `RuleSet` objects at runtime, enabling context-aware classification (e.g., relaxed thresholds for pediatric recordings or known arrhythmia patients).

---

## F. R-Peak / Peak Detection Algorithm Catalog

`vital_sqi` provides 14 peak detection algorithms — 7 for PPG and 7 for ECG — selected via the `peak_detector` integer parameter.

### PPG Peak Detection (IDs 1–7)

| ID | Name | Description |
|---|---|---|
| 1 | ADAPTIVE_THRESHOLD | Adaptive amplitude threshold method |
| 2 | COUNT_ORIG_METHOD | Count-originator method |
| 3 | CLUSTERER_METHOD | Clustering-based peak detection |
| 4 | SLOPE_SUM_METHOD | Slope sum function method |
| 5 | MOVING_AVERAGE_METHOD | Moving average envelope method |
| 6 | DEFAULT (vitalDSP) | Default method via vitalDSP library (recommended for PPG) |
| 7 | BILLAUER_METHOD | Billauer's peakdet algorithm |

### ECG R-Peak Detection (IDs 1–7)

| ID | Name | Description |
|---|---|---|
| 1 | HAMILTON | Hamilton & Tompkins (1986) detector |
| 2 | CHRISTOV | Christov (2004) real-time detector |
| 3 | ENGZEE | Engelse & Zeelenberg (1979) detector |
| 4 | SWT | Stationary Wavelet Transform detector |
| 5 | MVA | Moving Average (MVA) detector |
| 6 | MTEMP | Moving template correlation (default for ECG; `peak_detector=6`) |
| 7 | PAN_TOMPKINS | Pan & Tompkins (1985) classic detector |

> **Note:** For ECG functions, `peak_detector` defaults to `6` (MTEMP). For PPG functions, `peak_detector` defaults to `6` (DEFAULT/vitalDSP). The integer IDs are the same (1–7) but map to different algorithms per signal type.

---

## G. References

| # | Reference |
|---|---|
| 1 | Johnson, A.E.W., et al. "MIMIC-III, a freely accessible critical care database." *Scientific Data* 3, 160035 (2016). https://doi.org/10.1038/sdata.2016.35 |
| 2 | Goldberger, A.L., et al. "PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals." *Circulation* 101(23):e215–e220 (2000). |
| 3 | Moody, G.B., Mark, R.G. "The impact of the MIT-BIH Arrhythmia Database." *IEEE Engineering in Medicine and Biology Magazine* 20(3):45–50 (2001). |
| 4 | Orphanidou, C., et al. "Signal quality indices for the electrocardiogram and photoplethysmogram: Derivation and applications to wireless monitoring." *IEEE Journal of Biomedical and Health Informatics* 19(3):832–838 (2015). |
| 5 | Yeh, Y.C., Wang, W.J. "QRS complexes detection for ECG signal: The difference operation method." *Computer Methods and Programs in Biomedicine* 91(3):245–254 (2008). |
| 6 | Yao, S., et al. "ReAct: Synergizing Reasoning and Acting in Language Models." *ICLR 2023*. https://arxiv.org/abs/2210.03629 |
| 7 | Task Force of the European Society of Cardiology and the North American Society of Pacing and Electrophysiology. "Heart rate variability: standards of measurement, physiological interpretation, and clinical use." *Circulation* 93(5):1043–1065 (1996). |
| 8 | OUCRU internal documentation and clinical supervisor guidance — to be incorporated during development. |
