'use client';

import { useCallback, useState } from "react";
import { useUploadRecording, useBatchUpload } from "@/lib/queries/recording-queries";
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
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
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
      const result = await uploadSingle.mutateAsync(formData);
      onSuccess?.(result);
    } else {
      const result = await uploadBatch.mutateAsync(formData);
      onSuccess?.(result);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
          isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-white"
        }`}
      >
        <p className="text-sm text-gray-600">
          Drag &amp; drop CSV or Parquet files here, or{" "}
          <label className="cursor-pointer text-blue-600 underline">
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
          <ul className="mt-3 text-left text-sm text-gray-700 space-y-1">
            {files.map((f, i) => (
              <li key={i} className="truncate">{f.name}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Signal Type</label>
          <select
            value={signalType}
            onChange={(e) => setSignalType(e.target.value as "ecg" | "ppg")}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            {SIGNAL_TYPES.map((t) => (
              <option key={t} value={t}>{t.toUpperCase()}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Sampling Rate (Hz)</label>
          <input
            type="number"
            value={samplingRate}
            onChange={(e) => setSamplingRate(Number(e.target.value))}
            min={1}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Signal Column *</label>
        <input
          type="text"
          value={signalColumn}
          onChange={(e) => setSignalColumn(e.target.value)}
          required
          placeholder="e.g. ecg_lead_ii"
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Subject ID (optional)</label>
        <input
          type="text"
          value={subjectId}
          onChange={(e) => setSubjectId(e.target.value)}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Notes (optional)</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      {error && (
        <p className="text-sm text-red-600">
          Upload failed: {(error as Error).message}
        </p>
      )}
      {isSuccess && (
        <p className="text-sm text-green-600">Upload successful!</p>
      )}

      <button
        type="submit"
        disabled={isPending || !files.length || !signalColumn}
        className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {isPending ? "Uploading…" : `Upload ${files.length > 1 ? `${files.length} Files` : "File"}`}
      </button>
    </form>
  );
}
