import { createReducerFunction, ImmerReducer } from 'immer-reducer';

import { IUserProcess } from '@/interfaces/user-process';

export interface IFinishedProcessesState {
  isPending: boolean;
  isRejected: boolean;
  isMinorPending: boolean;
  processes: IUserProcess[];
  total: number;
}

const initialState: IFinishedProcessesState = {
  isPending: false,
  isRejected: false,
  isMinorPending: false,
  processes: [],
  total: 0,
};

export class FinishedProcessesReducer extends ImmerReducer<IFinishedProcessesState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setProcesses(processes: IUserProcess[], total: number) {
    this.draftState.isPending = false;
    this.draftState.processes = processes;
    this.draftState.total = total;
  }

  public setIsMinorPending(isMinorPending: boolean) {
    this.draftState.isMinorPending = isMinorPending;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }
}

export default createReducerFunction(FinishedProcessesReducer, initialState);
