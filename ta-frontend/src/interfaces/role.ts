export enum ROLE {
  EMPLOYEE = 1,
  MANAGER,
  ADMIN
}

export interface IRole {
  id: ROLE;
  name: string;
}
