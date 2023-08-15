import HttpClientProtected from '../HttpClientProtected';
import {
  IGetMeResponse,
  IGetAvailableProcessResponse,
  IScheduleProcessBody,
  IGetScheduledProcessesResponse,
  IStartProcessBody,
  IStartProcessResponse,
  IGetActiveProcessesResponse,
  IGetFinishedProcessesQueries,
  IGetFinishedProcessesResponse,
  IGetFinishedProcessesFiltersResponse,
  IGetUserProcessResponse,
  IDownloadUrlBody,
  IDownloadUrlResponse,
  IEmptyResponse,
  ICreateRegularProcessRequest, IGetRegularProcessesResponse,
} from './types';

class MainApiProtected extends HttpClientProtected {
  private static instanceCached: MainApiProtected;

  private constructor() {
    super(process.env.BASE_URL);
  }

  static getInstance = () => {
    if (!MainApiProtected.instanceCached) {
      MainApiProtected.instanceCached = new MainApiProtected();
    }

    return MainApiProtected.instanceCached;
  };

  public getMe = () => this.instance.get<IGetMeResponse>('/me');

  public getAvailableProcesses = () => (
    this.instance.get<IGetAvailableProcessResponse>('/available-processes'));

  public scheduleProcess = (processId: number, body?: IScheduleProcessBody) => (
    this.instance.post<IEmptyResponse>(`/processes/schedule/${processId}`, body));

  public getScheduledProcesses = () => (
    this.instance.get<IGetScheduledProcessesResponse>('/scheduled-processes'));

  public cancelScheduledProcess = (idScheduledProcess: number) => (
    this.instance.post<IEmptyResponse>(`/scheduled-processes/cancel/${idScheduledProcess}`)
  );

  public createRegularProcess = (body: ICreateRegularProcessRequest) => (
    this.instance.post<IStartProcessResponse>('/processes/regular', body));

  public getRegularProcesses = () => (
    this.instance.get<IGetRegularProcessesResponse>('/processes/regular'));

  public removeRegularProcess = (idRegularProcess: number) => (
    this.instance.delete<IEmptyResponse>(`/processes/regular/${idRegularProcess}`)
  );

  public startProcess = (id: number, body?: IStartProcessBody) => (
    this.instance.post<IStartProcessResponse>(`/processes/start/${id}`, body));

  public getActiveProcesses = () => (
    this.instance.get<IGetActiveProcessesResponse>('/active-processes'));

  public getFinishedProcesses = (params: IGetFinishedProcessesQueries) => (
    this.instance.get<IGetFinishedProcessesResponse>('/finished-processes', { params }));

  public getFinishedProcessesFilters = () => (
    this.instance.get<IGetFinishedProcessesFiltersResponse>('/finished-processes/filters'));

  public getProcessDetails = (id: string) => (
    this.instance.get<IGetUserProcessResponse>(`/user-processes/${id}`));

  public getDownloadUrl = (body: IDownloadUrlBody) => (
    this.instance.post<IDownloadUrlResponse>('/user-processes/download-artifact', body));
}

export default MainApiProtected;
