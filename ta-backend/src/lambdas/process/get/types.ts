import { Process } from '@/entities/Process';

export interface IProcessGetPathParams {
  id: string;
}

export interface IProcessGetResponse extends Pick<Process, 'id' | 'name' | 'type' | 'properties'> {}
