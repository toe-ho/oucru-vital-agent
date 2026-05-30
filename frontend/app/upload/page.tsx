'use client';

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FileUploadDropzone } from "@/components/upload/file-upload-dropzone";
import { useCreateAssessment } from "@/lib/queries/assessment-queries";
import { useAssessmentJob } from "@/lib/queries/assessment-queries";
import type { Recording } from "@/lib/types";

export default function UploadPage() {
  const router = useRouter();
  const [uploadedRecordingId, setUploadedRecordingId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const createAssessment = useCreateAssessment();

  // Poll job status — only active after jobId is set
  const { data: jobData } = useAssessmentJob(jobId ?? "");

  // Redirect when job completes
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
      // Assessment kickoff failed — still navigate to monitor
      router.push(`/recordings/${recording.id}/monitor`);
    }
  };

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-sm text-blue-600 hover:underline">
            ← Dashboard
          </Link>
          <h1 className="text-xl font-bold text-gray-900">Upload Recording</h1>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-6">
          {jobId ? (
            <div className="py-8 text-center space-y-3">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
              <p className="text-sm font-medium text-gray-700">
                Assessment running
                {jobData?.status && ` (${jobData.status})`}
                {jobData?.progress !== undefined && ` — ${jobData.progress}%`}
              </p>
              <p className="text-xs text-gray-500">
                Redirecting to monitor when complete…
              </p>
            </div>
          ) : (
            <FileUploadDropzone onSuccess={handleUploadSuccess} />
          )}
        </div>
      </div>
    </main>
  );
}
