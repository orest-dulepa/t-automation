import Joi from 'joi';
import { PROCESS_TYPE, IProperty } from '@/@types/process';
import { IProcessUpdateRequest } from './types';

const propertiesSchema = Joi.object<IProperty>({
  api_name: Joi.string().required(),
  name: Joi.string().required(),
  type: Joi.string().required(),
});

export const processUpdateSchema = Joi.object<IProcessUpdateRequest>({
  name: Joi.string(),
  type: Joi.string().valid(PROCESS_TYPE.ROBOCORP),
  // type: Joi.string().valid(PROCESS_TYPE.ROBOCORP, PROCESS_TYPE.UIPATH_BE1, PROCESS_TYPE.UIPATH_BE2),
  properties: Joi.array().items(propertiesSchema),
});
