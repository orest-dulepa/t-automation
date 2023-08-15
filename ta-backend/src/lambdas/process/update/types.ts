import { Process } from '@/entities/Process';

export interface IProcessUpdatePathParams {
  id: string;
}

export interface IProcessUpdateRequest
  extends Partial<Pick<Process, 'name' | 'type' | 'properties'>> {}

export interface IProcessUpdateResponse
  extends Pick<Process, 'id' | 'name' | 'type' | 'properties'> {}
