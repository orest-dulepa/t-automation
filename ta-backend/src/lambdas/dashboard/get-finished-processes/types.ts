import { UsersProcesses } from '@/entities/UsersProcesses';

export interface IGetFinishedUserProcessesQueryParams {
  processes_filter?: string;
  statuses_filter?: string;
  inputs_filter?: string;
  end_times_filter?: string;
  executed_by_filter?: string;
  processes_sort?: '0' | '1';
  run_number_sort?: '0' | '1';
  duration_sort?: '0' | '1';
  end_times_sort?: '0' | '1';
  executed_by_sort?: '0' | '1';
  amount?: string;
  page?: string;
}

export type IGetFinishedUserProcesses = {
  processes: UsersProcesses[],
  total: number,
}
