import { createSelector, Selector } from 'reselect';

import { State } from '@/store';
import { AuthenticateSteps } from '@/store/reducers/authenticate';

const selectAuthenticateState = (state: State) => state.authenticateReducer;

export const selectCurrentAuthenticateStep: Selector<State, AuthenticateSteps> = createSelector(
  selectAuthenticateState,
  ({ currentStep }) => currentStep,
);

export const selectIsAuthenticatePending: Selector<State, boolean> = createSelector(
  selectAuthenticateState,
  ({ isPending }) => isPending,
);

export const selectIsAuthenticateRejected: Selector<State, boolean> = createSelector(
  selectAuthenticateState,
  ({ isRejected }) => isRejected,
);

export const selectIsNotAllowedEmail: Selector<State, boolean> = createSelector(
  selectAuthenticateState,
  ({ isNotAllowedEmail }) => isNotAllowedEmail,
);
