import { createActionCreators } from 'immer-reducer';

import { AvailableProcessesReducer } from '@/store/reducers/available-processes';

import { AsyncAction } from './common';

export const availableProcessesActions = createActionCreators(AvailableProcessesReducer);

export type AvailableProcessesActions =
  | ReturnType<typeof availableProcessesActions.setIsPending>
  | ReturnType<typeof availableProcessesActions.setProcesses>
  | ReturnType<typeof availableProcessesActions.setIsRejected>;

export const loadAvailableProcesses = (): AsyncAction => async (
  dispatch,
  _,
  { mainApiProtected },
) => {
  try {
    dispatch(availableProcessesActions.setIsPending());

    const processes = await mainApiProtected.getAvailableProcesses();

    dispatch(availableProcessesActions.setProcesses(processes));
  } catch (e) {
    dispatch(availableProcessesActions.setIsRejected());
  }
};
