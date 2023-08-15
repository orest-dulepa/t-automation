import jwt from 'jsonwebtoken';

import { TOKEN_TYPE } from '@/@types/auth';

export const createToken = (id: number) =>
  jwt.sign({ type: TOKEN_TYPE.ACCESS_TOKEN, id }, process.env.JWT_SECRET, { expiresIn: '1d' });

export const createRefreshToken = (id: number) =>
  jwt.sign({ type: TOKEN_TYPE.REFRESH_TOKEN, id }, process.env.JWT_SECRET, { expiresIn: '30d' });

export const verifyToken = (token: string) => jwt.verify(token, process.env.JWT_SECRET);
