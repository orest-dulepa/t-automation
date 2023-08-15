import { createReducerFunction, ImmerReducer } from 'immer-reducer';

import { IUser } from '@/interfaces/user';

export interface UserState {
  isLoggedIn: boolean;
  isPending: boolean;
  user: IUser | null;
}

const initialState: UserState = {
  isLoggedIn: false,
  isPending: false,
  user: null,
};

export class UserReducer extends ImmerReducer<UserState> {
  public setIsLoggedIn(isLoggedIn: boolean) {
    this.draftState.isLoggedIn = isLoggedIn;
  }

  public setIsPending(isLoading: boolean) {
    this.draftState.isPending = isLoading;
  }

  public setUser(user: IUser | null) {
    this.draftState.user = user;
  }
}

export default createReducerFunction(UserReducer, initialState);
