import { createActionCreators } from 'immer-reducer';

import { UserReducer } from '@/store/reducers/user';

export const userActions = createActionCreators(UserReducer);

export type UserActions =
  | ReturnType<typeof userActions.setIsLoggedIn>
  | ReturnType<typeof userActions.setIsPending>
  | ReturnType<typeof userActions.setUser>;
