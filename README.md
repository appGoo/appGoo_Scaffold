# appGoo Scaffold
The 'Scaffold' repo primarily concerns itself with the pg/plsql development environment that builds Dynamic appGoo Databases Pages and Functions for the Web.

The functions are authored through your IDE (such as Sublime, Emacs or Visual Studio Code), saved in the file system and the appGoo Builder is then run to build the functions and procedures within the destination database.

## The appGoo Builder
TBA

## appGoo Builder Functions
All functions and procedures (collectively referred to as functions) belong to the 'ag_sys' schema. The procedures and functions that you author will be in your application's private schema and it's "search path" can be set to be before ag_sys so that you may use your version of the appGoo helper functions. If you alter the definition of the appGoo helper function then it is likely that it will get replaced and re-built due to a package update, therefore you are better implementing your own version of the function by copying (or creating your own) the appGoo version and altering what is required.

Function | Returns | Example | Notes
-------- | ------- | ------- | -----
ag_is_int (text) | integer | ag_is_int('3') = 1 | This is a safe function for determining that the variable is an integer. Returns 1 if it is an Integer, 0 if it is not an integer, and -1 if it is out of range of an integer and therefore is a BigInt. Note that decimals will be ignored. Once evaluated you can safely cast it.
ag_is_bigint (text) | integer | ag_is_bigint('3') = -1 | This is a safe function for determining that a variable is a big integer. Returns 1 if it is a big integer that is out of the range of an integer, 0 if it is not a big integer, and -1 if it is in the bounds of an integer. Decimals are ignored. Once evaluated you can afely cast it.
