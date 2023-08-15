import { APIGatewayProxyWithLambdaAuthorizerHandler } from 'aws-lambda';
import AWS from 'aws-sdk';
import middy from 'middy';
import { jsonBodyParser, doNotWaitForEmptyEventLoop, cors } from 'middy/middlewares';

import { validator } from '@/middlewares/validator';
import { errorHandler } from '@/middlewares/error-handler';
import { jsonBodySerializer } from '@/middlewares/json-body-serializer';

import { IGetArtifactDownloadUrlRequest, IGetArtifactDownloadUrlResponse } from './types';
import { artifactDownloadUrlSchema } from './schema';

const s3 = new AWS.S3();

const rawHandler: APIGatewayProxyWithLambdaAuthorizerHandler<
  IGetArtifactDownloadUrlRequest,
  IGetArtifactDownloadUrlResponse
> = async (event) => {
  console.log('Event: ', event);

  const { body } = event;
  const { key } = body;

  let contentType = 'text/plain';
  if (key.endsWith('.png')) contentType = 'image/png';
  if (key.endsWith('.jpg') || key.endsWith('.jpeg')) contentType = 'image/jpg';
  if (key.endsWith('.bmp')) contentType = 'image/bmp';
  if (key.endsWith('.css')) contentType = 'text/css';
  if (key.endsWith('.csv')) contentType = 'text/csv';
  if (key.endsWith('.doc')) contentType = 'application/msword';
  if (key.endsWith('.docx')) contentType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
  if (key.endsWith('.gif')) contentType = 'image/gif';
  if (key.endsWith('.html')) contentType = 'text/html';
  if (key.endsWith('.js')) contentType = 'text/javascript';
  if (key.endsWith('.json')) contentType = 'application/json';
  if (key.endsWith('.mp3')) contentType = 'audio/mpeg';
  if (key.endsWith('.mp4')) contentType = 'video/mp4';
  if (key.endsWith('.pdf')) contentType = 'application/pdf';
  if (key.endsWith('.svg')) contentType = 'image/svg+xml';
  if (key.endsWith('.xls')) contentType = 'application/vnd.ms-excel';
  if (key.endsWith('.xlsx')) contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
  if (key.endsWith('.xml')) contentType = 'image/svg+xml';

  const url = s3.getSignedUrl('getObject', {
    Bucket: process.env.BUCKET_NAME,
    ResponseContentDisposition: 'inline',
    ResponseContentType: contentType,
    Key: key,
  });

  return {
    statusCode: 200,
    body: {
      url,
    },
  };
};

export const handler = middy(rawHandler)
  .use(doNotWaitForEmptyEventLoop())
  .use(jsonBodyParser())
  .use(validator(artifactDownloadUrlSchema))
  .use(errorHandler())
  .use(jsonBodySerializer())
  .use(cors());
