# appGoo Scaffold
The 'Scaffold' repo primarily concerns itself with the pg/plsql development environment that builds Dynamic appGoo Databases Pages and Functions for the Web.

The functions are authored through your IDE (such as Sublime, Emacs or Visual Studio Code), saved in the file system and the appGoo Builder is then run to build the functions and procedures within the destination database.

[Read more about appGoo capability](TBD)

[Read more about how to develop applications in appGoo](TBD)

## The appGoo Builder
Simply referred to as the 'Builder', this program can build your application code into the database so that it is ready to be called by appGoo. The Builder installs the appGoo capability into the database as well as the application that you develop.

The builder caters for an upgrade to appGoo as enhancements and fixes are released, and also has the ability for you to upgrade the data and objects of your application in addition to new versions of your code.

The Builder consists of the following programs:
1. agBuild. This is the core program that builds your application code into the database.
2. agNew. Can instantiate a new appGoo project for you by creating a custom folder structure and populating the structure with the appGoo functionality to be installed into the database
3. agCreate. Can convert existing text assets into a database function call that allows the text asset to be retrieved by calling the function. For example, a call for a CSS file could be made from the database rather than the filesystem. Also allows minimisation, and caters for both CSS and JavaScript. This will also allow you to modify the output of either function based upon runtime parameters you supply.
4. agClean. This removes appGoo and all your code from the database but does not uninstall the objects nor data (apart from the functions and procedures)

[Read more about the appGoo Scaffold Builder](appGoo/docs/builder.md)

## appGoo Builder Functions
appGoo includes procedures and functions that are used to support the appGoo capability and to also accelerate the development of applications.

appGoo instals into a schema titled 'ag_sys' which refers to "appGoo System". You do not develop in this schema. If you do modify the objects within ag_sys you risk your customisation being replaced by an appGoo upgrade which will replace your customisations without notice.

The procedures and functions that you author will be in your application's private schema and it's "search path" can be set to be before ag_sys so that you may use your version of the appGoo helper functions. If you alter the definition of the appGoo helper function then it is likely that it will get replaced and re-built due to a package update, therefore you are better implementing your own version of the function by copying (or creating your own) the appGoo version and altering what is required.

[Read more about the appGoo Helper Functions](appGoo/docs/helperFunctions.md)
