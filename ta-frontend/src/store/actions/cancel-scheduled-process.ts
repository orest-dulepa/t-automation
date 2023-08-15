import { createActionCreators } from 'immer-reducer';

import { CancelScheduledProcessReducer } from '@/store/reducers/cancel-scheduled-process';

import { AsyncAction } from './common';

export const cancelScheduledProcessActions = createActionCreators(
  CancelScheduledProcessReducer,
);

export type CancelScheduledProcessActions =
  | ReturnType<typeof cancelScheduledProcessActions.setIsPending>
  | ReturnType<typeof cancelScheduledProcessActions.setIsRejected>
  | ReturnType<typeof cancelScheduledProcessActions.setProcessId>;

export const setScheduledProcessIdAsync = (id: number): AsyncAction => (dispatch) => {
  try {
    dispatch(cancelScheduledProcessActions.setProcessId(id));
  } catch (e) {
    console.log(e);
  }
};

export const cancelScheduledProcessAsync = (): AsyncAction => async (
  dispatch, getState, { mainApiProtected },
) => {
  try {
    dispatch(cancelScheduledProcessActions.setIsPending());

    const { cancelScheduledProcessReducer } = getState();
    const { processId } = cancelScheduledProcessReducer;

    await mainApiProtected.cancelScheduledProcess(processId!);

    dispatch(cancelScheduledProcessActions.reset());
  } catch (e) {
    dispatch(cancelScheduledProcessActions.setIsRejected());
  }
};
