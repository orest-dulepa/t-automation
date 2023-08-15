import { createSelector, Selector } from 'reselect';

import { State } from '@/store';

import { IUser } from '@/interfaces/user';
import { ROLE } from '@/interfaces/role';

const selectUserState = (state: State) => state.userReducer;

export const selectIsUserLoggedIn: Selector<State, boolean> = createSelector(
  selectUserState,
  ({ isLoggedIn }) => isLoggedIn,
);

export const selectIsUserPending: Selector<State, boolean> = createSelector(
  selectUserState,
  ({ isPending }) => isPending,
);

export const selectUser: Selector<State, IUser | null> = createSelector(
  selectUserState,
  ({ user }) => user,
);

export const selectIsUserManagerOrAdmin: Selector<State, boolean> = createSelector(
  selectUserState,
  ({ user }) => {
    if (!user) return false;

    const { id } = user.role;

    return id === ROLE.ADMIN || id === ROLE.MANAGER;
  },
);

export const selectIsUserAdmin: Selector<State, boolean> = createSelector(
  selectUserState,
  ({ user }) => {
    if (!user) return false;

    const { id } = user.role;

    return id === ROLE.ADMIN;
  },
);
