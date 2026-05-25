# 12 — UI/UX Specifications

[← Back to Index](../00-index.md)

---

## Overview

**Scope:** All UI screens display waveform data (ECG, PPG) only. Imaging visualization is deferred to future phases.

This document defines wireframe layouts, component breakdowns, interaction patterns, and design principles for the six primary screens of the Agentic AI Data Quality Monitoring web application.

---

## Design Principles

| Principle | Description |
|---|---|
| Clinical aesthetic | Clean, minimal interface appropriate for medical research contexts. No decorative elements. Data density over visual flair. |
| Accessibility | WCAG 2.1 AA compliance. Sufficient color contrast ratios. Keyboard-navigable. Screen-reader compatible labels. |
| Responsive | Optimized for desktop (1280px+) and tablet (768px–1279px). Mobile is out of scope for this version. |
| Consistency | shadcn/ui component library throughout. Consistent spacing (4px grid), typography (Inter font), and interaction patterns. |
| Data clarity | Charts prefer clarity over decoration. Axis labels always visible. Tooltips on hover for precise values. |

---

## Color System

| Token | Hex | Usage |
|---|---|---|
| `color-accept` | `#22c55e` | Accepted segments, passing metrics, success states |
| `color-reject` | `#ef4444` | Rejected segments, failing metrics, error states |
| `color-borderline` | `#eab308` | Borderline quality, warnings, pending states |
| `color-info` | `#3b82f6` | Links, active selections, informational badges |
| `color-surface` | `#ffffff` | Card and panel backgrounds |
| `color-background` | `#f8fafc` | Page background (light gray) |
| `color-border` | `#e2e8f0` | Dividers, card borders |
| `color-text-primary` | `#0f172a` | Primary body text |
| `color-text-muted` | `#64748b` | Labels, captions, secondary text |

---

## Screen 1: Upload Page

### Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  [LOGO] OUCRU Signal Quality Monitor          [Settings] [?Help]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Upload Recording                                                   │
│  ─────────────────────────────────────────────────────────         │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │              ↑  Drag & drop signal file here                │   │
│  │                                                             │   │
│  │         Supported formats: EDF, MIT/WFDB, CSV              │   │
│  │                 Maximum file size: 500 MB                   │   │
│  │                                                             │   │
│  │                  [ Browse Files ]                           │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Signal Configuration                                               │
│  ┌────────────────────────────┐  ┌──────────────────────────────┐  │
│  │ Signal Type                │  │ Sampling Rate (Hz)           │  │
│  │ ○ ECG   ○ PPG              │  │ [  250  ] ▲▼                │  │
│  └────────────────────────────┘  └──────────────────────────────┘  │
│                                                                     │
│                              [ Upload & Analyze ]                   │
│                                                                     │
│  ─────────────────────────────────────────────────────────         │
│  Recent Uploads                                                     │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Filename          │ Type │ Duration │ Status    │ Uploaded   │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ ecg_patient_01... │ ECG  │ 5m 32s   │ ● Completed│ 2h ago   │  │
│  │ ppg_sample_07.csv │ PPG  │ 10m 0s   │ ● Processing│ 5m ago  │  │
│  │ ecg_trial_003.edf │ ECG  │ 30m 0s   │ ✕ Failed  │ 1d ago   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Behavior |
|---|---|
| Dropzone | Accepts drag-and-drop or click-to-browse. Validates file extension on drop. Shows file name + size preview after selection. Rejects files > 500 MB with inline error message. |
| Signal Type Radio | ECG / PPG options. Required before upload. |
| Sampling Rate Input | Number input with up/down arrows. Accepts 50–10000 Hz. Shows warning if value differs from file metadata (when detectable). |
| Upload Button | Disabled until file + signal type selected. Shows spinner and "Processing…" text during upload. |
| Recent Uploads Table | Shows last 10 uploads. Status uses color-coded badges: green (completed), blue (processing), red (failed). Clicking a row navigates to Monitoring Screen. |

---

## Screen 2: Monitoring Screen

### Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  [←] ECG Recording — ecg_patient_01.edf       [Export] [Report]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────┐ ┌─────────────┐  │
│  │ WAVEFORM DISPLAY                             │ │ SQI Scores  │  │
│  │                                              │ │ ─────────── │  │
│  │  mV ↑                                        │ │ Seg #12     │  │
│  │  0.8│    ╭╮     ╭╮     ╭╮    ╭╮             │ │             │  │
│  │  0.4│   ╭╯╰╮  ╭╯╰╮  ╭╯╰╮  ╭╯╰╮            │ │ SNR         │  │
│  │   0 │──╯   ╰──╯   ╰──╯   ╰──╯   ╰──────    │ │ 18.4 dB  ✓ │  │
│  │ -0.4│                                        │ │             │  │
│  │     └──────────────────────────────── s      │ │ Kurtosis    │  │
│  │      0    2    4    6    8   10              │ │ 4.21     ✓ │  │
│  │                                              │ │             │  │
│  │  ████████████████ ████ ██████████████████   │ │ Skewness    │  │
│  │  [accept ██████] [rej] [accept █████████]   │ │ -0.34    ✓ │  │
│  │                                              │ │             │  │
│  └──────────────────────────────────────────────┘ │ Perf. Idx   │  │
│                                                    │ 0.72     ✓ │  │
│  Segment Navigation                                │             │  │
│  ┌──────────────────────────────────────────────┐ │ ZCR         │  │
│  │ [◀ Prev]  Segment: [12 ▼] / 47  [Next ▶]   │ │ 0.08     ✓ │  │
│  │                                              │ │             │  │
│  │ Classification: ● Accepted  [ Override ▼ ]  │ │ Overall     │  │
│  │ Quality Score: 0.87                          │ │ Score: 0.87 │  │
│  └──────────────────────────────────────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Behavior |
|---|---|
| Waveform Display | Recharts-based line chart. X-axis: time in seconds. Y-axis: amplitude (mV or normalized). Highlights the current segment's time range with a shaded overlay. |
| Color-coded segment bar | Horizontal bar below waveform. Each segment is rendered as a colored block: green (accept), red (reject), yellow (borderline/pending). Clicking a block navigates to that segment. |
| Segment Navigation | Prev/Next buttons step through segments sequentially. Dropdown selector allows jumping to any segment by number. Updates waveform view and SQI panel simultaneously. |
| Classification Badge | Displays the original AI classification and the current effective classification. Override controls are shown only to `admin` and `reviewer` users. MVP override labels are limited to `accept` and `reject`, and saving requires reason category plus note. Manual overrides are stored as append-only superseding events and flagged distinctly. |
| SQI Scores Panel | Lists all computed metrics for the current segment. Each row shows: metric name, value, pass/fail checkmark. Failing metrics shown in `color-reject` red. Passing metrics in `color-text-muted`. |

---

## Screen 3: Quality Dashboard

### Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Quality Dashboard              [Recording: ecg_patient_01 ▼] [↻]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐  │
│  │ Overall Score │ │   Accepted   │ │   Rejected   │ │  Pending  │  │
│  │              │ │              │ │              │ │           │  │
│  │     0.76     │ │   38 / 47    │ │    7 / 47    │ │   2 / 47  │  │
│  │   ████████░  │ │    80.9%     │ │    14.9%     │ │    4.3%   │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └───────────┘  │
│                                                                     │
│  ┌──────────────────────────────────┐ ┌────────────────────────┐   │
│  │ Accept/Reject Ratio              │ │ Alerts                 │   │
│  │                                  │ │ ────────────────────── │   │
│  │  Accept ████████████████ 80.9%   │ │ ⚠ Seg 12: SNR below   │   │
│  │  Reject ████ 14.9%               │ │   threshold (8.2 dB)  │   │
│  │  Pending ██ 4.3%                 │ │                        │   │
│  │                                  │ │ ⚠ Seg 33: High ZCR    │   │
│  └──────────────────────────────────┘ │   (0.61, max 0.5)     │   │
│                                       │                        │   │
│  Timeline Heatmap                     │ ✓ No baseline drift    │   │
│  ┌──────────────────────────────────┐ │   detected             │   │
│  │  0  5  10  15  20  25  30  35  40│ └────────────────────────┘   │
│  │  ▓▓▓▓▓░▓▓▓▓▓▓▓▓░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓│                              │
│  │  (▓=accept, ░=reject, ▒=pending) │                              │
│  └──────────────────────────────────┘                              │
│                                                                     │
│  Recent Recordings                                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Recording          │ Type │ Segments │ Score │ Date          │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │ ecg_patient_01.edf │ ECG  │ 47       │ 0.76  │ 2026-04-03   │  │
│  │ ppg_sample_07.csv  │ PPG  │ 60       │ 0.91  │ 2026-04-02   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Behavior |
|---|---|
| Summary Cards | 4 KPI cards: overall quality score (0–1 with mini gauge), accepted count/percent, rejected count/percent, pending count/percent. |
| Bar Chart | Horizontal stacked bar showing accept/reject/pending proportions. Uses system color tokens. |
| Alerts Panel | Agent-generated alerts for segments with notable quality issues. Each alert links to that segment in the Monitoring Screen. Green checkmarks for passing conditions. |
| Timeline Heatmap | One block per segment across the recording duration. Color encodes classification. Hovering a block shows tooltip with segment number and quality score. Clicking navigates to Monitoring Screen at that segment. |
| Recent Recordings Table | Sortable by date, score, or segment count. Clicking a row switches the dashboard to that recording. |

