import { createReducerFunction, ImmerReducer } from 'immer-reducer';

import { IUserProcess } from '@/interfaces/user-process';

export interface IActiveProcessesState {
  isPending: boolean;
  isRejected: boolean;
  processes: IUserProcess[];
}

const initialState: IActiveProcessesState = {
  isPending: false,
  isRejected: false,
  processes: [],
};

export class ActiveProcessesReducer extends ImmerReducer<IActiveProcessesState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setProcesses(processes: IUserProcess[]) {
    processes.sort((a, b) => a.id - b.id);

    this.draftState.isPending = false;
    this.draftState.processes = processes;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }
}

export default createReducerFunction(ActiveProcessesReducer, initialState);
