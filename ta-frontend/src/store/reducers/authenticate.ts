import { createReducerFunction, ImmerReducer } from 'immer-reducer';

export enum AuthenticateSteps {
  signIn = 'signIn',
  signUp = 'signUp',
  verify = 'verify'
}

export interface IAuthenticateState {
  currentStep: AuthenticateSteps;
  isPending: boolean;
  isRejected: boolean;
  isNotAllowedEmail: boolean;
}

const initialState: IAuthenticateState = {
  currentStep: AuthenticateSteps.signIn,
  isPending: false,
  isRejected: false,
  isNotAllowedEmail: false,
};

export class AuthenticateReducer extends ImmerReducer<IAuthenticateState> {
  public setIsPending() {
    this.draftState.isPending = true;
    this.draftState.isRejected = false;
  }

  public setNextStep(nextStep: AuthenticateSteps) {
    this.draftState.isPending = false;
    this.draftState.isNotAllowedEmail = false;
    this.draftState.currentStep = nextStep;
  }

  public setIsRejected() {
    this.draftState.isPending = false;
    this.draftState.isRejected = true;
  }

  public setIsNotAllowedEmail(isNotAllowedEmail: boolean) {
    this.draftState.isNotAllowedEmail = isNotAllowedEmail;
  }

  public reset() {
    this.draftState = initialState;
  }
}

export default createReducerFunction(AuthenticateReducer, initialState);
