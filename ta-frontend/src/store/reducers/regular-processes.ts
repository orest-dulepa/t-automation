import { createReducerFunction, ImmerReducer } from 'immer-reducer';
import { IRegularProcess } from '@/interfaces/regular-process';

export interface IRegularProcessesState {
  isPending: boolean;
  isRejected: boolean;
  processes: IRegularProcess[];
}

const initialState: IRegularProcessesState = {
  isPending: false,
  isRejected: false,
  processes: [],
};

export class RegularProcessesReducer extends ImmerReducer<IRegularProcessesState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setProcesses(processes: IRegularProcess[]) {
    processes.sort((a, b) => a.id - b.id);

    this.draftState.isPending = false;
    this.draftState.processes = processes;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }
}

export default createReducerFunction(RegularProcessesReducer, initialState);
