import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s::%(levelname)s::%(message)s')

import time
import json
import requests


class MattermostAPI:
    def __init__(self, url):
        self.url = url
        self.token = ""

    def get(self, request):
        headers = {"Authorization": "Bearer " + self.token }
        g = requests.get(self.url + request, headers=headers)
        return json.loads(g.text)

    def post(self, request, data=None):
        headers = {"Authorization": "Bearer " + self.token }
        logging.debug(json.dumps(data, indent=4))
        p = requests.post(self.url + request, headers=headers, data=json.dumps(data))
        return json.loads(p.text)

    def signup_with_team(self, team_id, email, username, password, allow_marketing):
        return self.post('/users/create', {
            'team_id': team_id,
            'email': email,
            'username': username,
            'password': password,
            'allow_marketing': allow_marketing
        })
    def login(self, name, email, password):
        """Login to the corresponding (self.url) mattermost instance."""
        props = { 'name': name, 'email': email, 'password': password }
        p = requests.post(self.url + '/users/login', data=json.dumps(props))
        self.token = p.headers["Token"] # Store the token for further requests
        return json.loads(p.text)
    def get_channels(self):
        return self.get('/channels/')
    def get_more_channels(self):
        return self.get('/channels/more')
    def get_channel_counts(self):
        return self.get('/channels/counts')
    def create_channel(self, name, display_name, team_id, description, channel_type):
        return self.post('/channels/create', {
            'name': name,
            'display_name': display_name,
            'team_id': team_id,
            'description': description,
            'type': channel_type
        })
    def create_direct_channel(self):
        return self.post('/channels/create_direct')
    def update_channel(self, props):
        return self.post('/channels/update', props)
    def update_channel_desc(self, channel_id, channel_description):
        return self.post('/channels/update_desc', { 'channel_id': channel_id, 'user_id': user_id })
    def channel(self, channel_id):
        return self.get('/channels/%s/' % (channel_id))
    def channel_extra_info(self, channel_id):
        return self.get('/channels/%s/extra_info' % (channel_id))
    def channel_join(self, channel_id):
        return self.post('/channels/%s/join' % (channel_id))
    def channel_leave(self, channel_id):
        return self.post('/channels/%s/leave' % (channel_id))
    def channel_delete(self, channel_id):
        return self.post('/channels/%s/delete' % (channel_id))
    def channel_add(self, channel_id, user_id):
        return self.post('/channels/%s/add' % (channel_id), { 'user_id': user_id })
    def channel_remove(self, channel_id):
        return self.post('/channels/%s/remove' % (channel_id), { 'user_id': user_id })
    def channel_update_last_viewed_at(self, channel_id):
        return self.post('/channels/%s/update_last_viewed_at' % (channel_id))

    def create_post(self, user_id, channel_id, message, create_at=int(time.time() * 1000), filenames=[], state="loading"):
        return self.post('/channels/%s/create' % (channel_id), {
            'user_id': user_id,
            'channel_id': channel_id,
            'message': message,
            'create_at': create_at,
            'filenames': filenames,
            'pending_post_id': user_id + ':' + str(create_at),
            'state': state
        })

    def get_channel_posts(self, channel_id, since):
        return self.get('/channels/%s/posts/%s' % (channel_id, since))

    def get_channel_post(self, channel_id, post_id):
        pass


