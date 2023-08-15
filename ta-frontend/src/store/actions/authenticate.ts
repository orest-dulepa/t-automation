import { createActionCreators } from 'immer-reducer';

import TokensLocalStorage from '@/local-storage/TokensLocalStorage';

import { AuthenticateReducer, AuthenticateSteps } from '@/store/reducers/authenticate';

import { AsyncAction } from './common';
import { userActions } from './user';

export const authenticateActions = createActionCreators(AuthenticateReducer);

export type AuthenticateActions =
  | ReturnType<typeof authenticateActions.setIsPending>
  | ReturnType<typeof authenticateActions.setNextStep>
  | ReturnType<typeof authenticateActions.setIsRejected>
  | ReturnType<typeof authenticateActions.setIsNotAllowedEmail>
  | ReturnType<typeof authenticateActions.reset>;

export const restoreAuthenticateAsync = (): AsyncAction => async (
  dispatch,
  _,
  { mainApiProtected },
) => {
  try {
    dispatch(userActions.setIsPending(true));

    const user = await mainApiProtected.getMe();

    dispatch(userActions.setUser(user));
    dispatch(userActions.setIsLoggedIn(true));
  } catch (e) {
    dispatch(userActions.setIsLoggedIn(false));
  } finally {
    dispatch(userActions.setIsPending(false));
  }
};

export const signInAsync = (email: string): AsyncAction => async (dispatch, _, { mainApi }) => {
  try {
    dispatch(authenticateActions.setIsPending());

    await mainApi.signIn({ email });

    dispatch(authenticateActions.setNextStep(AuthenticateSteps.verify));
  } catch (e) {
    if (e?.response?.status === 404) {
      dispatch(authenticateActions.setNextStep(AuthenticateSteps.signUp));
      return;
    }

    dispatch(authenticateActions.setIsRejected());
  }
};

export const signUpAsync = (
  email: string,
  firstName: string,
  lastName: string,
): AsyncAction => async (dispatch, _, { mainApi }) => {
  try {
    dispatch(authenticateActions.setIsPending());

    await mainApi.signUp({ email, firstName, lastName });

    dispatch(authenticateActions.setNextStep(AuthenticateSteps.verify));
  } catch (e) {
    if (e?.response?.data?.msg === 'not allowed email') {
      dispatch(authenticateActions.setIsNotAllowedEmail(true));
    }

    dispatch(authenticateActions.setIsRejected());
  }
};

export const verifyAsync = (email: string, otp: string): AsyncAction => async (
  dispatch,
  _,
  { mainApi },
) => {
  try {
    dispatch(authenticateActions.setIsPending());

    const response = await mainApi.verify({ email, otp });

    const { accessToken, refreshToken, user } = response;

    const tokensLocalStorage = TokensLocalStorage.getInstance();

    tokensLocalStorage.setAccessToken(accessToken);
    tokensLocalStorage.setRefreshToken(refreshToken);

    dispatch(userActions.setUser(user));
    dispatch(userActions.setIsLoggedIn(true));

    dispatch(authenticateActions.reset());
  } catch (e) {
    dispatch(authenticateActions.setIsRejected());
  }
};

export const logoutAsync = (): AsyncAction => async (dispatch) => {
  const tokensLocalStorage = TokensLocalStorage.getInstance();

  tokensLocalStorage.clear();

  dispatch(userActions.setIsLoggedIn(false));
  dispatch(userActions.setUser(null));
};
