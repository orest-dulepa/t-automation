"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PROPERTY_TYPE = exports.PROCESS_TYPE = void 0;
var PROCESS_TYPE;
(function (PROCESS_TYPE) {
    PROCESS_TYPE["ROBOCORP"] = "robocorp";
    PROCESS_TYPE["AWS"] = "AWS";
})(PROCESS_TYPE = exports.PROCESS_TYPE || (exports.PROCESS_TYPE = {}));
// interface IUIPathCredentialBase {
//   tenancyName: string;
//   usernameOrEmailAddress: string;
//   password: string;
// }
// export interface IUIPathCredentialBE1 extends IUIPathCredentialBase {
//   robotIds: number[];
//   release: string;
// }
//
// export interface IUIPathCredentialBE2 extends IUIPathCredentialBase {
//   botName: string;
// }
// export type IUIPathCredential = IUIPathCredentialBE1 | IUIPathCredentialBE2;
var PROPERTY_TYPE;
(function (PROPERTY_TYPE) {
    PROPERTY_TYPE["text"] = "text";
    PROPERTY_TYPE["textarea"] = "textarea";
    PROPERTY_TYPE["date"] = "date";
    PROPERTY_TYPE["email"] = "email";
    PROPERTY_TYPE["radio"] = "radio";
    PROPERTY_TYPE["checkbox"] = "checkbox";
    PROPERTY_TYPE["token"] = "token";
})(PROPERTY_TYPE = exports.PROPERTY_TYPE || (exports.PROPERTY_TYPE = {}));
//# sourceMappingURL=process.js.map