import { MigrationInterface, QueryRunner } from 'typeorm';

export class RenameCompaniesToOrganizations1601479203131 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE companies RENAME TO organizations`);
    await queryRunner.query(`ALTER TABLE companies_to_processes RENAME TO organizations_to_processes`);
    await queryRunner.query(`ALTER TABLE organizations_to_processes RENAME COLUMN company_id TO organization_id`);
    await queryRunner.query(`ALTER TABLE users RENAME COLUMN company_id TO organization_id`);
    await queryRunner.query(`ALTER TABLE users_processes RENAME COLUMN company_id TO organization_id`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`ALTER TABLE users_processes RENAME COLUMN organization_id TO company_id`);
    await queryRunner.query(`ALTER TABLE users RENAME COLUMN organization_id TO company_id`);
    await queryRunner.query(`ALTER TABLE organizations_to_processes RENAME COLUMN organization_id TO company_id`);
    await queryRunner.query(`ALTER TABLE organizations_to_processes RENAME TO companies_to_processes`);
    await queryRunner.query(`ALTER TABLE organizations RENAME TO companies`);
  }
}
