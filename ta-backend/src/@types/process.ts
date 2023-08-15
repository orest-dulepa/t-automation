export enum PROCESS_TYPE {
  ROBOCORP = 'robocorp',
  AWS = 'AWS',
}

export interface IRobocorpCredential {
  server: string;
  apiWorkspace: string;
  apiProcessId: string;
  rcWskey: string;
}

export interface IAWSBotCredential {
  ARN: string;
}

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

export enum PROPERTY_TYPE {
  text = 'text',
  textarea = 'textarea',
  date = 'date',
  email = 'email',
  radio = 'radio',
  checkbox = 'checkbox',
  token = 'token'
}

export interface IProperty {
  name: string;
  api_name: string;
  type: PROPERTY_TYPE;
}

export interface IPropertyWithValue extends IProperty {
  value: string;
}
