import Joi from 'joi';
import { ISignUpRequest } from './types';

export const signUpSchema = Joi.object<ISignUpRequest>({
  email: Joi.string().email().required(),
  firstName: Joi.string().required(),
  lastName: Joi.string().required(),
});
