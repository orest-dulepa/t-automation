import { User } from '@/entities/User';

export interface IMeResponse
  extends Pick<User, 'id' | 'firstName' | 'lastName' | 'email' | 'organization'> {}
