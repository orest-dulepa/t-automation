import { createSelector, Selector } from 'reselect';

import { IUserProcessDetails } from '@/interfaces/user-process';

import { State } from '@/store';

const selectProcessDetailsState = (state: State) => state.processDetailsReducer;

export const selectProcessDetails: Selector<State, IUserProcessDetails | null> = createSelector(
  selectProcessDetailsState,
  ({ processDetails }) => processDetails,
);

export const selectIsProcessDetailsPending: Selector<State, boolean> = createSelector(
  selectProcessDetailsState,
  ({ isPending }) => isPending,
);

export const selectIsArtifactDownloading: Selector<State, boolean> = createSelector(
  selectProcessDetailsState,
  ({ isArtifactDownloading }) => isArtifactDownloading,
);

export const selectIsProcessDetailsRejected: Selector<State, boolean> = createSelector(
  selectProcessDetailsState,
  ({ isRejected }) => isRejected,
);

export const selectProcessDetailsErrorMsg: Selector<State, string> = createSelector(
  selectProcessDetailsState,
  ({ errorMsg }) => errorMsg,
);
