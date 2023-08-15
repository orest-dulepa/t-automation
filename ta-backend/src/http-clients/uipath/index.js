"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
//
// import {
//   IUIPathCredential,
//   IUIPathCredentialBE1,
//   IUIPathCredentialBE2,
//   IPropertyWithValue,
// } from '@/@types/process';
//
// import { mapProperties } from '@/utils/map-properties';
//
// import { createInstance } from '../create-instance';
//
// import {
//   IAuthUIPathResponse,
//   IStartBE2Response,
//   IMonitorBE2Arguments,
//   IMonitorBE2Response,
//   IGetReleasesResponse,
//   IGetRobotsResponse,
//   IStartBE1Arguments,
//   IStartBE1Response,
//   IMonitorBE1Response,
//   IGetLogsBE1Response,
//   IGetLogsBE2Response,
// } from './types';
//
// const instance = createInstance('https://orchestrator.ta.com/');
//
// export const authUIPath = ({ credentials }: Process) => {
//   const { tenancyName, usernameOrEmailAddress, password } = credentials as IUIPathCredential;
//
//   const data = {
//     tenancyName,
//     usernameOrEmailAddress,
//     password,
//   };
//
//   return instance.post<IAuthUIPathResponse>(`/api/Account/Authenticate`, data);
// };
//
// export const getReleases = (auth: string) => {
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 1,
//   };
//
//   return instance.get<IGetReleasesResponse>(`/odata/Releases`, { headers });
// };
//
// export const getRobots = (auth: string) => {
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 1,
//   };
//
//   return instance.get<IGetRobotsResponse>(`/odata/Robots`, { headers });
// };
//
// export const startBE1 = ({ credentials }: Process, { auth, body }: IStartBE1Arguments) => {
//   const { release, robotIds } = credentials as IUIPathCredentialBE1;
//
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 1,
//   };
//
//   const data = {
//     startInfo: {
//       ReleaseKey: release,
//       Strategy: 'Specific',
//       RobotIds: robotIds,
//       JobsCount: 0,
//       Source: 'Manual',
//       InputArguments: JSON.stringify(mapProperties(body)),
//     },
//   };
//
//   console.log(data);
//
//   return instance.post<IStartBE1Response>(
//     `/odata/Jobs/UiPath.Server.Configuration.OData.StartJobs`,
//     data,
//     { headers },
//   );
// };
//
// export const monitorBE1 = (auth: string, key: string) => {
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 1,
//   };
//
//   return instance.get<IMonitorBE1Response>(`/odata/Jobs`, {
//     headers,
//     params: {
//       $filter: `Key eq ${key}`,
//     },
//   });
// };
//
// export const getBE2Logs = (auth: string, key: string) => {
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 2,
//   };
//
//   return instance.get<IGetLogsBE2Response>(`/odata/RobotLogs`, {
//     headers,
//     params: {
//       $filter: `contains(RawMessage, '"Queue_Item_Id": "${key}"') eq true`,
//       $select: 'Message,TimeStamp'
//     },
//   });
// };
//
// export const getBE1Logs = (auth: string, key: string) => {
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 1,
//   };
//
//   return instance.get<IGetLogsBE1Response>(`/odata/RobotLogs`, {
//     headers,
//     params: {
//       $filter: `JobKey eq ${key}`,
//     },
//   });
// };
//
// export const startBE2 = ({ credentials }: Process, auth: string, body: IPropertyWithValue[]) => {
//   const { botName } = credentials as IUIPathCredentialBE2;
//
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 2,
//   };
//
//   const data = {
//     itemData: {
//       Name: botName,
//       Priority: 'Normal',
//       SpecificContent: mapProperties(body),
//     },
//   };
//
//   console.log(data);
//
//   return instance.post<IStartBE2Response>(`/odata/Queues/UiPathODataSvc.AddQueueItem`, data, {
//     headers,
//   });
// };
//
// export const monitorBE2 = ({ id, auth }: IMonitorBE2Arguments) => {
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 2,
//   };
//
//   return instance.get<IMonitorBE2Response>(`/odata/QueueItems`, {
//     headers,
//     params: {
//       $filter: `Id eq ${id}`,
//     },
//   });
// };
//
// export const monitorBE2ByAncestorId = ({ id, auth }: IMonitorBE2Arguments) => {
//   const headers = {
//     Authorization: `Bearer ${auth}`,
//     'X-UIPATH-TenantName': 'Default',
//     'X-UIPATH-OrganizationUnitId': 2,
//   };
//
//   return instance.get<IMonitorBE2Response>(`/odata/QueueItems`, {
//     headers,
//     params: {
//       $filter: `AncestorId eq ${id}`,
//     },
//   });
// };
//# sourceMappingURL=index.js.map