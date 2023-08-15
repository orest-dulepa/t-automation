import { createReducerFunction, ImmerReducer } from 'immer-reducer';

export interface IRemoveRegularProcessState {
  isPending: boolean;
  isRejected: boolean;
  processId: null | number;
}

const initialState: IRemoveRegularProcessState = {
  isPending: false,
  isRejected: false,
  processId: null,
};

export class RemoveRegularProcessReducer extends ImmerReducer<IRemoveRegularProcessState> {
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

export default createReducerFunction(RemoveRegularProcessReducer, initialState);
