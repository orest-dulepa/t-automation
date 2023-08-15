import { createSelector, Selector } from 'reselect';
import { IScheduledProcess } from '@/interfaces/scheduled-process';
import { State } from '@/store';

const selectScheduledProcessesState = (state: State) => state.scheduledProcessesReducer;

export const selectScheduledProcesses: Selector<State, IScheduledProcess[]> = createSelector(
  selectScheduledProcessesState,
  ({ processes }) => processes,
);

export const selectIsScheduledProcessesPending: Selector<State, boolean> = createSelector(
  selectScheduledProcessesState,
  ({ isPending }) => isPending,
);

export const selectIsScheduledProcessesRejected: Selector<State, boolean> = createSelector(
  selectScheduledProcessesState,
  ({ isRejected }) => isRejected,
);
