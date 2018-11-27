/*
is_data_type.sql
This is a series of functions that return 3 choices (0 = false, 1 = true it is the data type, -1 = it can be the data type but is also another data type) stating whether the input is a particular data type and do not throw any uncaught exceptions. Types to check are:

* Integers, -1 is returned if it is a bigint
* Bigint, -1 is returned if it could also be an integer
* Date, -1 is returned if it also has a timezone
* Timestamp, -1 is returned if it also has a timezone
* Interval 
*/

CREATE OR REPLACE FUNCTION ag_sys.ag_is_int(p_int text) RETURNS INTEGER AS $$
DECLARE
 v_big BIGINT; 
BEGIN

 v_big := ABS(p_int::bigint);
 
 IF v_big > 2147483647 THEN RETURN -1; ELSE RETURN 1; END IF;
         
EXCEPTION
 WHEN OTHERS THEN
  RETURN 0;
END;$$ LANGUAGE plpgsql

CREATE OR REPLACE FUNCTION ag_sys.ag_is_int(p_int bigint) RETURNS INTEGER AS $$
DECLARE
 v_out INT;
BEGIN

 EXECUTE 'SELECT ag_sys.ag_is_int(''' || p_int || ''')' INTO v_out;
 RETURN v_out;
         
EXCEPTION
 WHEN OTHERS THEN
  RETURN 0;
END;$$ LANGUAGE plpgsql
