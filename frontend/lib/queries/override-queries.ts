'use client';

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { get, post } from "@/lib/api-client";
import type { OverrideEvent, EffectiveClassificationResponse } from "@/lib/types";

export function useSegmentOverrides(segmentId: string) {
  return useQuery<OverrideEvent[]>({
    queryKey: ["segmentOverrides", segmentId],
    queryFn: () => get<OverrideEvent[]>(`/api/segments/${segmentId}/overrides`),
    enabled: Boolean(segmentId),
  });
}

export function useEffectiveClassification(segmentId: string) {
  return useQuery<EffectiveClassificationResponse>({
    queryKey: ["effectiveClassification", segmentId],
    queryFn: () =>
      get<EffectiveClassificationResponse>(
        `/api/segments/${segmentId}/effective-classification`
      ),
    enabled: Boolean(segmentId),
  });
}

interface CreateOverridePayload {
  segmentId: string;
  label: "accept" | "reject";
  reason_category: string;
  note: string;
}

export function useCreateOverride() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ segmentId, ...body }: CreateOverridePayload) =>
      post<OverrideEvent>(`/api/segments/${segmentId}/overrides`, body),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["segmentOverrides", data.segment_id] });
      queryClient.invalidateQueries({
        queryKey: ["effectiveClassification", data.segment_id],
      });
    },
  });
}
