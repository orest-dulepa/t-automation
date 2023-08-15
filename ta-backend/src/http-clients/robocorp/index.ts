import {IRobocorpCredential, IPropertyWithValue, PROPERTY_TYPE} from '@/@types/process';

import { Process } from '@/entities/Process';

import { mapProperties } from '@/utils/map-properties';

import { createInstance } from '../create-instance';

import {
  IMonitorRobotArguments,
  IMonitorRobotResponse,
  IRobotArtifactsArguments,
  IRobotArtifactsResponse,
  IRobotDownloadArtifactArguments,
  IRobotDownloadEventsArguments,
  IRobotDownloadEventsResponse,
  IRobotDownloadLogsArguments,
  IRobotDownloadLogsResponse,
  IStartRobotV2Response,
  IDownloadArtifactArguments,
} from './types';
import axios from 'axios';
import {getCustomRepository} from "typeorm";
import {UserRepository} from "@/repositories/User";
import {createRefreshToken, createToken} from "@/utils/jwt";
import {createOrGetDBConnection} from "@/utils/db";
import {forbidden} from "@hapi/boom";


export const startRobocorp = async ({ credentials }: Process, body: IPropertyWithValue[]) => {
  const { server, apiProcessId, apiWorkspace, rcWskey } = credentials as IRobocorpCredential;

  await createOrGetDBConnection();

  const headers = {
    Authorization: `RC-WSKEY ${rcWskey}`,
  };

  const userRepository = getCustomRepository(UserRepository);

  const robotUser = await userRepository.getByEmailWithOrganizationAndRole('robocloud@ta.com');

  if (!robotUser) throw forbidden();

  const accessToken = createToken(robotUser.id);
  const refreshToken = createRefreshToken(robotUser.id);

  body.push(
      { name: 'Access Token', api_name: 'accessToken', value: accessToken, type: PROPERTY_TYPE.token },
      { name: 'Refresh Token', api_name: 'refreshToken', value: refreshToken, type: PROPERTY_TYPE.token }
  );

  const data = {
    variables: mapProperties(body),
  };

  const robocorpURL = createInstance(server + '/workspaces/');
  console.log('robocorpURL', robocorpURL);

  return robocorpURL.post<IStartRobotV2Response>(
    `/${apiWorkspace}/processes/${apiProcessId}/runs`,
    data,
    { headers },
  );
};

export const monitorRobocorp = ({
  server,
  apiWorkspace,
  apiProcessId,
  processRunId,
  rcWskey,
}: IMonitorRobotArguments) => {
  const headers = {
    Authorization: `RC-WSKEY ${rcWskey}`,
  };

  const robocorpURL = createInstance(server + '/workspaces/');
  console.log('robocorpURL', robocorpURL);

  return robocorpURL.get<IMonitorRobotResponse>(
    `/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}`,
    {
      headers,
      params: {
        embed: 'robotRuns',
      },
    },
  );
};

export const getRobocorpArtifacts = ({
  server,
  apiWorkspace,
  apiProcessId,
  processRunId,
  robotRunsId,
  rcWskey,
}: IRobotArtifactsArguments) => {
  const headers = {
    Authorization: `RC-WSKEY ${rcWskey}`,
  };

  const robocorpURL = createInstance(server + '/workspaces/');
  console.log('robocorpURL', robocorpURL);

  return robocorpURL.get<IRobotArtifactsResponse[]>(
    `/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}/robotRuns/${robotRunsId}/artifacts`,
    {
      headers,
    },
  );
};

export const downloadRobocorpArtifact = ({
  server,
  apiWorkspace,
  apiProcessId,
  processRunId,
  robotRunsId,
  artifactId,
  fileName,
  rcWskey,
}: IRobotDownloadArtifactArguments) => {
  const headers = {
    Authorization: `RC-WSKEY ${rcWskey}`,
  };

  const robocorpURL = createInstance(server + '/workspaces/');

  return robocorpURL.get<string>(
    `/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}/robotRuns/${robotRunsId}/artifacts/${artifactId}/${fileName}`,
    {
      headers
    },
  );
};

export const downloadArtifact = ({
  link,
}: IDownloadArtifactArguments) => {
  return axios.get(link, { responseType: 'arraybuffer' });
};

export const getRobocorpEvents = ({
  server,
  apiWorkspace,
  apiProcessId,
  processRunId,
  robotRunsId,
  rcWskey,
}: IRobotDownloadEventsArguments) => {
  const headers = {
    Authorization: `RC-WSKEY ${rcWskey}`,
  };

  const robocorpURL = createInstance(server + '/workspaces/');

  return robocorpURL.get<IRobotDownloadEventsResponse>(
    `/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}/robotRuns/${robotRunsId}/events`,
    {
      headers,
    },
  );
};

export const getRobocorpLogs = ({
  server,
  apiWorkspace,
  apiProcessId,
  processRunId,
  robotRunsId,
  rcWskey,
}: IRobotDownloadLogsArguments) => {
  const headers = {
    Authorization: `RC-WSKEY ${rcWskey}`,
  };

  const robocorpURL = createInstance(server + '/workspaces/');

  return robocorpURL.get<IRobotDownloadLogsResponse>(
    `/${apiWorkspace}/processes/${apiProcessId}/runs/${processRunId}/robotRuns/${robotRunsId}/messages`,
    {
      headers,
    },
  );
};

export const requestWithRetry = async ({
  func,
  args,
}: {
  func: typeof getRobocorpLogs;
  args: IRobotDownloadLogsArguments
}) => {
  try {
    return await func.call(func, args)
  } catch (e) {
    console.log(`Error, getting robo logs ${e}`)
  }

  return undefined;
}
