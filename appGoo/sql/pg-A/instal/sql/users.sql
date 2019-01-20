/*
# Create appGoo Users. This must be performed as a superUser
# Users will only be created if they do not exist
*/

DO $$
DECLARE
   isFound boolean := false::boolean;
   
BEGIN

	select (x.notfound = 1) from (
		select -1 as notfound
		from pg_catalog.pg_roles r
		where lower(r.rolname) = 'agroot'
		union all
		select 1 as notfound
		order by notfound asc) as x limit 1
	into isFound;

	if isFound then create user agroot with superuser; end if;
	isFound := false;

	select (x.notfound = 1) from (
		select -1 as notfound
		from pg_catalog.pg_roles r
		where lower(r.rolname) = 'agauth'
		union all
		select 1 as notfound
		order by notfound asc) as x limit 1
	into isFound;

	if isFound then 
		create user agauth with nosuperuser nocreaterole login password $___ag___$&AGPWD$___ag___$ nobypassrls;
	end if;
   
END$$;
