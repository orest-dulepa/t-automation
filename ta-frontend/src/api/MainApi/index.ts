import HttpClient from '../HttpClient';
import {
  ISignInBody,
  ISignUpBody,
  IVerifyBody,
  IVerifyResponse,
} from './types';

class MainApi extends HttpClient {
  private static instanceCached: MainApi;

  private constructor() {
    super(process.env.BASE_URL);
  }

  static getInstance = () => {
    if (!MainApi.instanceCached) {
      MainApi.instanceCached = new MainApi();
    }

    return MainApi.instanceCached;
  };

  public signIn = (body: ISignInBody) => this.instance.post('/sign-in', body);

  public signUp = (body: ISignUpBody) => this.instance.post('/sign-up', body);

  public verify = (body: IVerifyBody) => this.instance.post<IVerifyResponse>('/verify', body);
}

export default MainApi;
