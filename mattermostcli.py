import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s::%(levelname)s::%(message)s')

import requests
import json


class MattermostAPI:
    def __init__(self, url):
        self.url = url
        self.token = ""

    def get(self, request):
        headers = {"Authorization": "Bearer " + self.token }
        g = requests.get(self.url + request, headers=headers)
        return json.loads(g.text)

    def post(self, request, data):
        headers = {"Authorization": "Bearer " + self.token }
        p = requests.post(self.url + request, headers=headers, data=data)
        return json.loads(p.text)

    def login(self, name, email, password):
        """Login to the corresponding (self.url) mattermost instance."""
        props = { 'name': name, 'email': email, 'password': password }
        p = requests.post(self.url + '/users/login', headers=headers, data=json.dumps(props))
        self.token = p.headers["Token"] # Store the token for further requests
        return p
    def get_channels(self):
        return self.get('/channels/')
    def get_more_channels(self):
        return self.get('/channels/more')
    def get_channel_counts(self):
        return self.get('/channels/counts')
    def create_channel(self):
        return self.post('/channels/create')
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




class MattermostChannel:
    def __init__(self, attributes):
        for k, v in attributes.items():
            setattr(self, k, v)

    def update(self, attributes):
        pass

    def update_desc(self, description):
        pass

    def extra_info(self):
        pass

    def add(self, user_id):
        pass

    def remove(self, user_id):
        pass

    def delete(self):
        pass


class MattermostTeam:
    def __init__(self, attributes):
        for k, v in attributes.items():
            setattr(self, k, v)

class MattermostUser:
    def __init__(self, api, attributes):
        self.api = api
        for k, v in attributes.items():
            setattr(self, k, v)
        
    def join(self, channel_id):
        pass

    def leave(self, channel_id):
        pass

    def update_roles(self, xpto):
        pass

    def update_last_viewed_at(self, channel_id):
        pass

class Mattermost:
    def __init__(self, url, team, email, password):
        self.users = {}
        self.channels = {}
        self.api = MattermostAPI(url, team, email, password)
        self.user = None

    def login(self, team, email, password):
        self.user = User(self.api, team, email, password)

    def update(self):
        r = self.api.get_channels()
        for channel in r["channels"]:
            channel["members"] = r["members"][channel["id"]]
            self.channels[channel["id"]] = channel
            self.channels[channel["name"]] = channel
            self.channels[channel["display_name"]] = channel

    def msg_private(self, user_id):
        pass

def pretty(j):
    print(json.dumps(j, indent=4))

m = Mattermost("http://localhost:8065/api/v1")
m.login("helloteam", "joao.grilo@gmail.com", "grilo")
m.update()
pretty(m.api.channel("r1eft3caytbp5x1345e1aoswxo"))
