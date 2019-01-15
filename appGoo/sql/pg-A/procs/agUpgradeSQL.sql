/*

agUpgradeSQL(preOrPost text, newVersion text, sql text, testOnly boolean = false::boolean )

1. suppressErrors = False
2. get currentVersion and preStatus and postStatus
   Note that versions could be 1.0.3.0.7.2 -- allow up to 9 digits and zero fill if not supplied in
   newVersion and currentVersion. From left to right, first digit that in newVersion > currentVersion
   means that an upgrade is required
2. determine if newVersion is > currentVersion for pre/postStatus
3. If greater, then execute SQL, if not, end gracefully without messages
4. If upgrade was required, insert new upgrade record and update current version record for 
   pre/postStatus with newVersion
4. If testOnly then suppressErrors = True; SELECT 1; end if;
5. Have an exception block that checks testOnly & suppressErrors and if both are true then
   end gracefully -- otherwise report the error

agUpgradeReset(preOrPost text, resetVersion)

Restore the pre or postStatus record back to the currentVersion.
This updates the currentVersion record & marks the upgrade history table records as archived (but not deleted)
Note that restoring back to preStatus will also reset postStatus for the same version, but reset to postStatus will not reset preStatus

*/