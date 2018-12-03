/*
The developer can choose to check for an application role that has been assigned to a user (because roles have the permissions assigned that they are checking), or they can check for the existence of an individual permission. This will be determined by the logic of the app and how they implement permissions to roles.
*/

CREATE FUNCTION ag_has_role(p_role NAME, p_user text) RETURNS BOOLEAN AS
DECLARE
 v_user_id INT;
 v_user    NAME;
BEGIN
 IF ag_is_numeric(p_user) IN (1,2) THEN
    v_user_id := p_user::int;
    SELECT db_username INTO v_user
    FROM ag_sys.ag_users
    WHERE user_id = v_user_id;
 ELSE -- p_user is text
    SELECT db_username INTO v_user
    FROM ag_sys.ag_users
    WHERE lowercase(username) = lowercase(p_user);
 END IF;

 RETURN (SELECT pg_has_role(v_user, p_role, 'USAGE'));

EXCEPTION
 RETURN false;
END; 
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = ...; 

CREATE FUNCTION ag_has_permission(p_permission TEXT, p_user text) RETURNS BOOLEAN AS
DECLARE
 v_user_id INT;
 v_user    NAME;
BEGIN
 IF ag_is_numeric(p_user) IN(1,2) THEN
    v_user_id := p_user::int;
 ELSE -- p_user is text
    SELECT user_id INTO v_user_id
    FROM ag_sys.ag_users
    WHERE lowercase(username) = lowercase(p_user);
 END IF;

 RETURN (SELECT (pr.x > 0)
         FROM (
           SELECT 0 AS x
           UNION ALL
           SELECT 1 AS x
           FROM ag_sys.ag_role_permissions p,
                ag_sys.ag.user_roles r
           WHERE p.role_id = r.role_id
           AND   p.permission_code = lower(p_permission)
           AND   r.user_id = v_user_id
           ORDER BY x LIMIT 2
               ) pr ORDER BY x DESC LIMIT 1);

EXCEPTION
  RETURN false;
END; 
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = ...;
