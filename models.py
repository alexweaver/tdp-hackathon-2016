
from google.appengine.ext import ndb


class AppUser(ndb.Model):

	username = ndb.StringProperty()

class Bag(ndb.Model):

    userid = ndb.StringProperty()

    @staticmethod
    def get_user_bag_key(username):

    	bag = Bag.query(Bag.userid == username).get()

    	if bag is not None:
    		return bag.key

    	else:
    		bag = Bag(userid = username)
    		return bag.put()


class Item(ndb.Model):

	name = ndb.StringProperty()
	category = ndb.StringProperty()
	price = ndb.FloatProperty()
	# img = ndb.BlobProperty()

class Room(ndb.Model):

	name = ndb.StringProperty()
	item_categories = ndb.StringProperty(repeated=True)
	own = ndb.BooleanProperty()
	rent = ndb.BooleanProperty()
	popularity = ndb.IntegerProperty()

	def get_item(self):

		item_categories = []

		for category in self.item_catgories:
			item_categories = item_categories + Item.query(Item.category==category).fetch()

		return item_categories

