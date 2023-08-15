import { IUser } from '@/interfaces/user';

export interface ISignInBody {
  email: string;
}

export interface ISignUpBody {
  email: string;
  firstName: string;
  lastName: string;
}

export interface IVerifyBody {
  email: string;
  otp: string;
}

export interface IVerifyResponse {
  user: IUser;
  accessToken: string;
  refreshToken: string;
}
