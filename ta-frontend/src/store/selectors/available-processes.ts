import { createSelector, Selector } from 'reselect';

import { IProcess } from '@/interfaces/process';

import { State } from '@/store';

const selectAvailableProcessesState = (state: State) => state.availableProcessesReducer;

export const selectAvailableProcesses: Selector<State, IProcess[]> = createSelector(
  selectAvailableProcessesState,
  ({ processes }) => processes,
);

export const selectIsAvailableProcessesPending: Selector<State, boolean> = createSelector(
  selectAvailableProcessesState,
  ({ isPending }) => isPending,
);

export const selectIsAvailableProcessesRejected: Selector<State, boolean> = createSelector(
  selectAvailableProcessesState,
  ({ isRejected }) => isRejected,
);
