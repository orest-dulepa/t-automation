import { OrganizationsToProcesses } from '@/entities/OrganizationsToProcesses';

export interface IProcessLinkRequest {
  processId: number;
  organizationId: number;
}

export interface IProcessLinkResponse extends OrganizationsToProcesses {}