class MattermostClient:

    def __init__(self, url):
        self.users = {}
        self.channels = {}
        self.mentions = {}
        self.api = MattermostAPI(url)
        self.user = None

    def signup_with_team(self, team_id, email, username, password):
        """Signup the user as if it were just created.

        Creates a new user on the Mattermost instance. This implementation
        specifically requires a team token to be provided. Any existing
        Mattermost user can easily retrieve this team token since it's just
        the team's ID. It will NOT work if the Mattermost instance has no
        users (and, consequently, no teams).

        Arguments:
        team_id -- The hash representing the team's ID.
        email -- A valid (not sure if this is only validated on the client
                 side) e-mail address for the user to be notified, also
                 allowing password reset, and other functionality.
        username -- The username/nickname of the user creating the account.
                    Remember that the login is done with email, not username.
        password -- The password for the user being created.
        """
        self.api.signup_with_team(team_id, email, username, password, True)

    def login(self, team, email, password):
        """Login to the Mattermost instance.

        Sends a request that returns a token which is automatically stored
        within our MattermostAPI object for convenience. It will also
        immediately update the internal object state with everything concerning
        the server (channel lists, etc.).

        Arguments:
        name -- May be the channel_id, channel url-name or channel
                display_name.
        """
        self.user = self.api.login(team, email, password)
        self.update()
        return self.user

    def join_channel(self, name):
        """Join a channel.

        Required to be able to actually send messages to the channel.

        Arguments:
        name -- May be the channel_id, channel url-name or channel
                display_name.
        """
        r = self.api.channel_join(self.channels[name]["id"])
        if 'status_code' in r.keys():
            if r["status_code"] == 500:
                logging.error("Unable to join channel (%s): %s" % (name, json.dumps(r, indent=4)))

    def create_channel(self, display_name):
        """Create a channel.

        This action also makes the user a 'channel administrator'. If the
        channel already exists, this will give us an error.

        Arguments:
        display_name -- The user-visible name of the channel. We automatically
                        convert it to a viable url-name.
        """
        url_name = name.replace('_', '-').lower()
        r = self.api.create_channel(url_name, display_name, self.user["team_id"], description="", channel_type="O")
        if r["status_code"] == 400:
            logging.error("Unable to create channel (%s): %s" % (name, json.dumps(r, indent=4)))

    def leave_channel(self, channel):
        """Leaves a channel.

        Leave a channel the user is currently in. Since the Mattermost
        API allows a user to leave a channel where the user isn't in,
        we perform that validation ourselves to avoid spamming others
        with unwarrented notifications.

        Not being in a channel is actually not very important within
        a Team setting, since we're able to parse the channels we're
        not in without any kind of issue

        Arguments:
        channel -- The ID, name (url-name) or display_name of a channel.
        """
        c_id = self.channels[channel]["id"]
        r = self.api.channel_leave(c_id)
    
    def get_mentions(self, channel_id):
        """Get a list of mentions from a channel.

        Whenever a user messages another with @other_user, it counts as a
        "mention", which is stored in the model. What we do is retrieve
        a list, taking into account how exactly it counts a user is
        being mentioned (defined in the user's properties). Also, we
        only return the messages of the mentions themselves. I'm guessing
        this is good enough for 99% of the use cases, but sometimes you
        may want to have a 'chat' with the bot and this will not be enough.

        Example (which will NOT work with the current method):
        me: @jenkins build my job
        jenkins: sorry @user, but the parameters -h hello are required
        me: -h <something>
        jenkins: @user starting "build my job -h hello"
        """
        mentions = []
        c_id = channel_id
        since = self.channels[channel_id]["members"]["last_viewed_at"]
        posts = self.api.get_channel_posts(c_id, int(since))["posts"]
        if posts is None or self.channels[channel_id]["members"]["mention_count"] <= 0:
            return mentions
        for p in self.api.get_channel_posts(c_id, int(since))["posts"].values():
            keys = self.user["notify_props"]["mention_keys"].split(',')
            for k in keys:
                if k in p["message"]:
                    mentions.append(p)
            self.api.channel_update_last_viewed_at(c_id)
        return mentions

    def update(self):
        """Update the internal state to match the Mattermost instance."""

        # Channels the user is in
        r = self.api.get_channels()
        for channel in r["channels"]:
            channel["members"] = r["members"][channel["id"]]
            self.channels[channel["id"]] = channel
            self.channels[channel["name"]] = channel
            self.channels[channel["display_name"]] = channel
            # Update the mentions for this channel
            for m in self.get_mentions(channel["id"]):
                self.mentions[m["id"]] = m
        # Channels the user is NOT in, may be completely empty
        r = self.api.get_more_channels()
        for channel in r["channels"]:
            self.channels[channel["id"]] = channel
            self.channels[channel["name"]] = channel
            self.channels[channel["display_name"]] = channel

    def channel_msg(self, channel, message):
        """Send a message to a specific channel.

        There is no big mistery here, a simple message to a channel. It should
        be taken into account that channels aren't only limited to public (O).
        They might also be private 1:1 channels (D) which are the equivalent
        of sending a private message, and private channels for multiple users,
        which restrict who can participate in that channel (by default,
        channels should be considered public, though).

        Keyword arguments:
        channel -- Can be the channel_id, url-name or display_name of the channel.
        message -- The message being sent.
        """
        c_id = self.channels[channel]["id"]
        r = self.api.create_post(self.user["id"], c_id, 'blah')
        if 'status_code' in r.keys():
            if r["status_code"] == 403:
                logging.error("You need to join the channel first (%s): %s" % (channel, r["message"]))

m = MattermostClient("http://localhost:8065/api/v1")
#m.signup_with_team('gzwzj9yn5pg65yfb55seqnh1zo', 'c@c.com', 'myuser3', 'mypassword')
m.login("helloteam", "c@c.com", "mypassword")
print(json.dumps(m.mentions, indent=4))
m.mentions

#print(json.dumps(m.get_mentions(), indent=4))
#m.leave_channel('hello')
#m.join_channel('world')
#m.channel_msg('world', 'world everyone')
#m.create_channel('hello')
##m.join_channel('helloworld')
