import { createSelector, Selector } from 'reselect';
import { State } from '@/store';

const selectRemoveRegularProcessState = (state: State) => state.removeRegularProcessReducer;

export const selectRemoveRegularProcessId: Selector<State, number | null> = createSelector(
  selectRemoveRegularProcessState,
  ({ processId }) => processId,
);

export const selectIsRemoveRegularProcessesPending: Selector<State, boolean> = createSelector(
  selectRemoveRegularProcessState,
  ({ isPending }) => isPending,
);

export const selectIsRemoveRegularProcessesRejected: Selector<State, boolean> = createSelector(
  selectRemoveRegularProcessState,
  ({ isRejected }) => isRejected,
);
