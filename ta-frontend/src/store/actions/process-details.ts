import { createActionCreators } from 'immer-reducer';

import { ProcessStatus } from '@/interfaces/user-process';

import { sleep } from '@/utils/sleep';

import { ProcessDetailsReducer } from '@/store/reducers/process-details';

import { AsyncAction } from './common';

export const processDetailsActions = createActionCreators(ProcessDetailsReducer);

export type ProcessDetailsActions =
  | ReturnType<typeof processDetailsActions.setIsPending>
  | ReturnType<typeof processDetailsActions.setIsArtifactDownloading>
  | ReturnType<typeof processDetailsActions.setProcessDetails>
  | ReturnType<typeof processDetailsActions.setIsRejected>
  | ReturnType<typeof processDetailsActions.reset>;

export const loadProcessDetails = (id: string): AsyncAction => async (
  dispatch,
  _,
  { mainApiProtected },
) => {
  try {
    dispatch(processDetailsActions.setIsPending());

    const processDetails = await mainApiProtected.getProcessDetails(id);
    const { status } = processDetails;

    dispatch(processDetailsActions.setProcessDetails(processDetails));

    if (
      status !== ProcessStatus.FINISHED
      && status !== ProcessStatus.FAILED
      && status !== ProcessStatus.WARNING
    ) {
      dispatch(processMonitorRequest(id));
    }
  } catch (e) {
    const status = e?.response?.status;

    switch (status) {
      case 404: {
        const msg = "The process you were looking for wasn't found";
        dispatch(processDetailsActions.setIsRejected(msg));
        break;
      }
      case 403: {
        const msg = "You don't have enough permissions to see this process";
        dispatch(processDetailsActions.setIsRejected(msg));
        break;
      }
      default: {
        const msg = 'Something went wrong';
        dispatch(processDetailsActions.setIsRejected(msg));
      }
    }
  }
};

const processMonitorRequest = (id: string): AsyncAction => async (
  dispatch,
  getState,
  { mainApiProtected },
) => {
  try {
    const { router } = getState();
    const { pathname } = router.location;

    if (pathname !== `/processes/${id}`) return;

    const processDetails = await mainApiProtected.getProcessDetails(id);
    const { status } = processDetails;

    dispatch(processDetailsActions.setProcessDetails(processDetails));

    if (
      status === ProcessStatus.FINISHED
      || status === ProcessStatus.FAILED
      || status === ProcessStatus.WARNING
    ) {
      dispatch(loadProcessDetails(id));
      return;
    }

    await sleep(2500);

    dispatch(processMonitorRequest(id));
  } catch (e) {
    console.log(e);
  }
};

export const downloadArtifactAsync = (key: string): AsyncAction => async (
  dispatch,
  _2,
  { mainApiProtected },
) => {
  try {
    dispatch(processDetailsActions.setIsArtifactDownloading(true));

    const { url } = await mainApiProtected.getDownloadUrl({ key });

    const a = document.createElement('a');
    a.href = url;
    a.target = '_blank';
    a.click();
    a.remove();
  } catch (e) {
    console.log(e);
  } finally {
    dispatch(processDetailsActions.setIsArtifactDownloading(false));
  }
};
