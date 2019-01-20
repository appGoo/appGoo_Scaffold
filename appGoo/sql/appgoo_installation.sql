# SQL Files for the appGoo installation. Must reference file relative to current location of this file
# and files can only be in a subfolder.
# Folder substitution characters are:
# ~ Project HOME_DIR
# . up one level. This can be repeated. For example applying .. to "users/joe/git/projects/dinobj/play/sql" 
#   would result in "users/joe/git/projects/dinobj/"
# If the Project home directory is /usr/robert/git/ProjectX and the current directory was /source/sql, then an example of ~/app/instal would result in "/usr/robert/git/projectX/app/instal/"

<%include sql/users.sql %>
commit;
<%include sql/schema.sql %>
<%include sql/sequences.sql %>
<%include sql/auth_objects.sql %>