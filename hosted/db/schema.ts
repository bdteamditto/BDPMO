import { sqliteTable, text, integer, index } from 'drizzle-orm/sqlite-core';
export const workspace = sqliteTable('pmo_workspace', {id: integer('id').primaryKey(), revision: integer('revision').notNull().default(0), data: text('data').notNull()});
export const accounts = sqliteTable('pmo_accounts',{id:text('id').primaryKey(),password:text('password').notNull()});
export const sessions = sqliteTable('pmo_sessions',{id:text('id').primaryKey(),user:text('user').notNull(),csrf:text('csrf').notNull(),expires:integer('expires').notNull()},t=>[index('idx_pmo_sessions_expires').on(t.expires)]);
export const limits = sqliteTable('pmo_login_limits',{id:text('id').primaryKey(),count:integer('count').notNull(),expires:integer('expires').notNull()});
