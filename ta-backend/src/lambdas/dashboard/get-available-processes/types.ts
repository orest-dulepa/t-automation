import { Process } from '@/entities/Process';

export type IGetAvailableProcesses = Pick<Process, 'id' | 'name' | 'type' | 'properties'>[];
