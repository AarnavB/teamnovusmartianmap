import type { BenchmarkResult, PlanResponse, Point, ReplanResponse, RegistryResponse, TerrainData } from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof payload.detail === 'string' ? payload.detail : `API request failed (${response.status})`;
    throw new Error(message);
  }
  return payload as T;
}

export const api = {
  health: () => request<{ status: string }>('/api/health'),
  terrain: () => request<TerrainData>('/api/terrain'),
  registry: () => request<RegistryResponse>('/api/registry'),
  plan: (start: Point, goal: Point, constraints: Record<string, number>) =>
    request<PlanResponse>('/api/routes', { method: 'POST', body: JSON.stringify({ start, goal, constraints }) }),
  benchmark: (start: Point, goal: Point, constraints: Record<string, number>) =>
    request<{ benchmark_scope: string; results: BenchmarkResult[]; warning: string }>('/api/benchmark', { method: 'POST', body: JSON.stringify({ start, goal, constraints }) }),
  replan: (planId: string, obstacle: Point) =>
    request<ReplanResponse>('/api/replan', { method: 'POST', body: JSON.stringify({ plan_id: planId, obstacle }) }),
  reset: () => request<{ status: string }>('/api/reset', { method: 'POST' }),
};
