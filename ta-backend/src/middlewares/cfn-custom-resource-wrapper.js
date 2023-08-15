"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const axios_1 = __importDefault(require("axios"));
const sleep_1 = require("@/utils/sleep");
function isCFNEvent(event) {
    return 'LogicalResourceId' in event;
}
async function sendResponse({ event, context, response, }) {
    const payload = {
        Status: response.status,
        Reason: response.reason,
        PhysicalResourceId: context.logGroupName || event.LogicalResourceId,
        LogicalResourceId: event.LogicalResourceId,
        StackId: event.StackId,
        RequestId: event.RequestId,
        Data: response.data,
    };
    console.log(`Payload: ${JSON.stringify(payload, undefined, 2)}`);
    console.log(`PUTting payload to ${event.ResponseURL}`);
    for (let i = 0; i < 5; i++) {
        try {
            await axios_1.default.put(event.ResponseURL, JSON.stringify(payload));
            return;
        }
        catch (e) {
            console.log('ERROR PUT', e);
            if (i < 4) {
                await sleep_1.sleep(1000);
            }
        }
    }
}
function cfnCustomResourceWrapper() {
    return {
        after: async (handler) => {
            if (isCFNEvent(handler.event)) {
                await sendResponse({
                    event: handler.event,
                    response: handler.response,
                    context: handler.context,
                });
            }
        },
        onError: async (handler) => {
            console.error('onError:', handler.error);
            if (isCFNEvent(handler.event)) {
                await sendResponse({
                    event: handler.event,
                    response: {
                        status: 'FAILED',
                        reason: handler.error.message,
                    },
                    context: handler.context,
                });
            }
        },
    };
}
exports.default = cfnCustomResourceWrapper;
//# sourceMappingURL=cfn-custom-resource-wrapper.js.map