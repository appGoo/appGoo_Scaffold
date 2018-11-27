# appGoo Scaffold
The 'Scaffold' repo primarily concerns itself with the pg/plsql development environment that builds Dynamic appGoo Databases Pages and Functions for the Web.

The functions are authored through your IDE (such as Sublime, Emacs or Visual Studio Code), saved in the file system and the appGoo Builder is then run to build the functions and procedures within the destination database.

## The appGoo Builder
TBA

## appGoo Builder Functions
All functions and procedures (collectively referred to as functions) belong to the 'ag_sys' schema. The procedures and functions that you author will be in your application's private schema and it's "search path" can be set to be before ag_sys so that you may use your version of the appGoo helper functions. If you alter the definition of the appGoo helper function then it is likely that it will get replaced and re-built due to a package update, therefore you are better implementing your own version of the function by copying (or creating your own) the appGoo version and altering what is required.

#### Heading 4

##### Heading 5

###### ag_has_permission RETURNS BOOLEAN

This returns a true or false for determining whether a user has been assigned a role that is linked to a particular permission set within the application. You can pass ... TBA

Parameter | Type | Default | Notes
--------- | ---- | ------- | -----
p_permission | text | | This is the "permission code" that is either an integer expressed as text or a text string with no spaces. Examples are '100500' and 'view_projects'. Case insensitive
p_user | text | | This is either the username of the user or the user_id integer of the user passed as a text string. you can also pass current_user. There is deliberately no default of current_user to ensure that the application understands whom specifically it is checking permission for
```
ag_has_permission('150100', current_user) = false
```


###### ag_has_role RETURNS BOOLEAN
----------------------------------
This returns true or false depending upon whether the user passed is a member of the database role stated. The database username or the user_id can be passed and the role name is case insensitive. The 'name' data type is a special text datatype, if an integer is passed for a role name, ensure it is specifically cast like '1234'::name. 

Parameter | Type | Default | Notes
--------- | ---- | ------- | -----
p_role | name | | This is the case insensitive name of the application role that you want to check to see if the supplied user is a member of
p_user | text | | This is either the username or the user_id of the user to be used for validation purposes. If the user_id is passed ensure that it is quoted to be treated as text. Special database variables like current_user can also be passed
```
ag_has_role('Project Admin', '1421') = true
```


TO BE FIXED--
Function | Returns | Example | Notes
-------- | ------- | ------- | -----
ag_is_bigint (text) | integer | ag_is_bigint ('3') = -1 | This is a safe function for determining that a variable is a big integer. Returns 1 if it is a big integer that is out of the range of an integer, 0 if it is not a big integer, and -1 if it is in the bounds of an integer. Decimals are ignored. Once evaluated you can afely cast it.
ag_is_date (text) | integer | ag_is_date ('31/12/80') = 1 | This is a safe function for determining that a variable translates to a date. It returns 1 if it is a date, 0 if it is not a date, and -1 if it is a date with a time. When testing for dates it does not matter if 3/4/20 is 3rd April or 4th March because both responses are valid dates, but if it is 7/13/20 it will always try to resolve this to 13th July. Note that '3/4' or '4-Mar' or '4 Mar' or '4 March' or '4th March' will resolve to a valid date using the current year as it is expected that other helper functions can be used to build a complete date with this information. However, only the year may be omitted, if the month or day is omitted then it is not considered a valid date
ag_is_int (text) | integer | ag_is_int ('3') = 1 | This is a safe function for determining that the variable is an integer. Returns 1 if it is an Integer, 0 if it is not an integer, and -1 if it is out of range of an integer and therefore is a BigInt. Note that decimals will be ignored. Once evaluated you can safely cast it.
ag_is_interval (text) | integer | TBA | TBA 
ag_is_timestamp (text) | integer | ag_is_timestamp ('2/3/18 17:56 GMT+10') = -1 | This is a safe function for determining if a variable is a timestamp. for this to be successful there must be both a full date and time provided. The exception being that '12pm' or '7am' can provided. It returns 1 if it is a timestamp, 0 if it is not a timestamp (this includes it being a date only with no time), and -1 if it is a timestamp but has a timezone. Note that the precision of the time is not important, it does not mater whether it only provides the hour or has to the thousandth of a second, it is still a timestamp. Once evaluated you can safely cast it using other appGoo helper functions that have extensive flexibility with timestamps


