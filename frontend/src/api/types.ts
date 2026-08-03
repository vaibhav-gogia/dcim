export interface DataCenter {
  id: string;
  name: string;
  location: string | null;
}

export interface FloorRack {
  id: string;
  name: string;
  u_height: number;
  pos_x: number;
  pos_y: number;
}

export interface DataCenterFloor {
  id: string;
  name: string;
  racks: FloorRack[];
}

export type PowerState = "unknown" | "off" | "booting" | "on" | "shutting_down" | "cycling";

export interface SystemElevation {
  id: string;
  name: string;
  u_position: number;
  u_height: number;
  system_type: string;
  power_state: PowerState;
}

export interface RackElevation {
  id: string;
  name: string;
  u_height: number;
  systems: SystemElevation[];
}

export interface SystemDetail {
  id: string;
  rack_id: string;
  name: string;
  u_position: number;
  u_height: number;
  system_type: string;
  manufacturer: string | null;
  model: string | null;
  serial_number: string | null;
  bmc_driver_type: string;
  power_state: PowerState;
  power_state_updated_at: string | null;
}

export interface SystemHealth {
  power_state: PowerState;
  temps_c: Record<string, number>;
  fans_rpm: Record<string, number>;
  psus: Record<string, string>;
  read_at: string;
}

export interface PDUOutlet {
  id: string;
  outlet_number: number;
  state: "on" | "off";
  connected_system_id: string | null;
  connected_system_name: string | null;
}

export interface PDUWithOutlets {
  id: string;
  name: string;
  outlet_count: number;
  driver_type: string;
  outlets: PDUOutlet[];
}

export interface PowerActionResponse {
  power_state: PowerState;
}

export interface OutletActionResponse {
  state: "on" | "off";
}
