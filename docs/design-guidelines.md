# Design Guidelines

**Last Updated:** 2026-05-30  
**Framework:** Tailwind CSS + shadcn/ui (Radix UI primitives)  
**Target:** WCAG 2.1 AA accessibility

## Design Philosophy

1. **Clarity First** — Users should understand status and options at a glance
2. **Progressive Disclosure** — Advanced options behind secondary actions
3. **Consistency** — Reusable components with predictable behavior
4. **Accessibility** — Keyboard navigation, screen readers, color contrast
5. **Performance** — Minimal JavaScript, responsive images, efficient rendering

## Color Palette

### Status Colors (Semantic)

| Status | Hex | Tailwind | Usage |
|--------|-----|----------|-------|
| **Accept** | #10b981 | `emerald-500` | Segment passed QA, signal ready |
| **Reject** | #ef4444 | `red-500` | Segment failed QA, signal unusable |
| **Uncomputable** | #f59e0b | `amber-500` | Segment QA unclear, manual review needed |
| **Pending** | #6b7280 | `gray-500` | Assessment in progress, awaiting decision |
| **Stale** | #f59e0b | `amber-500` | Report outdated due to overrides |

### Neutral Colors

| Purpose | Hex | Tailwind | Usage |
|---------|-----|----------|-------|
| **Primary Text** | #1f2937 | `gray-900` | Headings, labels, body text |
| **Secondary Text** | #6b7280 | `gray-500` | Helper text, metadata |
| **Background** | #f9fafb | `gray-50` | Page background, cards |
| **Border** | #e5e7eb | `gray-200` | Dividers, form borders |
| **Disabled** | #d1d5db | `gray-300` | Disabled buttons, unavailable options |

### Interactive Colors

> **Updated 2026-05-30:** All interactive elements now use **Brand Indigo** (`#4338ca`). `blue-*` utilities are retired from components — use `bg-primary`, `text-primary`, `ring-ring` tokens.

| Element | Hex | Token | Usage |
|---------|-----|-------|-------|
| **Primary Button** | #4338ca | `bg-primary` | Main actions (assess, upload) — Brand Indigo |
| **Primary Hover** | #3730a3 | `bg-brand-hover` | Button hover state |
| **Dark Primary** | #6366f1 | `bg-primary` (dark) | Indigo-500 in `.dark` theme |
| **Danger Button** | #ef4444 | `bg-destructive` | Destructive actions (delete) |
| **Focus Ring** | #4338ca | `ring-ring` | Keyboard focus indicator ≥3:1 contrast |

### Dark Mode

> **Reclassified in-scope (2026-05-30).** Dark mode is fully implemented via `next-themes` + Tailwind `darkMode: "class"`. All tokens have `.dark` overrides in `globals.css`. The system respects OS preference (`defaultTheme="system"`).

| Feature | Status |
|---------|--------|
| Token dark variants | ✅ Implemented |
| `next-themes` provider | ✅ Implemented |
| Theme toggle in app shell | ✅ Implemented |
| No hydration flash | ✅ `suppressHydrationWarning` on `<html>` |

### Example Usage

```tsx
// Accept status badge
<span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-100 text-emerald-900">
  Accept
</span>

// Reject status badge
<span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-900">
  Reject
</span>

// Stale report warning
<div className="bg-amber-50 border border-amber-200 rounded p-4 text-amber-900">
  This report is stale. Please regenerate after reviewing segment overrides.
</div>
```

## Typography

### Scale

| Purpose | Font | Weight | Size | Line Height |
|---------|------|--------|------|-------------|
| **Page Title** | Inter | 600 | 32px | 40px |
| **Section Heading** | Inter | 600 | 24px | 32px |
| **Subsection** | Inter | 600 | 20px | 28px |
| **Label** | Inter | 500 | 14px | 20px |
| **Body** | Inter | 400 | 14px | 20px |
| **Small Text** | Inter | 400 | 12px | 16px |
| **Caption** | Inter | 400 | 11px | 16px |

### Examples

