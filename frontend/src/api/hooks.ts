import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./client";
import {
  DataCenter,
  DataHall,
  DataHallFloor,
  DataCenterFloor,
  OutletActionResponse,
  PDUWithOutlets,
  PowerActionResponse,
  PowerConnection,
  RackElevation,
  SystemDetail,
  SystemHealth,
} from "./types";

export function useDataCenters() {
  return useQuery({
    queryKey: ["datacenters"],
    queryFn: () => api.get<DataCenter[]>("/datacenters"),
  });
}

export function useDataCenterFloor(datacenterId: string) {
  return useQuery({
    queryKey: ["datacenter-floor", datacenterId],
    queryFn: () => api.get<DataCenterFloor>(`/datacenters/${datacenterId}/floor`),
    enabled: !!datacenterId,
  });
}

export function useRackElevation(rackId: string) {
  return useQuery({
    queryKey: ["rack-elevation", rackId],
    queryFn: () => api.get<RackElevation>(`/racks/${rackId}/elevation`),
    enabled: !!rackId,
    refetchInterval: 5000,
  });
}

export function useRackPdus(rackId: string) {
  return useQuery({
    queryKey: ["rack-pdus", rackId],
    queryFn: () => api.get<PDUWithOutlets[]>(`/racks/${rackId}/pdus`),
    enabled: !!rackId,
    refetchInterval: 5000,
  });
}

export function useSystemDetail(systemId: string | null) {
  return useQuery({
    queryKey: ["system", systemId],
    queryFn: () => api.get<SystemDetail>(`/systems/${systemId}`),
    enabled: !!systemId,
  });
}

export function useSystemHealth(systemId: string | null) {
  return useQuery({
    queryKey: ["system-health", systemId],
    queryFn: () => api.get<SystemHealth>(`/systems/${systemId}/health`),
    enabled: !!systemId,
    refetchInterval: 3000,
  });
}

export function usePowerAction(systemId: string, rackId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (action: "on" | "off" | "cycle") =>
      api.post<PowerActionResponse>(`/systems/${systemId}/power/${action}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rack-elevation", rackId] });
      queryClient.invalidateQueries({ queryKey: ["system-health", systemId] });
      queryClient.invalidateQueries({ queryKey: ["system", systemId] });
      queryClient.invalidateQueries({ queryKey: ["rack-pdus", rackId] });
    },
  });
}

export function useOutletAction(pduId: string, rackId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ outletId, action }: { outletId: string; action: "on" | "off" | "cycle" }) =>
      api.post<OutletActionResponse>(`/pdus/${pduId}/outlets/${outletId}/${action}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rack-pdus", rackId] });
      queryClient.invalidateQueries({ queryKey: ["rack-elevation", rackId] });
      queryClient.invalidateQueries({ queryKey: ["system-health"] });
      queryClient.invalidateQueries({ queryKey: ["system"] });
      queryClient.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
}

export function useDataCenter(datacenterId: string) {
  return useQuery({ queryKey: ["datacenter", datacenterId], queryFn: () => api.get<DataCenter>(`/datacenters/${datacenterId}`), enabled: !!datacenterId });
}
export function useDataHalls(datacenterId: string) {
  return useQuery({ queryKey: ["data-halls", datacenterId], queryFn: () => api.get<DataHall[]>(`/datacenters/${datacenterId}/data-halls`), enabled: !!datacenterId });
}
export function useDataHallFloor(dataHallId: string) {
  return useQuery({ queryKey: ["data-hall-floor", dataHallId], queryFn: () => api.get<DataHallFloor>(`/data-halls/${dataHallId}/floor`), enabled: !!dataHallId });
}

export function usePowerConnections(systemId: string) {
  return useQuery({ queryKey: ["power-connections", systemId], queryFn: () => api.get<PowerConnection[]>(`/systems/${systemId}/power-connections`) });
}
export function useWirePower(systemId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: { pdu_outlet_id: string; psu_label: string }) => api.post(`/systems/${systemId}/power-connections`, body),
    onSuccess: () => client.invalidateQueries(),
  });
}
export function useUnwirePower() {
  const client = useQueryClient();
  return useMutation({ mutationFn: (id: string) => api.delete(`/power-connections/${id}`), onSuccess: () => client.invalidateQueries() });
}
