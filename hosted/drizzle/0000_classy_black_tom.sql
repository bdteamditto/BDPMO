CREATE TABLE `pmo_accounts` (
	`id` text PRIMARY KEY NOT NULL,
	`password` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `pmo_login_limits` (
	`id` text PRIMARY KEY NOT NULL,
	`count` integer NOT NULL,
	`expires` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `pmo_sessions` (
	`id` text PRIMARY KEY NOT NULL,
	`user` text NOT NULL,
	`csrf` text NOT NULL,
	`expires` integer NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_pmo_sessions_expires` ON `pmo_sessions` (`expires`);--> statement-breakpoint
CREATE TABLE `pmo_workspace` (
	`id` integer PRIMARY KEY NOT NULL,
	`revision` integer DEFAULT 0 NOT NULL,
	`data` text NOT NULL
);
