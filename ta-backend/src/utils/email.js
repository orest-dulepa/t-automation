"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.sendOtpViaEmail = void 0;
const aws_sdk_1 = __importDefault(require("aws-sdk"));
const ses = new aws_sdk_1.default.SES();
exports.sendOtpViaEmail = (email, otp, firstName) => {
    const params = {
        Destination: {
            ToAddresses: [email],
        },
        Message: {
            Body: {
                Html: {
                    Charset: 'UTF-8',
                    Data: `
          <div style="background-color: #e6e6e6; margin-top: 20px; margin-right: 10px; margin-bottom: 20px;">
            <table style="margin: 0px auto;" cellpadding="25">
              <tbody>
                <tr>
                  <td>
                    <table style="background: #fff; border: 1px solid #a8adad; width: 584px; border-top: none; color: #4d4b48; font-family: Arial, Helvetica, sans-serif; font-size: 13px; line-height: 18px; box-shadow: 0px 2px 2px #A8ADAD;" cellpadding="24">
                      <tbody>
                        <tr>
                          <td>
                            <p style="margin-top: 0; margin-bottom: 20px;">Hi&nbsp;${firstName},</p>
                            <p style="margin-top: 0; margin-bottom: 10px;">Your One Time Password for TA&nbsp;is: <b>${otp}</b></p>
                            <p style="margin-top: 0; margin-bottom: 10px;">Please use this Password to complete your sign-in. Do not share this Password with anyone.</p>
                            <p style="margin-top: 0; margin-bottom: 15px;">Thank you,<br />TA</p>
                            <p style="margin-top: 0; margin-bottom: 0px; font-size: 11px;">Disclaimer: This email and any files transmitted with it are confidential and intended solely for the use of the individual or entity to whom they are addressed.</p>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          `,
                },
            },
            Subject: {
                Charset: 'UTF-8',
                Data: 'TA One time password',
            },
        },
        Source: 'otp@ta.com',
        ReplyToAddresses: [email],
    };
    return ses.sendEmail(params).promise();
};
//# sourceMappingURL=email.js.map