```tsx
// Page title
<h1 className="text-3xl font-semibold text-gray-900">Recordings</h1>

// Section heading
<h2 className="text-2xl font-semibold text-gray-900">Signal Quality</h2>

// Label
<label className="block text-sm font-medium text-gray-700">
  Classification
</label>

// Body text
<p className="text-sm text-gray-600">
  Segments with scores below thresholds are marked for review.
</p>

// Caption
<span className="text-xs text-gray-500">Last updated 5 minutes ago</span>
```

## Component Patterns

### Classification Badge

Used to display segment classification status.

```tsx
import { ClassificationBadge } from "@/components/ui/classification-badge";

export const SegmentCard = ({ segment }) => {
  return (
    <div className="p-4 border rounded">
      <span className="text-sm text-gray-600">Segment {segment.id}</span>
      <ClassificationBadge classification={segment.effective_classification} />
    </div>
  );
};
```

**Props:**
- `classification: "accept" | "reject" | "uncomputable"`
- `size?: "sm" | "md"` (default: md)
- `showLabel?: boolean` (default: true)

**Rendered HTML:**
```html
<!-- Accept -->
<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-100 text-emerald-900">
  Accept
</span>

<!-- Reject -->
<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-900">
  Reject
</span>

<!-- Uncomputable -->
<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-900">
  Uncomputable
</span>
```

### Segment Timeline

Visualizes segments in chronological order with color-coded status.

```tsx
import { SegmentTimeline } from "@/components/monitoring/segment-timeline";

export const RecordingMonitor = ({ segments }) => {
  return (
    <SegmentTimeline
      segments={segments}
      totalDuration={3600000}
      onSegmentClick={(segmentId) => {
        // Handle selection
      }}
      selectedSegmentId={activeSegmentId}
    />
  );
};
```

**Visual:**
```
0s                                           Duration: 3600s (1 hour)
│ ═══════ ═══════ ═══════ ┃ ═══════ ┃       Key:
└─────────────────────────────────────────  ═════ Accept
  │   │   │       │       │   │     │       ┃ ┃ ┃ Reject/Uncomputable
  └─ Accept
    └─ Accept
        └─ Reject
                └─ Accept
                    └─ Uncomputable
```

### SQI Scores Panel

Table showing individual SQI metric results.

```tsx
import { SqiScoresPanel } from "@/components/monitoring/sqi-scores-panel";

export const AssessmentResults = ({ segment, sqiResults, thresholds }) => {
  return (
    <SqiScoresPanel
      scores={sqiResults}
      thresholds={thresholds}
      variant="full"  // or "summary"
    />
  );
};
```

**Display:**

| Metric | Score | Threshold | Status |
|--------|-------|-----------|--------|
| HR Variability | 0.92 | > 0.70 | ✓ Pass |
| Motion | 0.45 | > 0.50 | ✗ Fail |
| SNR | 0.88 | > 0.70 | ✓ Pass |
| Baseline Wander | 0.77 | > 0.70 | ✓ Pass |

### Segment Override Panel

Form for reviewer/admin to override segment classification.

```tsx
import { SegmentOverridePanel } from "@/components/monitoring/segment-override-panel";

export const ReviewSegment = ({ segment, userRole }) => {
  const { mutate: submitOverride } = useOverrideMutation();

  const handleOverride = (classification, rationale) => {
    submitOverride({
      segment_id: segment.id,
      classification,
      rationale,
    });
  };

  return (
    <SegmentOverridePanel
      segment={segment}
      onSubmit={handleOverride}
      disabled={!["reviewer", "admin"].includes(userRole)}
    />
  );
};
```

**Features:**
- Dropdown to select classification (accept/reject/uncomputable)
- Text area for rationale (required)
- Submit button (reviewer/admin only)
- Shows current classification (read-only)
- Confirmation dialog on submit

### Report Viewer

Displays JSON report with freshness warning.

```tsx
import { ReportViewer } from "@/components/reports/report-viewer";

export const ReportPage = ({ report, freshness }) => {
  return (
    <ReportViewer
      report={report}
      isFresh={freshness.status === "fresh"}
      onRegenerate={handleRegenerate}
    />
  );
};
```

