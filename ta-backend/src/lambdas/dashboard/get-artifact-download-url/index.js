"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const aws_sdk_1 = __importDefault(require("aws-sdk"));
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const validator_1 = require("@/middlewares/validator");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const schema_1 = require("./schema");
const s3 = new aws_sdk_1.default.S3();
const rawHandler = async (event) => {
    console.log('Event: ', event);
    const { body } = event;
    const { key } = body;
    let contentType = 'text/plain';
    if (key.endsWith('.png'))
        contentType = 'image/png';
    if (key.endsWith('.jpg') || key.endsWith('.jpeg'))
        contentType = 'image/jpg';
    if (key.endsWith('.bmp'))
        contentType = 'image/bmp';
    if (key.endsWith('.css'))
        contentType = 'text/css';
    if (key.endsWith('.csv'))
        contentType = 'text/csv';
    if (key.endsWith('.doc'))
        contentType = 'application/msword';
    if (key.endsWith('.docx'))
        contentType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    if (key.endsWith('.gif'))
        contentType = 'image/gif';
    if (key.endsWith('.html'))
        contentType = 'text/html';
    if (key.endsWith('.js'))
        contentType = 'text/javascript';
    if (key.endsWith('.json'))
        contentType = 'application/json';
    if (key.endsWith('.mp3'))
        contentType = 'audio/mpeg';
    if (key.endsWith('.mp4'))
        contentType = 'video/mp4';
    if (key.endsWith('.pdf'))
        contentType = 'application/pdf';
    if (key.endsWith('.svg'))
        contentType = 'image/svg+xml';
    if (key.endsWith('.xls'))
        contentType = 'application/vnd.ms-excel';
    if (key.endsWith('.xlsx'))
        contentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    if (key.endsWith('.xml'))
        contentType = 'image/svg+xml';
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
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(middlewares_1.jsonBodyParser())
    .use(validator_1.validator(schema_1.artifactDownloadUrlSchema))
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map