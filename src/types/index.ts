// Approval types
export interface ApprovalRequest {
  id: string;
  execution_id: string;
  agent_name: string;
  agent_role: string;
  action_type: string;
  action_description: string;
  reasoning: string;
  potential_impact: string;
  requires_human_approval: boolean;
  status: string;
  requested_by: string;
  requested_at: string;
  expires_at: string | null;
  approved_by: string | null;
  approved_at: string | null;
  rejected_by: string | null;
  rejected_at: string | null;
  rejection_reason: string | null;
  cancelled_by: string | null;
  cancelled_at: string | null;
  cancellation_reason: string | null;
  updated_at: string;
  is_expired: boolean;
  is_pending: boolean;
}

export interface ApprovalCreate {
  execution_id?: string;
  agent_name?: string;
  agent_role?: string;
  action_type: string;
  action_description: string;
  reasoning: string;
  potential_impact: string;
  expires_at?: string;
}

export interface ApprovalUpdate {
  action_type?: string;
  action_description?: string;
  reasoning?: string;
  potential_impact?: string;
  expires_at?: string;
}

export interface ApprovalListResponse {
  approvals: ApprovalRequest[];
  count: number;
}

// Artifact types
export interface Artifact {
  id: string;
  project_id: string;
  task_id: string | null;
  execution_id: string | null;
  name: string;
  type: string;
  version: number;
  description: string | null;
  path: string | null;
  size: number | null;
  mime_type: string | null;
  checksum: string | null;
  author_id: string | null;
  created_at: string;
  extra_data: Record<string, any> | null;
  is_public: boolean;
}

export interface ArtifactCreate {
  project_id: string;
  task_id?: string | null;
  execution_id?: string | null;
  name: string;
  type: string;
  description?: string | null;
  path?: string | null;
  size?: number | null;
  mime_type?: string | null;
  checksum?: string | null;
  is_public?: boolean;
}

export interface ArtifactUpdate {
  name?: string | null;
  description?: string | null;
  path?: string | null;
  size?: number | null;
  mime_type?: string | null;
  checksum?: string | null;
  is_public?: boolean | null;
}

export interface ArtifactResponse {
  id: string;
  project_id: string;
  task_id: string | null;
  execution_id: string | null;
  name: string;
  type: string;
  version: number;
  description: string | null;
  path: string | null;
  size: number | null;
  mime_type: string | null;
  checksum: string | null;
  author_id: string | null;
  created_at: string;
  extra_data: Record<string, any> | null;
  is_public: boolean;
}

export interface ArtifactListResponse {
  artifacts: Artifact[];
  count: number;
}