import { createReducerFunction, ImmerReducer } from 'immer-reducer';

import { IUserProcessDetails } from '@/interfaces/user-process';

export interface IProcessDetailsState {
  isPending: boolean;
  isRejected: boolean;
  isArtifactDownloading: boolean;
  errorMsg: string;
  processDetails: IUserProcessDetails | null;
}

const initialState: IProcessDetailsState = {
  isPending: false,
  isRejected: false,
  isArtifactDownloading: false,
  errorMsg: '',
  processDetails: null,
};

export class ProcessDetailsReducer extends ImmerReducer<IProcessDetailsState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setIsArtifactDownloading(isArtifactDownloading: boolean) {
    this.draftState.isArtifactDownloading = isArtifactDownloading;
  }

  public setProcessDetails(processDetails: IUserProcessDetails) {
    this.draftState.isPending = false;
    this.draftState.processDetails = processDetails;
  }

  public setIsRejected(errMsg: string) {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
    this.draftState.errorMsg = errMsg;
  }

  public reset() {
    this.draftState = initialState;
  }
}

export default createReducerFunction(ProcessDetailsReducer, initialState);
