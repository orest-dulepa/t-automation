import { createActionCreators } from 'immer-reducer';
import xor from 'lodash/xor';

import { IUserProcess } from '@/interfaces/user-process';

import { sleep } from '@/utils/sleep';

import { ActiveProcessesReducer } from '@/store/reducers/active-processes';

import { AsyncAction } from './common';
import { loadFinishedProcesses } from './finished-processes';

export const activeProcessesActions = createActionCreators(ActiveProcessesReducer);

export type ActiveProcessesActions =
  | ReturnType<typeof activeProcessesActions.setIsPending>
  | ReturnType<typeof activeProcessesActions.setProcesses>
  | ReturnType<typeof activeProcessesActions.setIsRejected>;

export const loadActiveProcesses = (): AsyncAction => async (dispatch, _, { mainApiProtected }) => {
  try {
    dispatch(activeProcessesActions.setIsPending());

    const processes = await mainApiProtected.getActiveProcesses();

    dispatch(activeProcessesActions.setProcesses(processes));

    if (processes.length) {
      dispatch(processesMonitor());
    }
  } catch (e) {
    dispatch(activeProcessesActions.setIsRejected());
  }
};

const processesMonitor = (): AsyncAction => async (dispatch, getState, { mainApiProtected }) => {
  try {
    const { router, activeProcessesReducer } = getState();
    const { pathname } = router.location;

    if (pathname !== '/processes') return;

    const processesFromRequest = await mainApiProtected.getActiveProcesses();

    const { processes: processesFromStore } = activeProcessesReducer;

    const getRunId = ({ processRunId }: IUserProcess) => processRunId;

    const processesRunIdFromRequest = processesFromRequest.map(getRunId);
    const processesRunIdFromStore = processesFromStore.map(getRunId);

    const difference = xor(processesRunIdFromRequest, processesRunIdFromStore);

    await sleep(2500);

    dispatch(activeProcessesActions.setProcesses(processesFromRequest));

    if (difference.length) {
      dispatch(loadActiveProcesses());
      dispatch(loadFinishedProcesses());
      return;
    }

    dispatch(processesMonitor());
  } catch (e) {
    console.log(e);
  }
};
