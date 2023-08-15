"use strict";
require("reflect-metadata");
const _1599144883159_Company_1 = require("./src/migrations/1599144883159-Company");
const _1599204666261_User_1 = require("./src/migrations/1599204666261-User");
const _1599204739981_Process_1 = require("./src/migrations/1599204739981-Process");
const _1599205100277_CompaniesToProcesses_1 = require("./src/migrations/1599205100277-CompaniesToProcesses");
const _1599205172957_UsersProcesses_1 = require("./src/migrations/1599205172957-UsersProcesses");
const _1601027086378_AddProcessTypes_1 = require("./src/migrations/1601027086378-AddProcessTypes");
const _1601380388193_DropUsersProcessesLogsAndEventsColumns_1 = require("./src/migrations/1601380388193-DropUsersProcessesLogsAndEventsColumns");
const _1601387759163_ChangeProcessesPropertiesColumnType_1 = require("./src/migrations/1601387759163-ChangeProcessesPropertiesColumnType");
const _1601479203131_RenameCompaniesToOrganizations_1 = require("./src/migrations/1601479203131-RenameCompaniesToOrganizations");
const _1601985765017_CreateTableForEvents_1 = require("./src/migrations/1601985765017-CreateTableForEvents");
const _1603891655852_AddLogs_1 = require("./src/migrations/1603891655852-AddLogs");
const _1603970302488_AddColumnMetaToUserProcesses_1 = require("./src/migrations/1603970302488-AddColumnMetaToUserProcesses");
const _1605868111155_AddNewProcessStatus_1 = require("./src/migrations/1605868111155-AddNewProcessStatus");
const _1606125514727_UpdateStartTimeColumnInUsersProcesses_1 = require("./src/migrations/1606125514727-UpdateStartTimeColumnInUsersProcesses");
const _1606156394891_AddCreatedTimeToUserProcess_1 = require("./src/migrations/1606156394891-AddCreatedTimeToUserProcess");
const _1608894674640_Role_1 = require("./src/migrations/1608894674640-Role");
const _1608896007321_AddRoleIdToUser_1 = require("./src/migrations/1608896007321-AddRoleIdToUser");
const _1609844504515_AddGlobalAdminRole_1 = require("./src/migrations/1609844504515-AddGlobalAdminRole");
const _1612868410793_AddRobocorpRunId_1 = require("./src/migrations/1612868410793-AddRobocorpRunId");
const _1613378282066_ScheduledProcesses_1 = require("./src/migrations/1613378282066-ScheduledProcesses");
const _1613381163303_AddColumnsToScheduledProcess_1 = require("./src/migrations/1613381163303-AddColumnsToScheduledProcess");
const _1613381845385_AddScheduledProcessStatus_1 = require("./src/migrations/1613381845385-AddScheduledProcessStatus");
const OrganizationsToProcesses_1 = require("./src/entities/OrganizationsToProcesses");
const Organization_1 = require("./src/entities/Organization");
const Process_1 = require("./src/entities/Process");
const User_1 = require("./src/entities/User");
const UsersProcesses_1 = require("./src/entities/UsersProcesses");
const Event_1 = require("./src/entities/Event");
const Log_1 = require("./src/entities/Log");
const Role_1 = require("./src/entities/Role");
const ScheduledProcess_1 = require("./src/entities/ScheduledProcess");
const _1613392106487_ChangeScheduledProcessColumnType_1 = require("./src/migrations/1613392106487-ChangeScheduledProcessColumnType");
const _1613395374626_ChangeScheduledProcessColumnType2_1 = require("./src/migrations/1613395374626-ChangeScheduledProcessColumnType2");
const _1621378282066_RegularProcesses_1 = require("./src/migrations/1621378282066-RegularProcesses");
const RegularProcess_1 = require("./src/entities/RegularProcess");
const config = {
    type: 'postgres',
    host: process.env.DB_HOST,
    port: Number(process.env.DB_PORT),
    database: process.env.DB_NAME,
    username: process.env.DB_USER,
    password: process.env.DB_PWD,
    logging: true,
    entities: [
        OrganizationsToProcesses_1.OrganizationsToProcesses,
        Organization_1.Organization,
        Process_1.Process,
        RegularProcess_1.RegularProcess,
        User_1.User,
        UsersProcesses_1.UsersProcesses,
        Event_1.Event,
        Log_1.Log,
        Role_1.Role,
        ScheduledProcess_1.ScheduledProcess,
    ],
    migrations: [
        _1599144883159_Company_1.Company1599144883159,
        _1599204666261_User_1.User1599204666261,
        _1599204739981_Process_1.Process1599204739981,
        _1599205100277_CompaniesToProcesses_1.CompaniesToProcesses1599205100277,
        _1599205172957_UsersProcesses_1.UsersProcesses1599205172957,
        _1601027086378_AddProcessTypes_1.AddProcessTypes1601027086378,
        _1601380388193_DropUsersProcessesLogsAndEventsColumns_1.DropUsersProccesLogsAndEventsColumns1601380388193,
        _1601387759163_ChangeProcessesPropertiesColumnType_1.ChangeProcessesPropertiesColumnType1601387759163,
        _1601479203131_RenameCompaniesToOrganizations_1.RenameCompaniesToOrganizations1601479203131,
        _1601985765017_CreateTableForEvents_1.CreateTableForEvents1601985765017,
        _1603891655852_AddLogs_1.AddLogs1603891655852,
        _1603970302488_AddColumnMetaToUserProcesses_1.AddColumnMetaToUserProcesses1603970302488,
        _1605868111155_AddNewProcessStatus_1.AddNewProcessStatus1605868111155,
        _1606125514727_UpdateStartTimeColumnInUsersProcesses_1.UpdateStartTimeColumnInUsersProcesses1606125514727,
        _1606156394891_AddCreatedTimeToUserProcess_1.AddCreatedTimeToUserProcess1606156394891,
        _1608894674640_Role_1.Role1608894674640,
        _1608896007321_AddRoleIdToUser_1.AddRoleIdToUser1608896007321,
        _1609844504515_AddGlobalAdminRole_1.AddGlobalAdminRole1609844504515,
        _1612868410793_AddRobocorpRunId_1.AddRobocorpRunId1612868410793,
        _1613378282066_ScheduledProcesses_1.ScheduledProcesses1613378282066,
        _1613381163303_AddColumnsToScheduledProcess_1.AddColumnsToScheduledProcess1613381163303,
        _1613381845385_AddScheduledProcessStatus_1.AddScheduledProcessStatus1613381845385,
        _1613392106487_ChangeScheduledProcessColumnType_1.ChangeScheduledProcessColumnType1613392106487,
        _1613395374626_ChangeScheduledProcessColumnType2_1.ChangeScheduledProcessColumnType21613395374626,
        _1621378282066_RegularProcesses_1.RegularProcesses1621378282066,
    ],
    cli: {
        migrationsDir: 'src/migrations',
    },
};
module.exports = config;
//# sourceMappingURL=ormconfig.js.map