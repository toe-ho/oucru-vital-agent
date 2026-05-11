"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useDropzone } from "react-dropzone";
import { useQuery } from "@tanstack/react-query";
import { uploadRecording } from "@/services/recordings";
import { triggerAssessment, getJobStatus } from "@/services/assessments";
import { listRecordings } from "@/services/recordings";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [signalType, setSignalType] = useState<"ecg" | "ppg">("ppg");
  const [samplingRate, setSamplingRate] = useState(100);
  const [uploading, setUploading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [recordingId, setRecordingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"], "application/octet-stream": [".parquet", ".edf"] },
    maxFiles: 1,
  });

  // Poll job status while running
  useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (data) =>
      data?.state?.data?.status === "processing" || data?.state?.data?.status === "queued" ? 2000 : false,
    select: (data) => {
      if (data.status === "completed" && recordingId) {
        router.push(`/recordings/${recordingId}/monitor`);
      }
      return data;
    },
  });

  const { data: recentRecordings } = useQuery({
    queryKey: ["recordings"],
    queryFn: () => listRecordings({ limit: 10 }),
  });

  async function handleUpload() {
    if (!file) return;
    setError(null);
    setUploading(true);
    try {
      const uploaded = await uploadRecording(file, signalType, samplingRate);
      setRecordingId(uploaded.recording_id);
      const job = await triggerAssessment({ recording_id: uploaded.recording_id });
      setJobId(job.assessment_job_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setUploading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-brand-900 mb-6">Upload Waveform Recording</h1>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
          isDragActive ? "border-brand-700 bg-brand-100" : "border-gray-300 hover:border-brand-700"
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <p className="text-gray-800 font-medium">{file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)</p>
        ) : (
          <p className="text-gray-500">Drop a CSV, Parquet, or EDF file here, or click to select</p>
        )}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Signal Type</label>
          <div className="flex gap-4">
            {(["ppg", "ecg"] as const).map((t) => (
              <label key={t} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  value={t}
                  checked={signalType === t}
                  onChange={() => setSignalType(t)}
                  className="accent-brand-700"
                />
                <span className="text-sm uppercase font-medium">{t}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Sampling Rate (Hz)</label>
          <input
            type="number"
            value={samplingRate}
            onChange={(e) => setSamplingRate(Number(e.target.value))}
            className="border border-gray-300 rounded px-3 py-2 w-full text-sm"
            min={1}
          />
        </div>
      </div>

      {error && <p className="mt-4 text-red-600 text-sm">{error}</p>}

      {jobId && !error && (
        <p className="mt-4 text-brand-700 text-sm font-medium">
          Processing... redirecting when complete.
        </p>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="mt-6 w-full bg-brand-900 text-white py-3 rounded-lg font-medium disabled:opacity-40 hover:bg-brand-700 transition-colors"
      >
        {uploading ? "Uploading & Assessing..." : "Upload & Assess"}
      </button>

      {recentRecordings && recentRecordings.items.length > 0 && (
        <div className="mt-10">
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Recent Recordings</h2>
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="text-left px-3 py-2">Filename</th>
                <th className="text-left px-3 py-2">Type</th>
                <th className="text-left px-3 py-2">Status</th>
                <th className="text-left px-3 py-2">Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {recentRecordings.items.map((r) => (
                <tr key={r.recording_id} className="border-t hover:bg-gray-50 cursor-pointer"
                  onClick={() => router.push(`/recordings/${r.recording_id}/monitor`)}>
                  <td className="px-3 py-2">{r.filename}</td>
                  <td className="px-3 py-2 uppercase">{r.signal_type}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      r.status === "completed" ? "bg-green-100 text-green-800" :
                      r.status === "failed" ? "bg-red-100 text-red-800" : "bg-yellow-100 text-yellow-800"
                    }`}>{r.status}</span>
                  </td>
                  <td className="px-3 py-2 text-gray-500">{new Date(r.uploaded_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
