This bot helps to remember things.

I've used aiogram for main code creation.
User's sets are stored in Postresql database.
For limiting database access user's set is temporary stored in cash as well as user's state.
State holds user status and current used command in Redis.
There is also a time depended service which end user session (transfer changed data from Redis to database) every {RESET_HOURS}.
This option solves cases when user doesn't end session correctly, yet next time object's pool need to be prapared.
You can add objects one by one or by sending csv file with list of objects.
Training mode sends objects which next repetition day has come. Objects pop up in two randomly chosen modes (key / value or value / key).
Learn mode may be useful for freshly added objects or for objects which failed training check.
For all objects look up enter list_all command.

P.S.: by now mobile version doesn't work properly with spoilers, that is why training mode is better to use on desktop version.
