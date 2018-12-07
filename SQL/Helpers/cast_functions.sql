CREATE OR REPLACE FUNCTION ag_sys.ag_cast_date(
    p_cast text, p_format text DEFAULT 'env'::text, p_default text DEFAULT null::text)
  RETURNS text AS  /* The return is timstamptz in your local format as text, e.g. '2018-01-25 17:54:03.123456+11' */
$BODY$
DECLARE

  v_format text := trim(lower(p_format));
  v_format_default text;
  v_new text := trim(p_cast);
  v_mdy_checked boolean := false;
  v_dmy_checked boolean := false;
  v_ymd_checked boolean := false;
  v_regex_performed boolean := false;
  i smallInt := 0;
  --v_trace text := ''; 
begin

/* 
   Accepts date formats as documented in https://www.postgresql.org/docs/9.6/datatype-datetime.html#DATATYPE-DATETIME-DATE-TABLE
   Plus we also remove days and commas that can interfere with unusual custom formats
   todo: remove the date suffix (2nd, 3rd, etc..) without interfering with the timezone and remove 'sat' (the day for saturday) without interfering with the 'SAT' timezone.
*/

BEGIN
 case v_format
   when 'dmy', 'mdy', 'ymd' then null;
   else v_format := (select lower(right(current_setting('datestyle'), 3)));
 end case;
EXCEPTION
  when OTHERS then v_format := 'mdy';
END;
 
  v_format_default := v_format;
  --v_trace := '(' || v_format;

LOOP
  i := i + 1;
  if i > 6 then return p_default; end if;

  select set_config('datestyle', v_format, true) INTO v_format;

 BEGIN
 /*  
   v_trace := v_trace || ')(i=' || i::text || ' v_format=' || v_format || ' v_mdyc=' || v_mdy_checked::text || ' v_dmyc=' || v_dmy_checked::text || ' v_ymdc=' || v_ymd_checked::text || ' v_regex=' || v_regex_performed::text || ' v_new=' || coalesce(v_new, '');
*/

   if i > 3 and v_regex_performed = false then
     v_regex_performed := true;
     v_new := trim(regexp_replace(v_new, '(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sun|,)', '', 'gi'));
     /* Todo:
        Add regex to remove nd/rd/th/st from 23rd, 1st, 2nd, etc... without affecting a timezone like AEST
        Add regex to remove sat without affecting the SAT timezone
     */
   end if;

   case v_format when 'dmy' then v_dmy_checked := true; when 'mdy' then v_mdy_checked := true; else v_ymd_checked := true; end case;
   
   return v_new::timestamptz::text;

 EXCEPTION
   when OTHERS THEN
     if v_mdy_checked = true then
       if v_dmy_checked = true then
         if v_ymd_checked = true then
           if v_regex_performed = true then return p_default;
           else
             v_format := v_format_default;
             v_mdy_checked := false; v_dmy_checked := false; v_ymd_checked := false;
           end if;
         else v_format := 'ymd'; end if;
       else v_format := 'dmy'; end if;
     else v_format := 'mdy'; end if;
 END;
END LOOP;

EXCEPTION
  WHEN OTHERS THEN
    return p_default;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
