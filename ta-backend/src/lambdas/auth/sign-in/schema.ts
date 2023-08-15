import Joi from 'joi';
import { ISignInRequest } from './types';

export const signInSchema = Joi.object<ISignInRequest>({
  email: Joi.string().email().required(),
});