**Sections:**
- **Freshness Banner** (if stale)
- **Summary** — Overall assessment, recommendation
- **Timeline** — Colored segments with reasons
- **Flagged Segments** — Segments needing attention
- **Metrics** — Aggregated SQI statistics
- **Limitations** — Known constraints, caveats
- **Export Buttons** — HTML, PDF

### Waveform Viewer

Interactive line chart with segment overlays using Recharts.

```tsx
import { WaveformViewer } from "@/components/monitoring/waveform-viewer";

export const WaveformView = ({ recording, segments, onSegmentSelect }) => {
  return (
    <WaveformViewer
      recording={recording}
      segments={segments}
      selectedSegment={activeSegmentId}
      onSegmentClick={onSegmentSelect}
    />
  );
};
```

**Features:**
- Zoomable/pannable line chart
- Colored segment backgrounds
- Legend for colors
- Responsive width (container-dependent)
- No raw waveform array in props (metadata + stats only)

### Chatbot Panel

Chat interface with message history and suggested questions.

```tsx
import { ChatbotPanel } from "@/components/chat/chatbot-panel";

export const ChatPage = ({ recording }) => {
  const { messages, sendMessage, isLoading } = useChat(recording.id);

  return (
    <ChatbotPanel
      messages={messages}
      onSendMessage={sendMessage}
      isLoading={isLoading}
      suggestedQuestions={[
        "Why was segment 3 rejected?",
        "What does HR variability mean?",
        "How many segments passed QA?",
      ]}
    />
  );
};
```

**Features:**
- Message bubbles (user/system)
- Markdown rendering (system messages)
- Suggested questions (clickable)
- Loading indicator (while waiting for response)
- Keyboard submit (Enter), Shift+Enter for newline
- Auto-scroll to latest message

### File Upload Dropzone

Drag-and-drop or click to upload files.

```tsx
import { FileUploadDropzone } from "@/components/upload/file-upload-dropzone";

export const UploadPage = () => {
  const { mutate: uploadFiles, isLoading } = useUploadMutation();

  const handleFilesSelected = (files) => {
    uploadFiles(files);
  };

  return (
    <FileUploadDropzone
      onFilesSelected={handleFilesSelected}
      isLoading={isLoading}
      acceptedFormats={["csv", "parquet"]}
      maxFileSize={100 * 1024 * 1024}  // 100 MB
      multipleFiles={true}
    />
  );
};
```

**Features:**
- Drag-and-drop zone (visual feedback on hover)
- Click to open file picker
- File validation (format, size)
- Progress indicator (upload in progress)
- Error message display
- Success confirmation

## Layout Patterns

### Page Layout

```tsx
export default function RecordingMonitorPage() {
  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 p-6">
        <h1 className="text-3xl font-semibold text-gray-900">
          Recording: {recordingId}
        </h1>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-auto p-6">
        <div className="grid grid-cols-3 gap-6">
          {/* Left: Waveform */}
          <div className="col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <WaveformViewer {...} />
            </div>
          </div>

          {/* Right: Sidebar */}
          <aside className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <SqiScoresPanel {...} />
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <SegmentOverridePanel {...} />
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
```

### Modal Pattern

```tsx
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

export const ConfirmDeleteModal = ({ onConfirm, onCancel }) => {
  return (
    <Dialog open={true}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Recording?</DialogTitle>
          <DialogDescription>
            This action cannot be undone. All segments and reports will be deleted.
          </DialogDescription>
        </DialogHeader>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-white bg-red-500 rounded hover:bg-red-600"
          >
            Delete
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
```

### Loading & Error States

```tsx
// Loading state
export const LoadingState = ({ message = "Loading..." }) => {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      <span className="ml-3 text-gray-600">{message}</span>
    </div>
  );
};

// Error state
export const ErrorState = ({ error, onRetry }) => {
  return (
    <div className="bg-red-50 border border-red-200 rounded p-6 text-red-900">
      <h3 className="font-semibold">Error</h3>
      <p className="mt-2 text-sm">{error.message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Try Again
        </button>
      )}
    </div>
  );
};

// Empty state
export const EmptyState = ({ icon: Icon, title, message, action }) => {
  return (
    <div className="text-center p-12">
      <Icon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="mt-2 text-gray-600">{message}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
};
```

