# A statistical analysis of how poorly-matched players affect DotA 2 matches

## Requirements

* Tampermonkey (or another userscript manager) https://tampermonkey.net/
* Python 3.6+ https://www.python.org

## Scripts included

* `Dotabuff match ID extractor.js` userscript to be used with the links on `recent.html` to get recent match IDs.
* `recent.py` will receive these IDs and cache results from OpenDota to a subfolder. Once a given match information is downloaded, it will not be downloaded again while a file exists for it. Invalid matches will still be downloaded once, in order to prevent as many calls as possible to OpenDota (netiquette).
* ` process.py` will then scan and process all cached matches, ignoring those that are invalid (abandoned, etc).

Make sure to delete your local cache if you want to perform an entirely new batch of processing. Don't run more than one retrieval process at once to respect OpenDota's request policy.
