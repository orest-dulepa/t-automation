import Joi from 'joi';
import { IOrganizationUpdateRequest } from './types';

export const organizationUpdateSchema = Joi.object<IOrganizationUpdateRequest>({
  name: Joi.string(),
});
