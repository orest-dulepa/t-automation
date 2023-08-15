import 'reflect-metadata';
import { PostgresConnectionOptions } from 'typeorm/driver/postgres/PostgresConnectionOptions';

import { Company1599144883159 } from './src/migrations/1599144883159-Company';
import { User1599204666261 } from './src/migrations/1599204666261-User';
import { Process1599204739981 } from './src/migrations/1599204739981-Process';
import { CompaniesToProcesses1599205100277 } from './src/migrations/1599205100277-CompaniesToProcesses';
import { UsersProcesses1599205172957 } from './src/migrations/1599205172957-UsersProcesses';
import { AddProcessTypes1601027086378 } from './src/migrations/1601027086378-AddProcessTypes';
import { DropUsersProccesLogsAndEventsColumns1601380388193 } from './src/migrations/1601380388193-DropUsersProcessesLogsAndEventsColumns';
import { ChangeProcessesPropertiesColumnType1601387759163 } from './src/migrations/1601387759163-ChangeProcessesPropertiesColumnType';
import { RenameCompaniesToOrganizations1601479203131 } from './src/migrations/1601479203131-RenameCompaniesToOrganizations';
import { CreateTableForEvents1601985765017 } from './src/migrations/1601985765017-CreateTableForEvents';
import { AddLogs1603891655852 } from './src/migrations/1603891655852-AddLogs';
import { AddColumnMetaToUserProcesses1603970302488 } from './src/migrations/1603970302488-AddColumnMetaToUserProcesses';
import { AddNewProcessStatus1605868111155 } from './src/migrations/1605868111155-AddNewProcessStatus';
import { UpdateStartTimeColumnInUsersProcesses1606125514727 } from './src/migrations/1606125514727-UpdateStartTimeColumnInUsersProcesses';
import { AddCreatedTimeToUserProcess1606156394891 } from './src/migrations/1606156394891-AddCreatedTimeToUserProcess';
import { Role1608894674640 } from './src/migrations/1608894674640-Role';
import { AddRoleIdToUser1608896007321 } from './src/migrations/1608896007321-AddRoleIdToUser';
import { AddGlobalAdminRole1609844504515 } from './src/migrations/1609844504515-AddGlobalAdminRole';
import { AddRobocorpRunId1612868410793 } from './src/migrations/1612868410793-AddRobocorpRunId';
import { ScheduledProcesses1613378282066 } from './src/migrations/1613378282066-ScheduledProcesses';
import { AddColumnsToScheduledProcess1613381163303 } from './src/migrations/1613381163303-AddColumnsToScheduledProcess';
import { AddScheduledProcessStatus1613381845385 } from './src/migrations/1613381845385-AddScheduledProcessStatus';

import { OrganizationsToProcesses } from './src/entities/OrganizationsToProcesses';
import { Organization } from './src/entities/Organization';
import { Process } from './src/entities/Process';
import { User } from './src/entities/User';
import { UsersProcesses } from './src/entities/UsersProcesses';
import { Event } from './src/entities/Event';
import { Log } from './src/entities/Log';
import { Role } from './src/entities/Role';
import { ScheduledProcess } from './src/entities/ScheduledProcess';
import { ChangeScheduledProcessColumnType1613392106487 } from './src/migrations/1613392106487-ChangeScheduledProcessColumnType';
import { ChangeScheduledProcessColumnType21613395374626 } from './src/migrations/1613395374626-ChangeScheduledProcessColumnType2';
import { RegularProcesses1621378282066 } from './src/migrations/1621378282066-RegularProcesses';
import { RegularProcess } from './src/entities/RegularProcess';


const config: PostgresConnectionOptions = {
  type: 'postgres',
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT),
  database: process.env.DB_NAME,
  username: process.env.DB_USER,
  password: process.env.DB_PWD,
  logging: true,
  entities: [
    OrganizationsToProcesses,
    Organization,
    Process,
    RegularProcess,
    User,
    UsersProcesses,
    Event,
    Log,
    Role,
    ScheduledProcess,
  ],
  migrations: [
    Company1599144883159,
    User1599204666261,
    Process1599204739981,
    CompaniesToProcesses1599205100277,
    UsersProcesses1599205172957,
    AddProcessTypes1601027086378,
    DropUsersProccesLogsAndEventsColumns1601380388193,
    ChangeProcessesPropertiesColumnType1601387759163,
    RenameCompaniesToOrganizations1601479203131,
    CreateTableForEvents1601985765017,
    AddLogs1603891655852,
    AddColumnMetaToUserProcesses1603970302488,
    AddNewProcessStatus1605868111155,
    UpdateStartTimeColumnInUsersProcesses1606125514727,
    AddCreatedTimeToUserProcess1606156394891,
    Role1608894674640,
    AddRoleIdToUser1608896007321,
    AddGlobalAdminRole1609844504515,
    AddRobocorpRunId1612868410793,
    ScheduledProcesses1613378282066,
    AddColumnsToScheduledProcess1613381163303,
    AddScheduledProcessStatus1613381845385,
    ChangeScheduledProcessColumnType1613392106487,
    ChangeScheduledProcessColumnType21613395374626,
    RegularProcesses1621378282066,
  ],
  cli: {
    migrationsDir: 'src/migrations',
  },
};

export = config;
