-- Run after creating password protected waste_app and waste_dashboard roles.
-- Passwords belong in the runtime environment, not this repository.
GRANT CONNECT ON DATABASE waste_lab TO waste_app, waste_dashboard;
GRANT USAGE ON SCHEMA public TO waste_app, waste_dashboard;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO waste_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO waste_dashboard;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO waste_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO waste_dashboard;
