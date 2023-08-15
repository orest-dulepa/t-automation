import { APIGatewayProxyHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { forbidden } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { createOrGetDBConnection } from '@/utils/db';
import { createToken, createRefreshToken } from '@/utils/jwt';

import { UserRepository } from '@/repositories/User';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { verifySchema } from './schema';
import { IVerifyRequest, IVerifyResponse } from './types';

const rawHandler: APIGatewayProxyHandler<IVerifyRequest, IVerifyResponse> = async (event) => {
  await createOrGetDBConnection();

  const userRepository = getCustomRepository(UserRepository);

  let { email, otp } = event.body;
  email = email.toLowerCase();

  const user = await userRepository.getByEmailWithOrganizationAndRole(email);

  if (!user || user?.otp !== otp) throw forbidden();

  await userRepository.updateOtpByEmail(email, null);

  const accessToken = createToken(user.id);
  const refreshToken = createRefreshToken(user.id);

  return {
    statusCode: 200,
    body: {
      user: {
        id: user.id,
        firstName: user.firstName,
        lastName: user.lastName,
        email: user.email,
        role: user.role,
        organization: user.organization
      },
      accessToken,
      refreshToken,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(verifySchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
