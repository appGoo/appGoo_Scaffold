/*
create_sequence.sql

This is needed to enable consistent creation of like sequences from 9.6 and beyond. As of pg11, sequences can optionally decalre a data type (integer, bigint) that determine its boundaries. Instead, we manually specify the boundary.

Return 1 for Success, 0 for failure.

*/

CREATE OR REPLACE FUNCTION ag_sys.ag_create_sequence(p_name text, p_start bigint DEFAULT 1001) RETURNS INTEGER AS $$
DECLARE
  v_SQL text;
BEGIN
  -- CREATE SEQUENCE IF NOT EXISTS schema.sequence_name INCREMENT 1 MINVALUE -2147483648 MAXVALUE 2147483647 START 1001 CYCLE;
  v_SQL := 'CREATE SEQUENCE IF NOT EXISTS ' || p_name || ' INCREMENT 1 MINVALUE -2147483648 MAXVALUE 2147483647 START ' || p_start::text || ' CYCLE';
  EXECUTE v_SQL;
  RETURN 1;
         
EXCEPTION
 WHEN OTHERS THEN
  RETURN 0;
END;$$ LANGUAGE plpgsql


