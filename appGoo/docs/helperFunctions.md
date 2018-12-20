
#### ag_has_permission RETURNS BOOLEAN

This returns a true or false for determining whether a user has been assigned a role that is linked to a particular permission set within the application. You can pass ... TBA

Parameter | Type | Default | Notes
--------- | ---- | ------- | -----
p_permission | text | | This is the "permission code" that is either an integer expressed as text or a text string with no spaces. Examples are '100500' and 'view_projects'. Case insensitive
p_user | text | | This is either the username of the user or the user_id integer of the user passed as a text string. you can also pass current_user. There is deliberately no default of current_user to ensure that the application understands whom specifically it is checking permission for
```
ag_has_permission('150100', current_user) = false
```
------------------------


#### ag_has_role RETURNS BOOLEAN
This returns true or false depending upon whether the user passed is a member of the database role stated. The database username or the user_id can be passed and the role name is case insensitive. The 'name' data type is a special text datatype, if an integer is passed for a role name, ensure it is specifically cast like '1234'::name. 

Parameter | Type | Default | Notes
--------- | ---- | ------- | -----
p_role | name | | This is the case insensitive name of the application role that you want to check to see if the supplied user is a member of
p_user | text | | This is either the username or the user_id of the user to be used for validation purposes. If the user_id is passed ensure that it is quoted to be treated as text. Special database variables like current_user can also be passed
```
ag_has_role('Project Admin', '1421') = true
```
--------------------------

#### ag_is_*dataType* functions RETURNS INTEGER
There are multiple of these safe functions that allow you to test whether a text value is of a particular datatype. Returning an integer, a return of 1 indicates that the passed value is that of the datatype, 0 is a fail and it is not of the datatype. There is also a return of -1 that indicates another property of the value that is relevant for casting purposes, see the table below for further explanation.

Function | Results | Notes
-------- | ------- | -----
ag_is_date | 0 = not, 1 = Date only, 2 = Date with time, 3 = Timestamp, 4 = Timestamp with timezone | When testing for dates it does not matter if 3/4/20 is 3rd April or 4th March because both responses are valid dates, but if it is 7/13/20 it will always try to resolve this to 13th July. Note that '3/4' or '4-Mar' or '4 Mar' or '4 March' or '4th March' will resolve to a valid date using the current year as it is expected that other helper functions can be used to build a complete date with this information. However, only the year may be omitted, if the month or day is omitted then it is not considered a valid date. Special monikers for the date like 'Today' and 'Yesterday' are not considered valid dates here even though there might be other appGoo functions that convert them to a date
ag_is_interval | ? | TBA
ag_is_numeric | 0 = not, 1=smallInt, 2=Int, 3=BigInt, 4=Numeric | This tests if the text can be converted to a number value. It allows currency symbols, +/-, commas, leading decimal (e.g .3) and scientific notation. It will accept any number within the numeric range. It can also accept brackets and basic mathematical formulas but any complexity could result in the result being 0. All numbers with decimals (apart from X.0) will be returned as a numeric. The smallest data type that it can conform with will be the returned result, therefore testing '100' would return a smallInt rather than an Integer or bigInt even though this number could be cast to all 3 datatypes. Note that appGoo may recognise the value as a particular datatype, but it does not mean that the native cast functionality will work. For example, ag_is_numeric('$.7') = 4, but if you then did '$.7'::numeric you would encounter an error. Therefore you are best to use the ag_cast function to return the required value. 

```
ag_is_date('31/12/80') = 1; ag_is_date('11-DEC-17 15:36') = 2; ag_is_date('Today') = 0; ag_is_date('3/4') = 1;
ag_is_numeric('-214748364799') = 3; ag_is_numeric('-$214,748,364,799.0000') = 3; 
ag_is_numeric('7.0') = 1; ag_is_numeric('20e2') = 1; ag_is_numeric('-$.7')= 4; ag_is_numeric('3/4') = 0; 
ag_is_numeric('76%') = 0; ag_is_numeric('(21*700)-30000') = 3
```
----------------------------


#### ag_?


