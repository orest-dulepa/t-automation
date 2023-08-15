import { IPropertyWithValue } from '@/@types/process';

export const mapProperties = (properties: IPropertyWithValue[]) =>
  properties.reduce((a, { api_name, value }) => {
    return {
      ...a,
      [api_name]: value,
    };
  }, {});
