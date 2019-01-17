select current_user
set role appGooAdmin

create table ag_sys.rls_test (
id int primary key default nextval('ag_sys.ag_seq'),
name text,
description text,
age int,
dob date)

drop table ag_sys.rls_test
truncate table ag_sys.rls_test
insert into ag_sys.rls_test values (1, 'stephen', 'dad', 50, '05-mar-1968'),
(2, 'sansanee', 'mum', 36, '30-jun-1982'), (3, 'jonathan', 'son', 2, '8-Nov-2016')

alter table ag_sys.rls_test enable row level security
select * from ag_sys.rls_test

set role appgooadmin

create table ag_sys.ag_data_security_rules (
ds_rule_id int not null primary key default nextval('ag_sys.ag_seq'),
table_name text,
rule_SQL text)

create table ag_sys.ag_data_security_rule_columns (
ds_rule_column_id int not null primary key default nextval('ag_sys.ag_seq'),
ds_column_name text,
ds_operator text,
ds_text_array text[],
ds_value text)

truncate table ag_sys.ag_data_security_rule_columns
insert into ag_sys.ag_data_security_rules values(1, 'ag_sys.rls_test', null)
insert into ag_sys.ag_data_security_rule_columns values(1, 'name', 'like', null::text[], '%e%')

DO $$
DECLARE
   rls_sql1 text := '';
   rls_sql2 text := '';
   i integer := 0;
   r record;
   
BEGIN
   select 'create policy p' || ds_rule_id || ' ON ' || table_name || ' FOR SELECT TO r123 USING '
   into rls_sql1
   from ag_sys.ag_data_security_rules;

   select '(' || ds_column_name || ' ' || ds_operator || ' ''' || ds_value || ''')'
   into rls_sql2
   from ag_sys.ag_data_security_rule_columns;

   EXECUTE rls_sql1 || rls_sql2;
   
END$$;

drop policy p1 on ag_sys.rls_test;
create role r123;
select * from ag_sys.rls_test
GRANT ALL ON SCHEMA ag_sys TO r123;
GRANT ALL ON ag_sys.rls_test to r123
set role r123
select current_user
set role appgooadmin
alter role r123 with noinherit
GRANT ALL ON SCHEMA ag_sys TO appGooSudo;

select * from pg_roles where rolname = 'r123'
select pg_has_role('appgooadmin', 'appgoosudo', 'USAGE')
create user appGooAdmin IN ROLE appGooSudo;
alter role appGooAdmin WITH CREATEROLE;

create user "123"

set role "123"
select current_user::int

set role "root"
set role postgres
set role appgooadmin

select ('x'='x')
select (current_user = '123')
select current_user

DO $$
DECLARE
   rolint int := 123;
   roltxt text := '123';
   
BEGIN
execute 'set role "123"';
if current_user = rolint::name then
    execute 'set role root';
else
    execute 'set role postgres';
end if;
--perform 'select current_user';   
END$$;

create table ag_sys.my_test (
user_id int, user_name name)

insert into ag_sys.my_test values (123, 123)
insert into ag_sys.my_test (user_name) values('test')

select * from ag_sys.my_test

set role "123"
set role root
GRANT ALL ON SCHEMA ag_sys TO "u124";
grant all on ag_sys.my_test to "u124"
select current_user

alter table ag_sys.my_test enable row level security;
create policy p123 on ag_sys.my_test FOR SELECT TO "123" using (user_name like '%123%')
drop policy if exists p123 on ag_sys.my_test

select pg_has_role('123', 'USAGE')

set role root;
drop table ag_sys.my_test;

create table ag_sys.my_test (
user_id name not null primary key default nextval('ag_sys.ag_seq'), user_name name)

create user u124 WITH INHERIT IN ROLE "123";

set role "u124"

select * from pg_auth_members
select * from pg_roles

WITH RECURSIVE cte AS (
   SELECT oid, rolname FROM pg_roles WHERE rolname = 'u123'

   UNION ALL
   SELECT m.roleid, 'member of'
   FROM   cte
   JOIN   pg_auth_members m ON m.member = cte.oid
)
SELECT rolname FROM cte;

select app_role.rolname AS APP_ROLE, app_user.rolname AS APP_USER
from pg_auth_members m, pg_roles app_role, pg_roles app_user
where m.roleid = app_role.oid
and m.member = app_user.oid

select false::boolean AS has_rls
UNION ALL
select COALESCE(true, false)::boolean AS has_rls
from (
select true::boolean
from pg_catalog.pg_class t, pg_catalog.pg_policy p
where t.oid = p.polrelid
and COALESCE(t.relrowsecurity, false)::boolean 
and lower(t.relname) = lower('_events') 
and t.relkind in('r', 'p')
LIMIT 1) x
ORDER BY has_rls DESC
LIMIT 1;

select * from pg_class

ALTER TABLE _events DISABLE ROW LEVEL SECURITY;