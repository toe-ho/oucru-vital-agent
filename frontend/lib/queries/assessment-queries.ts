'use client';

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post } from "@/lib/api-client";
import type { AssessmentJob, JobResultsResponse, AgentLogEntry } from "@/lib/types";

const POLLING_STATUSES = new Set(["queued", "processing"]);

export function useAssessmentJob(jobId: string) {
  return useQuery<AssessmentJob>({
    queryKey: ["assessmentJob", jobId],
    queryFn: () => get<AssessmentJob>(`/api/assess/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && POLLING_STATUSES.has(status) ? 3000 : false;
    },
  });
}

export function useJobResults(jobId: string) {
  return useQuery<JobResultsResponse>({
    queryKey: ["jobResults", jobId],
    queryFn: () => get<JobResultsResponse>(`/api/assess/${jobId}/results`),
    enabled: Boolean(jobId),
  });
}

export function useJobLogs(jobId: string) {
  return useQuery<AgentLogEntry[]>({
    queryKey: ["jobLogs", jobId],
    queryFn: () => get<AgentLogEntry[]>(`/api/assess/${jobId}/logs`),
    enabled: Boolean(jobId),
  });
}

export function useRecordingJobs(recordingId: string) {
  return useQuery<AssessmentJob[]>({
    queryKey: ["recordingJobs", recordingId],
    queryFn: () => get<AssessmentJob[]>(`/api/recordings/${recordingId}/jobs`),
    enabled: Boolean(recordingId),
  });
}

interface CreateAssessmentPayload {
  recording_id: string;
  options?: Record<string, unknown>;
}

export function useCreateAssessment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateAssessmentPayload) =>
      post<AssessmentJob>("/api/assess", payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["assessmentJob", data.job_id] });
    },
  });
}
