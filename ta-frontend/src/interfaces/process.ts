export enum ProcessType {
  ROBOCORP = 'robocorp'
  // UIPATH_BE1 = 'uipath_be1',
  // UIPATH_BE2 = 'uipath_be2'
}

export enum PropertyType {
  TEXT = 'text',
  TEXTAREA = 'textarea',
  DATE = 'date',
  EMAIL = 'email',
  RADIO = 'radio',
  CHECKBOX = 'checkbox'
}

export enum PropertyDataDefaultValues {
  YESTERDAY = 'YESTERDAY',
  TODAY = 'TODAY',
  TOMORROW = 'TOMORROW'
}

export interface IProperty {
  name: string;
  api_name: string;
  mandatory: boolean;
  default: string;
  options: Array<string>;
  type: PropertyType;
}

export interface IPropertyWithValue extends IProperty {
  value: string;
}

export interface IProcess {
  id: number;
  name: string;
  type: ProcessType;
  properties: IProperty[];
}
