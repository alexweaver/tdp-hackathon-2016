#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging

import urllib
import json
import webapp2
from models import Item
from models import Room
from models import Residence
from models import Inventory
from models import ItemRoomRelation
from google.appengine.api import users

from google.appengine.ext import ndb
import jinja2
import os

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

from google.appengine.ext.webapp import template

class MainHandler(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()
		if user:
		
			self.redirect("welcome")

		else:
			template_data = {}
			template_data['login_url'] = users.create_login_url("welcome")

			template = JINJA_ENVIRONMENT.get_template('login.html')
			self.response.write(template.render(template_data))


class AdminHandler(webapp2.RequestHandler):

	def get(self):

		items = Item.query().fetch()
		rooms = Room.query().fetch()
		relations = ItemRoomRelation.query().fetch()

		item_dicts = []
		for item in items:
			item_data = {}
			item_data["name"] = item.name
			item_data["category"] = item.category
			item_data["price"] = item.price
			item_data["encoded"] = urllib.quote(item.name)
			item_dicts.append(item_data)

		room_dicts = []
		for room in rooms:
			room_data = {}
			room_data["name"] = room.name
			room_dicts.append(room_data)

		template_data = {}
		template_data['items'] = item_dicts
		template_data['rooms'] = room_dicts
		template_data['relations'] = relations


		template = JINJA_ENVIRONMENT.get_template('admin.html')
		self.response.write(template.render(template_data))


	# def post(self):

	# 	self.get

# Rooms handler

class RoomHandler(webapp2.RequestHandler):
	
	def get(self):
		
		rooms = Room.query()

		names = []
		for room in rooms.fetch():
			names.append(str(room.name))

		logging.debug(names)

		self.response.write(json.dumps(names))

	def post(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/welcome')
			self.response.write('<html><body>{}</body></html>'.format('<a href="' + login_url + '">Sign in</a>'))
			return

		residence = Residence.get_residence_by_user(user)

		name = self.request.get("name").strip()
		if name == '':	
			self.response.write('no room name')
			return

		room = Room(name=name, parent=residence.key)
		room.put()

		self.redirect("/room-tour?room=" + name)

	# def put(self):

	# 	name = self.request.get("name")

# Create item

# Get user inventory

# class BagHandler(webapp2.RequestHandler):

# 	def get(self):

# 		username = self.request.get("user")
# 		app_user = AppUser.query(AppUser.username==username).get()

# 		if app_user is None:
# 			app_user = AppUser(username=username)
# 			app_user.put()

# 		bag_key = Bag.get_user_bag_key(username)

# 		items = Item.query(ancestor=bag_key).fetch()

# 		items_serialized = []
# 		for item in items:
# 			items_serialized.append(json.dumps(item.to_dict()))

# 		self.response.write(items_serialized)

# Get average price of a category

class PriceHandler(webapp2.RequestHandler):

	def get(self):

		category = self.request.get("category")

		if category is '':
			self.response.write("no item type provided")
			return

		items = Item.query(Item.category==category).fetch()

		prices = []
		for item in items:
			prices.append(item.price)
		
		if len(prices) > 0:
			self.response.write(sum(prices)/len(prices))
			return

		self.response.write(json.dumps(0))

# Get user total value

class ValueHandler(webapp2.RequestHandler):

	def get(self):

		username = self.request.get("user")
		user = AppUser.query(AppUser.username==username).get()

		if user is None:
			user = AppUser(username=username)
			user.put()

		bag_key = Bag.get_user_bag_key(username)

		items = Item.query(ancestor=bag_key).fetch()

		value = 0
		for item in items:
			value += item.price

		self.response.write(json.dumps(value))


class RoomItemHandler(webapp2.RequestHandler):

	def get(self):

		name = self.request.get("name")

		if name is '':
			self.response.write("no room name given")
			return

		room = Room.query(Room.name==name).get()
		room.popularity += 1
		room.put()

		self.response.write(json.dumps(room.item_categories))
		return



class ResidenceTourHandler(webapp2.RequestHandler):

	def get(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/welcome')
			self.response.write('<html><body>{}</body></html>'.format('<a href="' + login_url + '">Sign in</a>'))
			return

		residence = Residence.get_residence_by_user(user)
		inventory = Inventory.get_inventory_by_user(user)

		other_homes = Residence.query(Residence.own==residence.own).fetch()

		logging.error(other_homes)

		rooms = []
		for home in other_homes:
			rooms += Room.query(ancestor=home.key).filter(Room.name!="miscellaneous").fetch()

		room_count = {}
		for room in rooms:
			name = room.name
			if name in room_count:
				room_count[name] += 1
				continue
			room_count[name] = 1

		room_count_final = {}
		for room in room_count:
			my_count = Room.query(ancestor=residence.key).filter(Room.name==room).count()

			if my_count == 0:
				room_count_final[str(room)] = ("", room_count[room] / max(len(other_homes), 1))
			else:
				up_count = str(my_count + 1)
				my_tail = ""
				if up_count[-1:] in ["0", "4", "5", "6", "7", "8", "9"]:
					my_tail = "th"
				elif up_count[-1:] in ["2"]:
					my_tail = "nd"
				elif up_count[-1:] in ["1"]:
					my_tail = "st"
				elif up_count[-1:] in ["3"]:
					my_tail = "rd"
				room_count_final[str(room)] = (" (" + up_count + my_tail + ")", room_count[room] / max(len(other_homes), 1) - 2 * my_count)
		
		room_count_final = sorted(room_count_final.items(), key=lambda x: x[1], reverse=True)

		template = JINJA_ENVIRONMENT.get_template('tourRoomPage.html')
		template_data = {'rooms': room_count_final}

		self.response.write(template.render(template_data))


class RoomTourHandler(webapp2.RequestHandler):

	def get(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/welcome')
			self.response.write('<html><body>{}</body></html>'.format('<a href="' + login_url + '">Sign in</a>'))
			return

		name = self.request.get("room")

		if name is '':
			self.response.write("no room specified")
			ResidenceTourHandler

		residence = Residence.get_residence_by_user(user)
		room = Room.query(ancestor=residence.key).filter(Room.name==name).get()

		if room is None:
			room = Room(name=name, parent=residence.key)
			room.put()

		other_rooms = Room.query(Room.name==name).fetch()

		relations = []
		for other_room in other_rooms:
			relations += ItemRoomRelation.query(ItemRoomRelation.room==other_room.key).fetch()

		item_count = {}
		for relation in relations:
			category = relation.item.get().category
			if category in item_count:
				item_count[category] += 1
				continue
			item_count[category] = 1

		logging.error(item_count)

		inventory = Inventory.get_inventory_by_user(user)

		item_count_final = {}
		for item in item_count:
			my_count = Item.query(ancestor=inventory.key).filter(Item.category==item).count()

			if my_count == 0:
				item_count_final[str(item)] = ("", item_count[item] / max(len(other_rooms), 1))
			else:
				up_count = str(my_count + 1)
				my_tail = ""
				if up_count[-1:] in ["0", "4", "5", "6", "7", "8", "9"]:
					my_tail = "th"
				elif up_count[-1:] in ["2"]:
					my_tail = "nd"
				elif up_count[-1:] in ["1"]:
					my_tail = "st"
				elif up_count[-1:] in ["3"]:
					my_tail = "rd"
				logging.error( "(" + up_count + my_tail + ")")
				item_count_final[str(item)] = ("(" + up_count + my_tail + ")", item_count[item] / max(len(other_rooms), 1) - 2 * my_count)
				

		item_count_final = sorted(item_count_final.items(), key=lambda x: x[1], reverse=True)

		logging.error(item_count_final)

		template = JINJA_ENVIRONMENT.get_template('tourItemPage.html')
		template_data = {}
		template_data['items'] = item_count_final
		template_data['room'] = room.name



		self.response.write(template.render(template_data))

class HomeHandler(webapp2.RequestHandler):

	def get(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/home')

			template_data = {}
			template_data['login_url'] = login_url

			template = JINJA_ENVIRONMENT.get_template('login.html')
			self.response.write(template.render(template_data))
			return

		inventory = Inventory.get_inventory_by_user(user)
		items = inventory.get_items().fetch()

		total_price = 0

		logout_url = users.create_logout_url("/")

		relations = []
		for item in items:
			relations += ItemRoomRelation.query(ancestor=inventory.key).filter(ItemRoomRelation.item==item.key).fetch()
			total_price += item.price

		relation_data = {}
		for relation in relations:
			item = relation.item.get()
			item_data = {'category': item.category, 'name': item.name, 'price': "${0:.2f}".format(item.price), 'encoded': urllib.quote(item.name)}

			if relation.room.get().name in relation_data:
				relation_data[relation.room.get().name].append(item_data)
				continue
			relation_data[str(relation.room.get().name)] = [item_data]
			logging.error(relation)

		logging.error(relation_data)

		template_data = {}
		template_data['relations'] = relation_data
		template_data['total_price'] = "${0:.2f}".format(total_price)
		template_data['logout_url'] = logout_url

		template = JINJA_ENVIRONMENT.get_template('userHomePage.html')
		self.response.write(template.render(template_data))


class AddItemHandler(webapp2.RequestHandler):

	def get(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/home')

			template_data = {}
			template_data['login_url'] = login_url

			template = JINJA_ENVIRONMENT.get_template('login.html')
			self.response.write(template.render(template_data))
			return

		category = self.request.get("category")
		room = self.request.get("room")

		items = Item.query(Item.category==category).fetch()

		if category != '':
			prices = []
			for item in items:
				prices.append(item.price)
				logging.error(item.price)
			price = sum(prices) / len(prices) if len(prices) > 0 else 0
		else:
			price = 0
		template_data = {}
		template_data["category"] = category
		template_data["price"] = "{0:.2f}".format(price)
		template_data["room"] = room
		template_data['back_url'] = "/home" if room == "miscellaneous" else "/room-tour?room=" + room
		
		template = JINJA_ENVIRONMENT.get_template('addItemTour.html')
		self.response.write(template.render(template_data))

	def post(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/home')

			template_data = {}
			template_data['login_url'] = login_url

			template = JINJA_ENVIRONMENT.get_template('login.html')
			self.response.write(template.render(template_data))
			return

		residence = Residence.get_residence_by_user(user)

		category = self.request.get('category')
		name = self.request.get('name')
		price = self.request.get('price')

		price = float(price)

		inventory = Inventory.get_inventory_by_user(user)
		item = Item(category=category, name=name, price=price, parent=inventory.key)
		item.put()

		room_name = self.request.get("room")

		residence = Residence.get_residence_by_user(user)
		room = Room.query(ancestor=residence.key).filter(Room.name==room_name).get()
		if room is None:
			room = Room(name=room_name, parent=residence.key)
			room.put()
		
		relation = ItemRoomRelation(item=item.key, room=room.key, parent=inventory.key)
		relation.put()

		if room_name == "miscellaneous":
			self.redirect("/home")
			return



		self.redirect("/room-tour?room=" + urllib.quote(room_name))

class WelcomeHandler(webapp2.RequestHandler):

	def get(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/home')

			template_data = {}
			template_data['login_url'] = login_url

			template = JINJA_ENVIRONMENT.get_template('login.html')
			self.response.write(template.render(template_data))
			return

		template_data = {}

		template = JINJA_ENVIRONMENT.get_template('landingPage.html')
		self.response.write(template.render(template_data))


class DeleteItemHandler(webapp2.RequestHandler):

	def get(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/welcome')
			self.response.write('<html><body>{}</body></html>'.format('<a href="' + login_url + '">Sign in</a>'))
			return

		name = self.request.get("name")

		inventory = Inventory.get_inventory_by_user(user)
		item = Item.query(ancestor=inventory.key).filter(Item.name==name).get()


		if item is not None:
			for relation in ItemRoomRelation.query(ancestor=inventory.key).filter(ItemRoomRelation.item==item.key).fetch():
				relation.key.delete()
			item.key.delete()

		self.redirect("home")

class StatusHandler(webapp2.RequestHandler):

	def get(self):
		
		user = users.get_current_user()

		if user is None:
			self.redirect("/")
			return

		residence = Residence.get_residence_by_user(user)

		status = self.request.get("status")

		residence.own = True if status == "owner" else False
		logging.error(residence.own)
		residence.put()

		self.redirect("home-tour")

class PieHandler(webapp2.RequestHandler):

	def get(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/home')

			template_data = {}
			template_data['login_url'] = login_url

			template = JINJA_ENVIRONMENT.get_template('login.html')
			self.response.write(template.render(template_data))
			return

		inventory = Inventory.get_inventory_by_user(user)
		items = inventory.get_items().fetch()

		logout_url = users.create_logout_url("/")

		relations = []
		for item in items:
			relations += ItemRoomRelation.query(ancestor=inventory.key).filter(ItemRoomRelation.item==item.key).fetch()

		i = 0
		relation_data = {}
		for relation in relations:
			i += 1
			if i > 5:
				break
			room_name = relation.room.get().name
			if room_name in relation_data:
				relation_data[room_name] += relation.item.get().price
			else:
				relation_data[room_name] = relation.item.get().price


		i = 0
		cols = ["#4789b", "#EF7014", "#4BA449", "#154995", "#757374"]

		relation_data_final = []
		for k in relation_data:
			i += 1
			relation_data_final.append({"title": str(k), "value": relation_data[k], "color": cols[i]})

		relation_data_final = sorted(relation_data_final, key=lambda x: x["value"], reverse=True)

		template_data = {}
		template_data['relations'] = relation_data_final

		self.response.write(template_data)

app = webapp2.WSGIApplication([
	('/', MainHandler)
	, ('/room', RoomHandler)
	, ('/admin', AdminHandler)
	, ('/home-tour', ResidenceTourHandler)
	, ('/room-tour', RoomTourHandler)
	, ('/add', AddItemHandler)
	, ('/home', HomeHandler)
	, ('/welcome', WelcomeHandler)
	, ('/delete', DeleteItemHandler)
	, ('/status', StatusHandler)
	, ('/pie', PieHandler)
], debug=True)



