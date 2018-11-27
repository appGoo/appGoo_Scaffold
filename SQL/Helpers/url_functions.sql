/*
All functions that relate to working with URL Strings
 - decode/encode
 - parameter parsing
 
 We can parse an individual parameter or we can have the entire parameter string parsed into a JSONB object that allows fast retrieval of any/all parameters
*/

CREATE OR REPLACE FUNCTION ag_urlDecode(
    p_encoded text DEFAULT '')
  RETURNS text AS
$BODY$

  SELECT convert_from(CAST(E'\\x' || array_to_string(ARRAY(
    SELECT CASE WHEN length(r.m[1]) = 1 THEN 
      encode(convert_to(r.m[1], 'SQL_ASCII'), 'hex') 
    ELSE 
      substring(r.m[1] from 2 for 2) 
    END
  FROM regexp_matches(replace($1, '+', ' '), '%[0-9a-f][0-9a-f]|.', 'gi') AS r(m)), '') AS bytea), 'UTF8')


$BODY$
  LANGUAGE sql VOLATILE
  COST 100;

CREATE OR REPLACE FUNCTION ag_urlEncode(p_string text default '')
 RETURNS text AS
$body$
DECLARE
    i      integer;
    v_tempTxt   text;
    v_ascii  integer;
    v_encodedText text;
BEGIN
    v_encodedText = '';
    FOR i IN 1 .. length(p_string) LOOP
        v_tempTxt := substr(p_string, i, 1);
        IF v_tempTxt ~ '[0-9a-zA-Z:/@._?#-]+' THEN
            v_encodedText := v_encodedText || v_tempTxt;
        ELSE
            v_ascii := ascii(v_tempTxt);
            IF v_ascii > x'07ff'::integer THEN
            /* This means that the text includes a 3-byte or more sequence */
                --RAISE EXCEPTION 'Won''t deal with 3 (or more) byte sequences.';
              v_encodedText := v_encodedText || v_tempTxt;
            ELSE
	      IF v_ascii <= x'0f'::integer THEN
		v_tempTxt := '%0'||to_hex(v_ascii);
	      ELSIF v_ascii <= x'07f'::integer THEN
		v_tempTxt := '%'||to_hex(v_ascii);
	      ELSE
		v_tempTxt := '%'||to_hex((v_ascii & x'03f'::integer)+x'80'::integer);
		v_ascii := v_ascii >> 6;
		v_tempTxt := '%'||to_hex((v_ascii & x'01f'::integer)+x'c0'::integer) || v_tempTxt;
	      END IF;
              v_encodedText := v_encodedText || upper(v_tempTxt);
             END IF;
         END IF;
    END LOOP;
    RETURN v_encodedText;
    
EXCEPTION
    WHEN OTHERS THEN
        return p_string;
END
$body$
LANGUAGE plpgsql;

create or replace function ag_parseParams(
    p_parameter_string text,
    p_parameter text,
    p_decode boolean default true,
    p_default_value text default ''
    )
RETURNS text AS
$BODY$
declare
    v_parameter text := '&' || replace(replace(lower(p_parameter), '&', ''), '=', '') || '=';
    v_parameter_start integer;
    v_paramValue_len  integer;
    v_parameter_string text := trim(coalesce(p_parameter_string, ''));
    v_return_text text := ''; 
begin
    /* Prepare Parameter String
    We need to cater for:
         http://example.com/?x=1
         ?x=1
         x=1
         '' */
    v_parameter_string := substring(v_parameter_string from position('?' in v_parameter_string));
    if left(v_parameter_string, 1) = '?' then
      v_parameter_string := '&' || substring(v_parameter_string from 2);
    else
      v_parameter_string := '&' || v_parameter_string;
    end if;
    v_parameter_start := position(v_parameter in lower(v_parameter_string));
    if v_parameter_start > 0 then
         v_parameter_start := v_parameter_start + length(v_parameter);
         v_paramValue_len := position('&' in substring(v_parameter_string from v_parameter_start))-1;
         if v_paramValue_len > 0 then
            v_return_text := substring(v_parameter_string from v_parameter_start for v_paramValue_len);
         else
            if trim(left(substring(v_parameter_string from v_parameter_start),1)) = '&' then
              v_return_text := '';
            else
              v_return_text := substring(v_parameter_string from v_parameter_start);
            end if;
         end if;
    end if;

    if coalesce(v_return_text, '') = '' THEN v_return_text := coalesce(p_default_value, ''); end if;

    if p_decode THEN
      return ag_urlDecode(v_return_text);
    else
      return v_return_text;
    end if;

exception
    when others then
      if coalesce(length(p_default_value),0) > 0 then
        return p_default_value;
      else -- return safe values
        return null;
    end if;
end;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;



create or replace function ag_parseParams(
    p_parameter_string text,
    p_decode boolean default true
    )
RETURNS JSONB AS
$BODY$
declare
    v_parameter_string text := trim(coalesce(p_parameter_string, ''));
    v_paramStr text := '';
    v_arr1  text[];
    v_arr2  text[];
    i   integer;
begin
    /* Prepare Parameter String
    We need to cater for:
         http://example.com/?x=1
         ?x=1
         x=1
         '' */
    v_parameter_string := substring(v_parameter_string from position('?' in v_parameter_string));
    if left(v_parameter_string, 1) = '?' OR left(v_parameter_string, 1) = '&' then
      v_parameter_string := substring(v_parameter_string from 2);
    end if;
    v_arr1 := string_to_array(v_parameter_string, '&');
    if array_length(v_arr1, 1) = 1 then 
     if coalesce(position('=' in v_arr1[1]), 0) = 0 then RETURN '{}'::jsonb; end if;
    end if;
    
    FOREACH v_paramStr IN ARRAY v_arr1 LOOP
       v_arr2 := v_arr2 || string_to_array(v_paramStr, '=');
    END LOOP;

    if p_decode then
       FOR i IN 2 .. array_length(v_arr2, 1) BY 2 LOOP
         v_arr2[i] := ag_urlDecode(v_arr2[i]);
       END LOOP;
    end if;

    RETURN jsonb_object(v_arr2);

exception
    when others then
      return '{}'::jsonb;
end;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
