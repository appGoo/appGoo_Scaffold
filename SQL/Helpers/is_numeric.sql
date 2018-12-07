/*
is_numeric.sql
This is a SAFE function that returns an integer (0 = false, > 0 a legal data type). You can pass a value to this (text) and not invoke an error if the datatype is not correct
*/

CREATE OR REPLACE FUNCTION ag_sys.ag_is_numeric(p_numeric text) RETURNS INTEGER AS $$
DECLARE
 v_pos integer; 
 v_type integer := 0;
 v_numeric text := lower(trim(p_numeric));
 c_numeric numeric;
 c_bigint bigint;
 c_int integer;
 c_smallint smallint;
BEGIN

/* 
  Note: This does not find numbers in a string and strips out the text. For example B38 does not become 38. Instead it checks to see if the complete value is a legal number. If you want to strip out text, then use to_number(text,format)

  0: Not a number that can be used - it might be too large or contain text
  1: SmallInt; -32768 to 32767
  2: Integer;  -2147483648 to 2147483647
  3: Big Integer; -9223372036854775808 to 9223372036854775807
  4: Numeric; up to 99 digits before the decimal place and up to 38 digits after the decimal place
  5: Roman Numerals; from 1 to 3999 (not yet implemented)
  6: Have not implemented scientific notation
  We don't test for other data types. we allow -/+, $ and local currency symbols, and commas
*/

  -- Initial check to see if it contains any letters
  -- To enhance to check for 'e' for scientific notation, then change pattern to '[a-df-z]'
  if coalesce(substring(v_numeric, '[a-z`~!@#&*_={}<>?/\\\|]'),'0') != '0' THEN
       return 0;
  else
    --If it is a percent, then divide the number by 100 before proceeding
    --It is possible that this results in a decimal or a whole number, so we cannot automatically return a 4
    if position('%' in v_numeric) = length(v_numeric) then
      c_numeric:= to_number(v_numeric, '99999999999999999999D9999999999S')/100;
    else
      --We only treat a single % as the last character of the string as being legal (checked above), otherwise we error
      if coalesce(substring(v_numeric, '[%]'),'0') != '0' THEN
        return 0;
      else
        -- if it can be cast as numeric, then detect if it has a decimal, if no decimal then do other tests
        c_numeric:= to_number(v_numeric, '99999999999999999999D9999999999S');
      end if;
    end if;
    v_type := 4;
    v_pos := position('.' in c_numeric::text);
    if v_pos > 0 AND substring(c_numeric::text from v_pos+1)::numeric > 0 THEN return 4; end if;
    
    c_bigint   := c_numeric::bigint;  v_type := 3;
    c_int      := c_numeric::integer; v_type := 2;
    c_smallint := c_numeric::smallint;
    return 1;
  end if;
         
EXCEPTION
 WHEN OTHERS THEN
  RETURN v_type;
END;$$ LANGUAGE plpgsql
