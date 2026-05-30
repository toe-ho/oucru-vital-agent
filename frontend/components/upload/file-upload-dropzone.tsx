'use client';

import { useCallback, useState } from "react";
import { useUploadRecording, useBatchUpload } from "@/lib/queries/recording-queries";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { Recording } from "@/lib/types";

interface FileUploadDropzoneProps {
  onSuccess?: (recordings: Recording | Recording[]) => void;
}

const SIGNAL_TYPES = ["ecg", "ppg"] as const;

export function FileUploadDropzone({ onSuccess }: FileUploadDropzoneProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [signalType, setSignalType] = useState<"ecg" | "ppg">("ecg");
  const [samplingRate, setSamplingRate] = useState(250);
  const [signalColumn, setSignalColumn] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [notes, setNotes] = useState("");

  const uploadSingle = useUploadRecording();
  const uploadBatch = useBatchUpload();

  const isPending = uploadSingle.isPending || uploadBatch.isPending;
  const isSuccess = uploadSingle.isSuccess || uploadBatch.isSuccess;
  const error = uploadSingle.error ?? uploadBatch.error;

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = Array.from(e.dataTransfer.files).filter(
      (f) => f.name.endsWith(".csv") || f.name.endsWith(".parquet")
    );
    setFiles((prev) => [...prev, ...dropped]);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setFiles(Array.from(e.target.files));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files.length || !signalColumn) return;

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    formData.append("signal_type", signalType);
    formData.append("sampling_rate", String(samplingRate));
    formData.append("signal_column", signalColumn);
    if (subjectId) formData.append("subject_id", subjectId);
    if (notes) formData.append("notes", notes);

    if (files.length === 1) {
      onSuccess?.(await uploadSingle.mutateAsync(formData));
    } else {
      onSuccess?.(await uploadBatch.mutateAsync(formData));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Dropzone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        className={cn(
          "rounded-lg border-2 border-dashed p-8 text-center transition-colors",
          isDragging
            ? "border-primary bg-brand-ink"
            : "border-border bg-muted/30 hover:border-primary/50"
        )}
      >
        <p className="text-sm text-muted-foreground">
          Drag &amp; drop CSV or Parquet files here, or{" "}
          <label className="cursor-pointer text-primary underline hover:text-brand-hover">
            browse
            <input
              type="file"
              multiple
              accept=".csv,.parquet"
              onChange={handleFileChange}
              className="sr-only"
            />
          </label>
        </p>
        {files.length > 0 && (
          <ul className="mt-3 text-left text-sm text-foreground space-y-1">
            {files.map((f, i) => (
              <li key={i} className="truncate font-mono text-xs">{f.name}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="signal-type" className="block text-xs font-medium text-foreground mb-1">Signal Type</label>
          <select
            id="signal-type"
            value={signalType}
            onChange={(e) => setSignalType(e.target.value as "ecg" | "ppg")}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {SIGNAL_TYPES.map((t) => (
              <option key={t} value={t}>{t.toUpperCase()}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="sampling-rate" className="block text-xs font-medium text-foreground mb-1">Sampling Rate (Hz)</label>
          <Input
            id="sampling-rate"
            type="number"
            value={samplingRate}
            onChange={(e) => setSamplingRate(Number(e.target.value))}
            min={1}
          />
        </div>
      </div>

      <div>
        <label htmlFor="signal-column" className="block text-xs font-medium text-foreground mb-1">Signal Column *</label>
        <Input
          id="signal-column"
          type="text"
          value={signalColumn}
          onChange={(e) => setSignalColumn(e.target.value)}
          required
          placeholder="e.g. ecg_lead_ii"
        />
      </div>

      <div>
        <label htmlFor="subject-id" className="block text-xs font-medium text-foreground mb-1">Subject ID (optional)</label>
        <Input
          id="subject-id"
          type="text"
          value={subjectId}
          onChange={(e) => setSubjectId(e.target.value)}
        />
      </div>

      <div>
        <label htmlFor="upload-notes" className="block text-xs font-medium text-foreground mb-1">Notes (optional)</label>
        <Textarea
          id="upload-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
        />
      </div>

      {error && (
        <p className="text-sm text-reject">Upload failed: {(error as Error).message}</p>
      )}
      {isSuccess && (
        <p className="text-sm text-accept">Upload successful!</p>
      )}

      <Button
        type="submit"
        className="w-full"
        disabled={isPending || !files.length || !signalColumn}
      >
        {isPending ? "Uploading…" : `Upload ${files.length > 1 ? `${files.length} Files` : "File"}`}
      </Button>
    </form>
  );
}
