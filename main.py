from gildcivility_helpers import CivilityDB as db
from gildcivility_helpers import RedditCrawler as r
from gildcivility_helpers import RedditPoster as rp
from gildcivility_helpers import Twilio as twilio
import os
import json
from flask import Flask, request
app = Flask(__name__)


class HTTP:
    @staticmethod
    def status_code(params, auth):
        if auth != os.environ.get('AUTH'):
            return {"status_code": 401, "error": "Invalid Authentication"}
        for param, value in params.items():
            if not value:
                return {"status_code": 422, "error": "Bad request: Missing param '{}'".format(param)}


class App:
    @staticmethod
    @app.route("/poster", methods=["POST"])
    def poster():
        bodies, rids = request.values.get("Bodies"), request.values.get("RIDs")
        auth = request.values.get("Auth")
        HTTP.status_code(params={"Bodies": bodies, "RIDs": rids}, auth=auth)
        bot_mongo_ids = list()
        for i in range(len(bodies)):
            res, error = rp.post_to_reddit(bodies[i], rids[i])
            if res != 429:
                bot_mongo_id = res
            else:
                return res, error

            doc = db.trigger.find_one({"reddit_id": rids[i]})
            print(doc, rids[i])
            db.update(doc, inp=bot_mongo_id, collection="trigger")
            # Log that a post was made (and what type of post) in the database to avoid duplicate posts
            bot_mongo_ids.append(bot_mongo_id)
        return {"status_code": 201, "mongo_ids": json.dumps(bot_mongo_ids)}

    @staticmethod
    @app.route("/notifier", methods=["POST"])
    def notifier():
        # Evaluate any outstanding Solicitation posts to decide whether to Gild and Post a poem
        notif_sids = list()
        posts = request.values.get("Posts", None)
        auth = request.values.get("Auth")
        HTTP.status_code(params={"Posts": posts}, auth=auth)
        if not posts:
            return 422, "Bad request: Missing param 'Posts'"
        for bot_post in posts:
            bot_score = r.check_new_score(bot_post['reddit_id'])
            notification_sid = None
            if bot_score > 2:
                trigger, flag = r.get_history(bot_post)
                notification_sid = twilio.notification(trigger, flag)
                notif_sids.append(notification_sid)
            db.update(doc=bot_post,
                      inp="notif",
                      collection="bot",
                      notification_sid=notification_sid,
                      new_score=bot_score)
        return {"status_code": 201, "notif_sids": json.dumps(notif_sids)}

    @staticmethod
    @app.route("/sms", methods=["POST"])
    def gilder():
        response = request.values.get("Body", None)
        posts = db.get_post_parts()
        # Gild the Civility confirmed by the above functions using User input (from Twilio) of a poem
        poem, reddit_bot_id, reddit_flag_id = twilio.poem_return(response)
        rp.reddit.comment(id=reddit_bot_id).edit(poem + "\n\n" + posts["footer"])
        rp.reddit.comment(id=reddit_flag_id).gild()
        db.update(reddit_bot_id, inp="gilding", poem=poem, collection="bot")
        return {"status_code": 201, "reddit_id": reddit_bot_id}


if __name__ == "__main__":
    print("\n\nBetter to die in service of immortality")
    print("than leave the planet")
    print("without trying to better it.\n\n")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
