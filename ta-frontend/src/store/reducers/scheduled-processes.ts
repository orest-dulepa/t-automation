import { createReducerFunction, ImmerReducer } from 'immer-reducer';

import { IScheduledProcess } from '@/interfaces/scheduled-process';

export interface IScheduledProcessesState {
  isPending: boolean;
  isRejected: boolean;
  processes: IScheduledProcess[];
}

const initialState: IScheduledProcessesState = {
  isPending: false,
  isRejected: false,
  processes: [],
};

export class ScheduledProcessesReducer extends ImmerReducer<IScheduledProcessesState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setProcesses(processes: IScheduledProcess[]) {
    processes.sort((a, b) => a.id - b.id);

    this.draftState.isPending = false;
    this.draftState.processes = processes;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }
}

export default createReducerFunction(ScheduledProcessesReducer, initialState);
