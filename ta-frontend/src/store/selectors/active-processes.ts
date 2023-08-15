import { createSelector, Selector } from 'reselect';

import { IUserProcess } from '@/interfaces/user-process';

import { State } from '@/store';

const selectActiveProcessesState = (state: State) => state.activeProcessesReducer;

export const selectActiveProcesses: Selector<State, IUserProcess[]> = createSelector(
  selectActiveProcessesState,
  ({ processes }) => processes,
);

export const selectIsActiveProcessesPending: Selector<State, boolean> = createSelector(
  selectActiveProcessesState,
  ({ isPending }) => isPending,
);

export const selectIsActiveProcessesRejected: Selector<State, boolean> = createSelector(
  selectActiveProcessesState,
  ({ isRejected }) => isRejected,
);
