"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.jsonBodySerializer = void 0;
exports.jsonBodySerializer = () => {
    const serialize = (handler, next) => {
        const { body } = handler.response;
        handler.response.body = typeof body === 'string' ? body : JSON.stringify(body);
        next();
    };
    return {
        after: serialize,
    };
};
//# sourceMappingURL=json-body-serializer.js.map