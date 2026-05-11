"use client";

import { QueryClient } from "@tanstack/react-query";

let queryClient: QueryClient | undefined;

export function getQueryClient(): QueryClient {
  if (!queryClient) {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 30_000,
          retry: 1,
        },
      },
    });
  }
  return queryClient;
}
