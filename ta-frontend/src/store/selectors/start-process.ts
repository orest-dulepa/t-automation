import { createSelector, Selector } from 'reselect';

import { IProcess } from '@/interfaces/process';

import { State } from '@/store';

const selectStartProcessState = (state: State) => state.startProcessReducer;

export const selectIsStartProcessPending: Selector<State, boolean> = createSelector(
  selectStartProcessState,
  ({ isPending }) => isPending,
);

export const selectIsStartProcessRejected: Selector<State, boolean> = createSelector(
  selectStartProcessState,
  ({ isRejected }) => isRejected,
);

export const selectIsStartProcess: Selector<State, IProcess | null> = createSelector(
  selectStartProcessState,
  ({ process }) => process,
);
