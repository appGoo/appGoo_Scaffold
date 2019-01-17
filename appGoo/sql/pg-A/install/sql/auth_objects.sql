/* 
# User authentication objects.
# Note that this assumes that the agAuth user exists

*/

create table ag_sys.agUsers (
user_id integer primary key default nextval(ag_sys.agSeq),
username text not null,
hashword text,
isActive boolean not null,
emailAddress text,
description text );