import Joi from 'joi';
import { IVerifyRequest } from './types';

export const verifySchema = Joi.object<IVerifyRequest>({
  email: Joi.string().email().required(),
  otp: Joi.string().required(),
});
