import { APIGatewayProxyHandler } from 'aws-lambda';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';
import { badRequest } from '@hapi/boom';
import { getCustomRepository } from 'typeorm';

import { generateOTP } from '@/utils/otp';
import { createOrGetDBConnection } from '@/utils/db';
import { sendOtpViaEmail } from '@/utils/email';

import { UserRepository } from '@/repositories/User';
import { OrganizationRepository } from '@/repositories/Organization';

import { User } from '@/entities/User';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { signUpSchema } from './schema';
import { ISignUpRequest } from './types';

const rawHandler: APIGatewayProxyHandler<ISignUpRequest> = async (event) => {
  await createOrGetDBConnection();

  const userRepository = getCustomRepository(UserRepository);
  const organizationRepository = getCustomRepository(OrganizationRepository);

  let { email, firstName, lastName } = event.body;
  email = email.toLowerCase();

  const domain = email.split('@')[1];
  const subdomain = domain.split('.')[0].toLowerCase();

  const organization = await organizationRepository.getByName(subdomain);

  if (!organization) throw badRequest('not allowed email');

  const otp = generateOTP();

  const user = new User(email, firstName, lastName, organization);

  user.setOtp(otp);

  await userRepository.insert(user);

  await sendOtpViaEmail(email, otp, firstName);

  return {
    statusCode: 201,
    body: {},
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(signUpSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
