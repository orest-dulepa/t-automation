import Joi from 'joi';
import { IProcessLinkRequest } from './types';

export const processLinkSchema = Joi.object<IProcessLinkRequest>({
  organizationId: Joi.number().required(),
  processId: Joi.number().required(),
});
