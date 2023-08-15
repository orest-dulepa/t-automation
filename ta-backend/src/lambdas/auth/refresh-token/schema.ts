import Joi from 'joi';
import { IRefreshTokenRequest } from './types';

export const refreshTokenSchema = Joi.object<IRefreshTokenRequest>({
  refreshToken: Joi.string().required(),
});
