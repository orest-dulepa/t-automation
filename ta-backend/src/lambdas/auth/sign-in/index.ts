import { APIGatewayProxyHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { notFound } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { generateOTP } from '@/utils/otp';
import { createOrGetDBConnection } from '@/utils/db';
import { sendOtpViaEmail } from '@/utils/email';

import { UserRepository } from '@/repositories/User';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { signInSchema } from './schema';
import { ISignInRequest } from './types';

import { User } from '@/entities/User';

const rawHandler: APIGatewayProxyHandler<ISignInRequest> = async (event) => {
  await createOrGetDBConnection();

  const userRepository = getCustomRepository(UserRepository);

  const email = event.body.email.toLowerCase();

  const otp = generateOTP();

  const { affected } = await userRepository.updateOtpByEmail(email, otp);

  if (!affected) throw notFound('user was not found');

  let currentUser: User | undefined = await userRepository.getByEmailWithOrganizationAndRole(email);

  await sendOtpViaEmail(email, otp, currentUser.firstName);

  return {
    statusCode: 200,
    body: {},
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(signInSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
