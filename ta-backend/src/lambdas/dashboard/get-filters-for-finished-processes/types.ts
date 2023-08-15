import { Process } from '@/entities/Process';
import { User } from '@/entities/User';

export interface IGetFiltersForFinishedProcesses {
  processes: Process[];
  users: User[];
}
