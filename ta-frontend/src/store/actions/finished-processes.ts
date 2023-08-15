import { createActionCreators } from 'immer-reducer';

import { FinishedProcessesReducer } from '@/store/reducers/finished-processes';

import { AsyncAction } from './common';

export const finishedProcessesActions = createActionCreators(FinishedProcessesReducer);

export type FinishedProcessesActions =
  | ReturnType<typeof finishedProcessesActions.setIsPending>
  | ReturnType<typeof finishedProcessesActions.setProcesses>
  | ReturnType<typeof finishedProcessesActions.setIsMinorPending>
  | ReturnType<typeof finishedProcessesActions.setIsRejected>;

export const loadFinishedProcesses = (): AsyncAction => async (
  dispatch,
  getState,
  { mainApiProtected },
) => {
  try {
    dispatch(finishedProcessesActions.setIsPending());

    const { filtersReducer } = getState();
    const { queries } = filtersReducer;

    const { processes, total } = await mainApiProtected.getFinishedProcesses(queries);

    dispatch(finishedProcessesActions.setProcesses(processes, total));
  } catch (e) {
    dispatch(finishedProcessesActions.setIsRejected());
  }
};

export const loadFinishedProcessesViaFilters = (): AsyncAction => async (
  dispatch,
  getState,
  { mainApiProtected },
) => {
  try {
    dispatch(finishedProcessesActions.setIsMinorPending(true));

    const { filtersReducer } = getState();
    const { queries } = filtersReducer;

    const { processes, total } = await mainApiProtected.getFinishedProcesses(queries);

    dispatch(finishedProcessesActions.setProcesses(processes, total));
  } catch (e) {
    dispatch(finishedProcessesActions.setIsRejected());
  } finally {
    dispatch(finishedProcessesActions.setIsMinorPending(false));
  }
};
