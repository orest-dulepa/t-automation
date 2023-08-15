import { createReducerFunction, ImmerReducer } from 'immer-reducer';

import { IProcess } from '@/interfaces/process';

interface IStartProcessState {
  isPending: boolean;
  isRejected: boolean;
  process: null | IProcess;
}

const initialState: IStartProcessState = {
  isPending: false,
  isRejected: false,
  process: null,
};

export class StartProcessReducer extends ImmerReducer<IStartProcessState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }

  public setProcess(process: IProcess) {
    this.draftState.process = process;
  }

  public reset() {
    this.draftState = initialState;
  }
}

export default createReducerFunction(StartProcessReducer, initialState);
