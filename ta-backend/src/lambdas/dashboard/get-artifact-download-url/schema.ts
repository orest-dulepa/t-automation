import Joi from 'joi';
import { IGetArtifactDownloadUrlRequest } from './types';

export const artifactDownloadUrlSchema = Joi.object<IGetArtifactDownloadUrlRequest>({
  key: Joi.string().required(),
});
