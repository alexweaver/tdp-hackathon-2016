
from google.appengine.ext import ndb


class AppUser(ndb.Model):

	username = ndb.StringProperty()

class Inventory(ndb.Model):

    user_id = ndb.StringProperty()

    @staticmethod
    def get_inventory_by_user(user):
    	inventory = Inventory.query(Inventory.user_id==user.user_id()).get()

    	if inventory is None:
    		inventory = Inventory(user_id=user.user_id())
    		inventory.put()

    	return inventory

class Residence(ndb.Model):

	user_id = ndb.StringProperty()

	@staticmethod
	def get_residence_by_user(user):
    	residence = Residence.query(Residence.user_id==username).get()

    	if residence is None:
    		residence = Residence(user_id=user.user_id())
    		residence.put()

    	return residence

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

	