---

## Screen 4: Report Viewer

### Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Report: ecg_patient_01.edf                [PDF] [HTML] [Print]     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  OUCRU Signal Quality Assessment Report                     │   │
│  │  Recording: ecg_patient_01.edf   │  Generated: 2026-04-03   │   │
│  │  Signal Type: ECG                │  Duration: 5m 32s        │   │
│  │  Sampling Rate: 250 Hz           │  Overall Score: 0.76     │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │  1. Executive Summary                                       │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  The recording contains 47 segments. 38 (80.9%) were        │   │
│  │  accepted, 7 (14.9%) rejected. Primary rejection causes:    │   │
│  │  low SNR (4 segments), high ZCR (2 segments), motion        │   │
│  │  artifact (1 segment).                                      │   │
│  │                                                             │   │
│  │  2. Quality Timeline                                        │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  [Timeline chart embedded — same as dashboard heatmap]      │   │
│  │                                                             │   │
│  │  3. Flagged Segments                                        │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  │ Seg │ Time     │ Reason              │ Score │ Class    │  │   │
│  │  │  12 │ 1:54–2:04│ SNR below threshold │ 0.31  │ REJECT  │  │   │
│  │  │  33 │ 5:20–5:30│ High ZCR            │ 0.44  │ REJECT  │  │   │
│  │                                                             │   │
│  │  4. Recommendations                                         │   │
│  │  ─────────────────────────────────────────────────────────  │   │
│  │  • Re-record segments 12 and 33 if clinically significant.  │   │
│  │  • Review electrode contact around the 2-minute mark.      │   │
│  │  • Overall recording quality is acceptable for analysis.   │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Behavior |
|---|---|
| Report Header | Recording metadata: filename, signal type, sampling rate, duration, overall score. Fixed at top of report body. |
| Section Navigation | Sticky left sidebar (on wide screens) with anchor links to each report section: Summary, Timeline, Flagged Segments, Recommendations. |
| Timeline Chart | Embedded Recharts timeline/heatmap-style visualization (same data as dashboard). Read-only in report view. |
| Flagged Segments Table | Lists rejected and borderline segments with time range, primary rejection reason (from agent reasoning), quality score, and classification label. |
| Recommendations | Bullet list generated by the agent's interpretation of quality patterns. Rendered from `content_json.recommendations` array. |
| Export Buttons | **PDF**: triggers backend `/reports/{id}/export/pdf` endpoint. **HTML**: downloads standalone HTML file. **Print**: `window.print()` with print-specific CSS. |

---

## Screen 5: Settings Page

### Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Settings                                       [Save] [Reset All]  │
├──────────────────┬──────────────────────────────────────────────────┤
│  ▶ SQI Thresholds│                                                   │
│  ▶ Segmentation  │  SQI Thresholds                                  │
│  ▶ Agent Config  │  ──────────────────────────────────────────────  │
│  ▶ Import/Export │  Configure the accept/reject boundaries for each  │
│                  │  quality metric. Leave blank for no bound.       │
│                  │                                                   │
│                  │  ┌────────────────────────────────────────────┐  │
│                  │  │ Metric        │Category │ Min  │ Max │ Edit │  │
│                  │  ├────────────────────────────────────────────┤  │
│                  │  │ snr           │ stat    │ 10.0 │  — │  ✎  │  │
│                  │  │ kurtosis      │ stat    │  2.0 │20.0│  ✎  │  │
│                  │  │ skewness      │ stat    │ -2.0 │ 2.0│  ✎  │  │
│                  │  │ perf_index    │ waveform│  0.5 │  — │  ✎  │  │
│                  │  │ zero_cr       │ waveform│  — │ 0.5│  ✎  │  │
│                  │  └────────────────────────────────────────────┘  │
│                  │                                                   │
│                  │  Segmentation Configuration                      │
│                  │  ──────────────────────────────────────────────  │
│                  │  Window Duration   [10] seconds  ●──────○        │
│                  │  (range: 5–60s)                                  │
│                  │                                                   │
│                  │  Overlap           [ ] Enable overlap            │
│                  │  Overlap duration  [0] seconds (if enabled)      │
│                  │                                                   │
│                  │  Split Type        ● Time   ○ Beat count         │
│                  │                                                   │
│                  │  Import/Export Configuration                     │
│                  │  ──────────────────────────────────────────────  │
│                  │  [ Export Config JSON ]  [ Import Config JSON ]  │
└──────────────────┴──────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Behavior |
|---|---|
| Left Sidebar Nav | Accordion-style section navigation. Highlights active section. Sections: SQI Thresholds, Segmentation, Agent Config, Import/Export. |
| SQI Thresholds Table | Each row is one metric. Edit button opens an inline row form with min/max number inputs. Empty field means "no bound". Validation: min must be less than max. |
| Segmentation Config | Duration slider (5–60s, step 1). Overlap checkbox enables/disables overlap seconds input. Split type radio (time vs beat count). |
| Agent Config | Model name input, temperature slider (0–1, step 0.05), max steps number, timeout seconds. |
| Save/Reset Buttons | Save persists all changes to `settings` table via `PUT /api/settings/thresholds`. Reset All restores factory defaults after confirmation dialog. |
| Import/Export JSON | Export downloads current settings as a JSON file. Import uploads a JSON file and populates all fields for review before saving. |

---

## Screen 6: Chatbot Panel

### Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Agent Chat                          Recording: [ecg_patient_01 ▼]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │  🤖  Hello! I have analyzed ecg_patient_01.edf.            │   │
│  │      The recording has an overall quality score of 0.76.   │   │
│  │      7 segments were rejected. Ask me anything.            │   │
│  │                                                             │   │
│  │  👤  Why was segment 12 rejected?                          │   │
│  │                                                             │   │
│  │  🤖  Segment 12 (1:54–2:04) was rejected because the SNR  │   │
│  │      was 8.2 dB, which is below the minimum threshold of   │   │
│  │      10.0 dB. This indicates significant noise relative to │   │
│  │      the signal amplitude. This may be caused by electrode │   │
│  │      movement or poor skin contact at that time point.     │   │
│  │                                                             │   │
│  │  👤  Which metric caused the most rejections?              │   │
│  │                                                             │   │
│  │  🤖  SNR (Signal-to-Noise Ratio) caused 4 out of 7        │   │
│  │      rejections, making it the primary quality issue in    │   │
│  │      this recording.                                       │   │
│  │                                                 [2026-04-03]│   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Suggested Questions                                                │
│  [ Why was segment 45 rejected? ]  [ What is the overall quality?] │
│  [ Which metric failed the most?]  [ Is this recording usable?  ]  │
│                                                                     │
│  ┌──────────────────────────────────────────────┐ [ Send ↵ ]       │
│  │ Ask a question about this recording...       │                  │
│  └──────────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Behavior |
|---|---|
| Recording Context Selector | Dropdown to select which recording the chat context refers to. Switching recordings clears the chat history and sends a new context initialization message. |
| Message Area | Scrollable list of user and assistant messages. Auto-scrolls to bottom on new message. Human messages right-aligned, agent messages left-aligned. Timestamps shown per exchange. |
| Suggested Questions | Pre-built question chips that populate the input field on click. Dynamically updated based on the selected recording's anomalies (e.g., chips mention specific rejected segment numbers). |
| Input Field | Multi-line text input. Sends on Enter (Shift+Enter for newline). Disabled while awaiting agent response. Shows typing indicator (three dots) during processing. |
| Message Rendering | Agent responses render markdown (bold, bullet lists). Code/metric values rendered in monospace. |

---

## Navigation Structure

```
/                          → Upload Page (default landing)
/recordings/:id/monitor    → Monitoring Screen
/recordings/:id/report     → Report Viewer
/dashboard                 → Quality Dashboard
/settings                  → Settings Page
/chat                      → Chatbot Panel (can also open as side panel)
```

### Global Navigation Bar

Present on all screens. Contains:
- Logo / app name (links to `/`)
- Navigation links: Dashboard, Chat
- Settings icon (links to `/settings`)
- Help icon (opens documentation modal)
