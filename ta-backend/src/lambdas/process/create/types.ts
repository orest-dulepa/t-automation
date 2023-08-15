import { Process } from '@/entities/Process';

export interface IProcessCreateRequest
  extends Pick<Process, 'name' | 'type' | 'credentials' | 'properties'> {
  organizationId: number;
}

export interface IProcessCreateResponse
  extends Pick<Process, 'id' | 'name' | 'type' | 'properties'> {}
