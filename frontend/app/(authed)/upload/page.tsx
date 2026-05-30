'use client';

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileUploadDropzone } from "@/components/upload/file-upload-dropzone";
import { useCreateAssessment, useAssessmentJob } from "@/lib/queries/assessment-queries";
import { Stat } from "@/components/ui/stat";
import type { Recording } from "@/lib/types";

export default function UploadPage() {
  const router = useRouter();
  const [uploadedRecordingId, setUploadedRecordingId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const createAssessment = useCreateAssessment();
  const { data: jobData } = useAssessmentJob(jobId ?? "");

  if (jobData?.status === "completed" && uploadedRecordingId) {
    router.push(`/recordings/${uploadedRecordingId}/monitor`);
  }

  const handleUploadSuccess = async (result: Recording | Recording[]) => {
    const recording = Array.isArray(result) ? result[0] : result;
    if (!recording) return;
    setUploadedRecordingId(recording.id);
    try {
      const job = await createAssessment.mutateAsync({ recording_id: recording.id });
      setJobId(job.job_id);
    } catch {
      router.push(`/recordings/${recording.id}/monitor`);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-foreground">Upload Recording</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Accepts CSV or Parquet files with ECG or PPG signal data.
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        {jobId ? (
          <div className="py-8 text-center space-y-3">
            <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
            <p className="text-sm font-medium text-foreground">
              Assessment running
              {jobData?.status && ` — `}
              {jobData?.progress !== undefined && (
                <Stat className="font-semibold">{jobData.progress}%</Stat>
              )}
            </p>
            <p className="text-xs text-muted-foreground">
              Redirecting to monitor when complete…
            </p>
          </div>
        ) : (
          <FileUploadDropzone onSuccess={handleUploadSuccess} />
        )}
      </div>
    </div>
  );
}
