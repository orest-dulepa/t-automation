import { createReducerFunction, ImmerReducer } from 'immer-reducer';

export interface ICancelScheduledProcessState {
  isPending: boolean;
  isRejected: boolean;
  processId: null | number;
}

const initialState: ICancelScheduledProcessState = {
  isPending: false,
  isRejected: false,
  processId: null,
};

export class CancelScheduledProcessReducer extends ImmerReducer<ICancelScheduledProcessState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }

  public setProcessId(processId: number) {
    this.draftState.processId = processId;
  }

  public reset() {
    this.draftState = initialState;
  }
}

export default createReducerFunction(CancelScheduledProcessReducer, initialState);
