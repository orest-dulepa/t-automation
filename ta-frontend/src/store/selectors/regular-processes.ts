import { createSelector, Selector } from 'reselect';
import { IRegularProcess } from '@/interfaces/regular-process';
import { State } from '@/store';

const selectRegularProcessesState = (state: State) => state.regularProcessesReducer;

export const selectRegularProcesses: Selector<State, IRegularProcess[]> = createSelector(
  selectRegularProcessesState,
  ({ processes }) => processes,
);

export const selectIsRegularProcessesPending: Selector<State, boolean> = createSelector(
  selectRegularProcessesState,
  ({ isPending }) => isPending,
);

export const selectIsRegularProcessesRejected: Selector<State, boolean> = createSelector(
  selectRegularProcessesState,
  ({ isRejected }) => isRejected,
);
