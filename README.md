Convert AAR into Eclipse Android library project
================================================

This is a standalone Python script which convert [an `*.aar` file][aar] to an Android library project that Eclipse is able to import. This allows existing projects still using Eclipse ADT to reference new libraries distributed in `*.aar` without much trouble.

Note that

* [Manifest merging][merge] is not enabled automatically on Eclipse.
* Custom lints (`lint.jar`) are not yet supported

[aar]: http://tools.android.com/tech-docs/new-build-system/aar-format
[merge]: http://stackoverflow.com/q/10976635
