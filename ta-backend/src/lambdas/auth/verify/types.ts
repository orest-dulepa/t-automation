import { User } from '@/entities/User';

export interface IVerifyRequest {
  email: string;
  otp: string;
}

export interface IVerifyResponse {
  user: Pick<User, 'id' | 'firstName' | 'lastName' | 'email' | 'organization' | 'role'>;
  accessToken: string;
  refreshToken: string;
}
