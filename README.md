# Requirements

* [Python 3.6+](https://www.python.org)
* [Tampermonkey](https://tampermonkey.net/) (or another web-browser userscript manager, optional)


# Instructions

* `Dotabuff match ID extractor.js` is an userscript to be used with the links on `recent.html` to get recent match IDs. If you already have a collection of (or some alternative access to) match IDs, you can skip this phase altogether.
* `recent.py` will receive these IDs and cache results from OpenDota to a subfolder. Once a given match information is downloaded, it will not be retrieved again as long as a file exists for it in the cache subfolder. Invalid matches will still be saved in order to prevent as many repeat calls as possible to OpenDota.
* ` process.py` will then scan and process all cached matches, ignoring those that are invalid (ie. abandoned, bot games, etc).

Make sure to delete your local cache if you want to perform an entirely new batch of processing. Don't run more than one retrieval process at once to respect OpenDota's request policy.

This process has been designed and tested only for game modes allowed on Ranked Matchmaking. If you supply Match IDs for custom games and lobbies or non-standard game modes, you'll likely need to reevaluate and fine-tune many (or all) indicators used.
