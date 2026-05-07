# 02 — Problem Statement

[← Back to Index](../00-index.md)

---

## Context: OUCRU Data Collection

OUCRU (Oxford University Clinical Research Unit) conducts clinical research across Southeast Asia, deploying wearable devices and bedside monitors that continuously record physiological signals from study participants. The primary signal types are:

| Signal | Source | Typical Frequency |
|--------|--------|-------------------|
| ECG (Electrocardiogram) | Bedside monitors, wearable patches | 250–1000 Hz *(typical ranges — not client-specified)* |
| PPG (Photoplethysmogram) | Wearable wristbands, pulse oximeters | 25–250 Hz *(typical ranges — not client-specified)* |

These recordings are ingested into Electronic Data Capture (EDC) systems that store raw waveform files alongside clinical metadata. A single study session may produce hours of continuous waveform data per participant. At scale — across multiple sites, studies, and devices — the system ingests large volumes of high-frequency time-series data daily.

---

## Current Quality Control Approach

OUCRU's existing QC pipeline operates in two stages:

1. **Static rule-based checks** applied automatically at ingestion time. Rules flag records that violate fixed thresholds (e.g., signal amplitude out of range, missing duration, sampling rate mismatch).
2. **Manual human review** performed periodically by data engineers and clinical researchers who visually inspect flagged and sampled records to make accept/reject decisions.

---

## Pain Points

### 1. Human Review Does Not Scale

A human reviewer cannot continuously monitor hours of waveform data. Quality issues that occur mid-recording — sensor disconnection, patient movement, electrical interference — are only detectable through detailed inspection of the waveform itself. Manual review is:

- **Slow**: reviewing a single hour-long recording may take 15–30 minutes of expert time *(estimated — not client-specified)*
- **Expensive**: requires skilled clinical or engineering personnel
- **Delayed**: issues are typically discovered hours or days after data collection
- **Inconsistent**: inter-reviewer variability affects classification reliability

### 2. Static Rules Do Not Capture Contextual Quality Issues

Static threshold rules operate on summary statistics and structural properties. They cannot:

- Detect transient noise segments within an otherwise acceptable recording
- Distinguish artifact patterns that vary across device types and patient populations
- Reason about the clinical significance of a quality issue in context
- Adapt to new device sources without manual rule authoring

### 3. Heterogeneous Data Sources

OUCRU deploys multiple device types across different research sites. Each device produces waveforms with distinct:

- Sampling rates and bit depths
- Noise profiles and baseline wander characteristics
- File formats and metadata schemas

A single static rule set cannot handle this heterogeneity without extensive per-device configuration, which does not scale as new devices are added.

### 4. Growing Data Volume Outpaces Review Capacity

Clinical research data volumes are growing as studies scale and participant enrollment increases. The ratio of data volume to available reviewer time is worsening. Without automation, the review backlog will continue to grow.

---

## Gap Analysis

| Capability | Current State | Required State |
|------------|--------------|----------------|
| Continuous monitoring | Not possible (manual) | Automated, always-on |
| Contextual artifact detection | Not available (static rules) | LLM-orchestrated tool calls |
| Multi-device adaptability | Manual per-device rules | Configurable, generalised |
| Review throughput | Limited by human capacity | Scales with compute |
| Report generation | Manual compilation | Automated output |
| Time-to-detection | Hours to days | Near-immediate post-upload |

---

## Scope Note: Imaging Data

OUCRU's data quality challenges extend beyond waveform signals to imaging data. However, this project scopes the initial phase to waveform data (ECG, PPG) only, with imaging quality monitoring identified as a future extension.

---

## Cost of Undetected Quality Issues

Failing to detect data quality problems in clinical waveform recordings carries serious downstream consequences:

| Impact Area | Consequence |
|-------------|-------------|
| **Research data integrity** | Corrupted or noisy signals included in analysis produce unreliable study findings |
| **Regulatory compliance** | Clinical trial data submitted with undocumented quality issues may violate Good Clinical Practice (GCP) standards |
| **Resource waste** | Clinical staff time spent on data collection is wasted if recordings are later found unusable |
| **Patient safety (indirect)** | Research conclusions derived from poor-quality data may inform clinical guidelines incorrectly |
| **Reproducibility** | Studies using inconsistently quality-controlled data cannot be reliably reproduced |
