import { createSelector, Selector } from 'reselect';

import { IUserProcess } from '@/interfaces/user-process';

import { State } from '@/store';

const selectFinishedProcessesState = (state: State) => state.finishedProcessesReducer;

export const selectFinishedProcesses: Selector<State, IUserProcess[]> = createSelector(
  selectFinishedProcessesState,
  ({ processes }) => processes,
);

export const selectIsFinishedProcessesPending: Selector<State, boolean> = createSelector(
  selectFinishedProcessesState,
  ({ isPending }) => isPending,
);

export const selectIsFinishedProcessesMinorPending: Selector<State, boolean> = createSelector(
  selectFinishedProcessesState,
  ({ isMinorPending }) => isMinorPending,
);

export const selectIsFinishedProcessesRejected: Selector<State, boolean> = createSelector(
  selectFinishedProcessesState,
  ({ isRejected }) => isRejected,
);

export const selectFinishedProcessesTotal: Selector<State, number> = createSelector(
  selectFinishedProcessesState,
  ({ total }) => total,
);
