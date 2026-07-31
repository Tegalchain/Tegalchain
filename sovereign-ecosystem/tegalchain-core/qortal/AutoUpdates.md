# Auto Updates

## Theory
* Using a specific git commit (e.g. abcdef123) we produce a determinstic JAR with consistent hash.
* To avoid issues with over-eager anti-virus / firewalls we obfuscate JAR using very simplistic XOR-based method.
* Obfuscated JAR is uploaded to various well-known locations, usually including github itself, referenced in settings.
* An `ARBITRARY` transaction is published by a **non-admin** member of the "dev" group (groupID 1) with:
	+ 'service' set to 1
	+ txGroupId set to dev groupID, i.e. 1 
and containing this data:
    + git commit's timestamp in milliseconds (8 bytes)
    + git commit's SHA1 hash (20 bytes)
    + SHA256 hash of *obfuscated* JAR (32 bytes)
* Admins of dev group approve above transaction until it reaches, or exceeds, dev group's approval threshold (e.g. 60%).
* Nodes notice approved transaction and begin auto-update process of:
    + checking transaction's timestamp is greater than node's current build timestamp
    + checking git commit timestamp (in data payload) is greater than node's current build timestamp
    + downloading update (obfuscated JAR) from various locations using git commit SHA1 hash
    + checking downloaded update's SHA256 hash matches hash in transaction's data payload
    + calling ApplyUpdate Java class to shutdown, update and restart node

## Obfuscation method
The same method is used to obfuscate and de-obfuscate:
* XOR each byte of the file with 0x5A

## Typical download locations
The git SHA1 commit hash is used to replace `%s` in various download locations, e.g.:
* https://github.com/QORT/qortal/raw/%s/qortal.update
* https://raw.githubusercontent.com@151.101.16.133/QORT/qortal/%s/qortal.update

These locations are part of the org.qortal.settings.Settings class and can be overriden in settings.json like:
```
  "autoUpdateRepos": [
    "http://mirror.qortal.org/auto-updates/%s",
    "https://server.host.name@1.2.3.4/Qortal/%s"
  ]
```
The latter entry is an example where the IP address is provided, bypassing name resolution, for situations where DNS is unreliable or unavailable.

## XOR tool
To help with manual verification of auto-updates, there is a XOR tool included in the Qortal JAR.
It can be used thus:
```
$ java -cp qortal.jar org.qortal.XorUpdate
usage: XorUpdate <input-file> <output-file>
$ java -cp qortal.jar org.qortal.XorUpdate qortal.jar qortal.update
$
```