## Responsive Design

### Breakpoints

| Breakpoint | Width | Usage |
|------------|-------|-------|
| `sm` | 640px | Tablets (portrait) |
| `md` | 768px | Tablets (landscape) |
| `lg` | 1024px | Small desktops |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large desktops |

### Example: Responsive Grid

```tsx
// Single column on mobile, 2 on tablet, 3 on desktop
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => (
    <Card key={item.id}>{item.name}</Card>
  ))}
</div>

// Navigation responsive
<nav className="hidden lg:flex">
  {/* Desktop navigation */}
</nav>
<button className="lg:hidden">
  {/* Mobile menu toggle */}
</button>
```

## Accessibility (WCAG 2.1 AA)

### Keyboard Navigation

All interactive elements must be keyboard accessible:

```tsx
// Button
<button className="focus:outline-none focus:ring-2 focus:ring-blue-500">
  Click me
</button>

// Link
<a href="/path" className="focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
  Go to page
</a>

// Form input
<input
  type="text"
  className="focus:outline-none focus:ring-2 focus:ring-blue-500"
  aria-label="Your name"
/>
```

### Screen Reader Support

```tsx
// Icon button needs label
<button aria-label="Close dialog" onClick={onClose}>
  <XIcon />
</button>

// Headings structure
<h1>Main Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>

// Form inputs with labels
<label htmlFor="email">Email address</label>
<input id="email" type="email" />

// Live regions for updates
<div aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>
```

### Color Contrast

Minimum 4.5:1 contrast ratio for normal text:

```tsx
// Good contrast (pass)
<span className="text-gray-900 bg-white">Text</span>

// Bad contrast (fail)
<span className="text-gray-400 bg-gray-100">Text</span>
```

## Dark Mode (Future)

Reserved for post-MVP. Structure CSS for toggle-ready design:

```tsx
// Tailwind dark: pseudo-class
<div className="bg-white dark:bg-gray-900">
  <p className="text-gray-900 dark:text-gray-50">Text</p>
</div>
```

## Icon Usage

All icons from `lucide-react`:

```tsx
import { ChevronDown, AlertCircle, CheckCircle } from "lucide-react";

// Icon button
<button className="p-2 hover:bg-gray-100 rounded">
  <ChevronDown className="h-5 w-5" />
</button>

// Inline icon
<span className="inline-flex items-center gap-2">
  <AlertCircle className="h-4 w-4 text-amber-500" />
  Warning message
</span>
```

## Animation & Transitions

Keep animations subtle and purposeful:

```tsx
// Fade in
<div className="animate-fadeIn">Content</div>

// Slide down
<div className="transition-all duration-200 transform translate-y-0 opacity-100">
  Content
</div>

// Custom animation (globals.css)
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease-in-out;
}
```

## Component Library

All components located in `frontend/components/`:

- **`ui/`** — Primitive components (badge, button, dialog, etc.)
- **`upload/`** — File upload (dropzone, progress)
- **`monitoring/`** — Assessment visualization (waveform, timeline, SQI, override)
- **`reports/`** — Report display (viewer, export)
- **`chat/`** — Chat interface (chatbot panel, messages)
- **`common/`** — Shared (nav, footer, auth state)

## Storybook (Post-MVP)

Reserve for component documentation and visual regression testing:

```bash
npm install -D @storybook/next
npm run storybook
```

Example story:

```tsx
// components/ui/classification-badge.stories.tsx
import type { Meta, StoryObj } from "@storybook/react";
import { ClassificationBadge } from "./classification-badge";

const meta: Meta<typeof ClassificationBadge> = {
  component: ClassificationBadge,
  title: "UI/ClassificationBadge",
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Accept: Story = {
  args: { classification: "accept" },
};

export const Reject: Story = {
  args: { classification: "reject" },
};

export const Uncomputable: Story = {
  args: { classification: "uncomputable" },
};
```
