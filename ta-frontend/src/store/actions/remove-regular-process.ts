import { createActionCreators } from 'immer-reducer';
import { RemoveRegularProcessReducer } from '@/store/reducers/remove-regular-process';
import { AsyncAction } from './common';

export const removeRegularProcessActions = createActionCreators(
  RemoveRegularProcessReducer,
);

export type RemoveRegularProcessActions =
  | ReturnType<typeof removeRegularProcessActions.setIsPending>
  | ReturnType<typeof removeRegularProcessActions.setIsRejected>
  | ReturnType<typeof removeRegularProcessActions.setProcessId>;

export const setRegularProcessIdAsync = (id: number): AsyncAction => (dispatch) => {
  try {
    dispatch(removeRegularProcessActions.setProcessId(id));
  } catch (e) {
    console.log(e);
  }
};

export const removeRegularProcessAsync = (): AsyncAction => async (
  dispatch, getState, { mainApiProtected },
) => {
  try {
    dispatch(removeRegularProcessActions.setIsPending());

    const { removeRegularProcessReducer } = getState();
    const { processId } = removeRegularProcessReducer;

    await mainApiProtected.removeRegularProcess(processId!);

    dispatch(removeRegularProcessActions.reset());
  } catch (e) {
    dispatch(removeRegularProcessActions.setIsRejected());
  }
};
