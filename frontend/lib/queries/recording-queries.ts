'use client';

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post } from "@/lib/api-client";
import type { Recording } from "@/lib/types";

interface RecordingsPage {
  items: Recording[];
  total: number;
  page: number;
  page_size: number;
}

export function useRecordings(page = 1) {
  return useQuery<RecordingsPage>({
    queryKey: ["recordings", page],
    queryFn: () => get<RecordingsPage>("/api/recordings", { page }),
  });
}

export function useRecording(id: string) {
  return useQuery<Recording>({
    queryKey: ["recording", id],
    queryFn: () => get<Recording>(`/api/recordings/${id}`),
    enabled: Boolean(id),
  });
}

export function useUploadRecording() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) =>
      post<Recording>("/api/recordings/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recordings"] });
    },
  });
}

export function useBatchUpload() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (formData: FormData) =>
      post<Recording[]>("/api/recordings/batch-upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recordings"] });
    },
  });
}
