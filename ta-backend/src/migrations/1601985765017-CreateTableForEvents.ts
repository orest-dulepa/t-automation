import { MigrationInterface, QueryRunner } from 'typeorm';

export class CreateTableForEvents1601985765017 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(
      `CREATE TABLE IF NOT EXISTS events (
          id SERIAL PRIMARY KEY NOT NULL,
          seq_no text NOT NULL,
          time text NOT NULL,
          event_type text NOT NULL,
          user_process_id int NOT NULL,
          FOREIGN KEY (user_process_id) REFERENCES users_processes (id))`,
    );

    await queryRunner.query(`CREATE INDEX idx_user_process_id ON events (user_process_id)`);
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query('DROP INDEX IF EXISTS idx_user_process_id');

    await queryRunner.query('DROP TABLE IF EXISTS events');
  }
}
