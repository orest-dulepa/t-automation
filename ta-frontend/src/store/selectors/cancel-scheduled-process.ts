import { createSelector, Selector } from 'reselect';

import { State } from '@/store';

const selectCancelScheduledProcessState = (state: State) => state.cancelScheduledProcessReducer;

export const selectCancelScheduledProcessId: Selector<State, number | null> = createSelector(
  selectCancelScheduledProcessState,
  ({ processId }) => processId,
);

export const selectIsCancelScheduledProcessesPending: Selector<State, boolean> = createSelector(
  selectCancelScheduledProcessState,
  ({ isPending }) => isPending,
);

export const selectIsCancelScheduledProcessesRejected: Selector<State, boolean> = createSelector(
  selectCancelScheduledProcessState,
  ({ isRejected }) => isRejected,
);
