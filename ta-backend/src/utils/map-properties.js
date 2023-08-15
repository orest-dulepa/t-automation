"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.mapProperties = void 0;
exports.mapProperties = (properties) => properties.reduce((a, { api_name, value }) => {
    return {
        ...a,
        [api_name]: value,
    };
}, {});
//# sourceMappingURL=map-properties.js.map