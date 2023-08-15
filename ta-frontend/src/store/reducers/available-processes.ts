import { createReducerFunction, ImmerReducer } from 'immer-reducer';

import { IProcess } from '@/interfaces/process';

export interface IAvailableProcessesState {
  isPending: boolean;
  isRejected: boolean;
  processes: IProcess[];
}

const initialState: IAvailableProcessesState = {
  isPending: false,
  isRejected: false,
  processes: [],
};

export class AvailableProcessesReducer extends ImmerReducer<IAvailableProcessesState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setProcesses(processes: IProcess[]) {
    this.draftState.isPending = false;
    this.draftState.processes = processes;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }
}

export default createReducerFunction(AvailableProcessesReducer, initialState);
