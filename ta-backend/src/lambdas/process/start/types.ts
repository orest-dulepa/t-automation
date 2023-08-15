import { IPropertyWithValue } from '@/@types/process';

export type IProcessStartEvent = {
  processId: string;
  userId: string;
  meta: IPropertyWithValue[];
  dataForBot: IPropertyWithValue[];
  changeStatusUrl: string;
};
