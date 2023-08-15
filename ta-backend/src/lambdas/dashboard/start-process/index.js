"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = void 0;
const aws_sdk_1 = __importDefault(require("aws-sdk"));
const middy_1 = __importDefault(require("middy"));
const middlewares_1 = require("middy/middlewares");
const error_handler_1 = require("@/middlewares/error-handler");
const json_body_serializer_1 = require("@/middlewares/json-body-serializer");
const auth_parser_1 = require("@/middlewares/auth-parser");
const process_1 = require("@/@types/process");
const lambda = new aws_sdk_1.default.Lambda();
const rawHandler = async (event) => {
    console.log('Event: ', event);
    const { body, pathParameters, requestContext } = event;
    const { id } = pathParameters;
    const { authorizer: user } = requestContext;
    const changeStatusUrl = `https://${event.requestContext.domainName}/${event.requestContext.stage}/processes/change-status`;
    const dataForBot = [
        { name: 'Change Status Url', api_name: 'changeStatusUrl', value: changeStatusUrl, type: process_1.PROPERTY_TYPE.text },
    ];
    const lambdaParams = {
        FunctionName: process.env.START_PROCESS_LAMBDA_ARN,
        InvocationType: 'RequestResponse',
        Payload: JSON.stringify({
            processId: id,
            userId: user.id,
            meta: body || [],
            dataForBot: dataForBot || [],
            changeStatusUrl,
        }),
    };
    await lambda
        .invoke(lambdaParams)
        .promise()
        .catch((e) => console.log(e));
    return {
        statusCode: 201,
        body: {},
    };
};
exports.handler = middy_1.default(rawHandler)
    .use(middlewares_1.doNotWaitForEmptyEventLoop())
    .use(auth_parser_1.authParser())
    .use(middlewares_1.jsonBodyParser())
    .use(error_handler_1.errorHandler())
    .use(json_body_serializer_1.jsonBodySerializer())
    .use(middlewares_1.cors());
//# sourceMappingURL=index.js.map