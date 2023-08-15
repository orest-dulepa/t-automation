import LocalStorage from './LocalStorage';

enum Locals {
  ACCESS_TOKEN = 'access_token',
  REFRESH_TOKEN = 'refresh_token'
}

class TokensLocalStorage extends LocalStorage<Locals> {
  private static instance?: TokensLocalStorage;

  private constructor() {
    super();
  }

  public static getInstance() {
    if (!TokensLocalStorage.instance) {
      TokensLocalStorage.instance = new TokensLocalStorage();
    }

    return TokensLocalStorage.instance;
  }

  public getAccessToken() {
    return this.get(Locals.ACCESS_TOKEN);
  }

  public setAccessToken(accessToken: string) {
    this.set(Locals.ACCESS_TOKEN, accessToken);
  }

  public getRefreshToken() {
    return this.get(Locals.REFRESH_TOKEN);
  }

  public setRefreshToken(refreshToken: string) {
    this.set(Locals.REFRESH_TOKEN, refreshToken);
  }

  public clear() {
    this.clearItems([Locals.ACCESS_TOKEN, Locals.REFRESH_TOKEN]);
  }
}

export default TokensLocalStorage;
