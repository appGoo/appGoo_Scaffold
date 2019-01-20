/* 
# User authentication objects.
# Note that this assumes that the agAuth user exists

*/

create table if not exists ag_sys.agUsers (
user_id integer primary key default nextval(ag_sys.agSeq),
username text not null,
hashword text,
isActive boolean not null,
emailAddress text,
description text );

create or replace view ag_sys.agAuthUsers_v as 
	select user_id, username, hashword
	from ag_sys.agUsers 
	where isActive;