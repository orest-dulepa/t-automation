import Joi from 'joi';
import {
  PROCESS_TYPE,
  IRobocorpCredential,
  // IUIPathCredentialBE1,
  // IUIPathCredentialBE2,
  IProperty,
} from '@/@types/process';
import { IProcessCreateRequest } from './types';

const robocorpCredentialSchema = Joi.object<IRobocorpCredential>({
  server: Joi.string().required(),
  apiProcessId: Joi.string().required(),
  apiWorkspace: Joi.string().required(),
  rcWskey: Joi.string().required(),
});

// const uiPathCredentialBE1Schema = Joi.object<IUIPathCredentialBE1>({
//   tenancyName: Joi.string().required(),
//   usernameOrEmailAddress: Joi.string().required(),
//   password: Joi.string().required(),
//   robotIds: Joi.array().items(Joi.number()).required(),
//   release: Joi.string().required(),
// });

// const uiPathCredentialBE2Schema = Joi.object<IUIPathCredentialBE2>({
//   tenancyName: Joi.string().required(),
//   usernameOrEmailAddress: Joi.string().required(),
//   password: Joi.string().required(),
//   botName: Joi.string().required(),
// });

const propertiesSchema = Joi.object<IProperty>({
  api_name: Joi.string().required(),
  name: Joi.string().required(),
  type: Joi.string().required(),
});

export const processCreateSchema = Joi.object<IProcessCreateRequest>({
  name: Joi.string().required(),
  type: Joi.string()
    // .valid(PROCESS_TYPE.ROBOCORP, PROCESS_TYPE.UIPATH_BE1, PROCESS_TYPE.UIPATH_BE2)
    .valid(PROCESS_TYPE.ROBOCORP)
    .required(),
  credentials: Joi.alternatives().try(
    robocorpCredentialSchema,
    // uiPathCredentialBE1Schema,
    // uiPathCredentialBE2Schema,
  ),
  properties: Joi.array().items(propertiesSchema).required(),
});
