/* eslint-disable import/prefer-default-export */
export const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));
