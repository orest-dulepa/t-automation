import Joi from 'joi';
import { IOrganizationCreateRequest } from './types';

export const organizationCreateSchema = Joi.object<IOrganizationCreateRequest>({
  name: Joi.string().required(),
});
