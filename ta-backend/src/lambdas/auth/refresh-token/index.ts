import { APIGatewayProxyHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { badData } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { UserRepository } from '@/repositories/User';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { ITokenPayload, TOKEN_TYPE } from '@/@types/auth';

import { createOrGetDBConnection } from '@/utils/db';
import { createToken, createRefreshToken, verifyToken } from '@/utils/jwt';

import { refreshTokenSchema } from './schema';
import { IRefreshTokenRequest, IRefreshTokenResponse } from './types';

const rawHandler: APIGatewayProxyHandler<IRefreshTokenRequest, IRefreshTokenResponse> = async (
  event,
) => {
  const { refreshToken: oldRefreshToken } = event.body;

  const { id, type } = verifyToken(oldRefreshToken) as ITokenPayload;

  if (type !== TOKEN_TYPE.REFRESH_TOKEN) {
    throw badData('invalid token type');
  }

  await createOrGetDBConnection();

  const userRepository = getCustomRepository(UserRepository);

  const user = await userRepository.getById(id);

  if (!user) {
    throw badData('invalid token type');
  }

  const accessToken = createToken(user.id);
  const refreshToken = createRefreshToken(user.id);

  return {
    statusCode: 200,
    body: {
      accessToken,
      refreshToken,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(refreshTokenSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
