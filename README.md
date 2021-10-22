# TrackDota2-Core
This project's main purpose is to track pro dota players and link match ids with youtube videos. Linking matches is done by identifying the heroes in the youtube video and then searching through the database for matches with similar heroes.

See: [trackdota2](https://www.trackdota2.com)


## todo
docs

tests

date as input for link_matches() (so for e.g yt vids that were uploaded x days ago are only compared with matches that started x days ago) 

write script to delete frame files if the heroes were extracted or invalid.

write script to archive live.json files if they were inserted into db

refactor code/delete unneeded stuff.
