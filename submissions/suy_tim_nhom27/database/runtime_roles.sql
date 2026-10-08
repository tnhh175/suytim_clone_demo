-- Runs after schema, seed, portal grants, and result-integrity migration on a fresh demo DB.
-- POSTGRES_USER is a bootstrap superuser; the Gateway connects only as hf_demo_runtime.
\getenv runtime_password HF_RUNTIME_PASSWORD

CREATE ROLE hf_demo_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE ROLE hf_demo_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT PASSWORD :'runtime_password';

REASSIGN OWNED BY hf_demo TO hf_demo_owner;
ALTER SCHEMA public OWNER TO hf_demo_owner;
ALTER DATABASE hf_demo OWNER TO hf_demo_owner;

GRANT CONNECT ON DATABASE hf_demo TO hf_demo_runtime;
GRANT USAGE ON SCHEMA public TO hf_demo_runtime;
GRANT SELECT ON app_user, role, user_role, user_permission TO hf_demo_runtime;
GRANT SELECT, INSERT, UPDATE ON auth_session TO hf_demo_runtime;
GRANT hf_demo_owner TO hf_demo_runtime WITH INHERIT FALSE, SET TRUE;
GRANT hf_patient_portal TO hf_demo_runtime WITH INHERIT FALSE, SET TRUE;
