export enum TOKEN_TYPE {
  ACCESS_TOKEN,
  REFRESH_TOKEN,
}

export interface ITokenPayload {
  id: number;
  type: TOKEN_TYPE;
}
