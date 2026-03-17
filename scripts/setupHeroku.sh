#!/bin/bash

heroku create e3w
heroku git:remote -a e3w
git push heroku master

cat .env | xargs heroku config:set
