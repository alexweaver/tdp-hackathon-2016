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
from google.appengine.api import users

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
			nickname = user.nickname()
			logout_url = users.create_logout_url('/')
			greeting = 'Welcome, {}! (<a href="{}">sign out</a>)'.format(
				nickname, logout_url)

			self.response.write(Bag.get_user_bag_key(user))


		else:
			login_url = users.create_login_url('/')
			greeting = '<a href="{}">Sign in</a>'.format(login_url)

		self.response.write(
			'<html><body>{}</body></html>'.format(greeting))


class AdminHandler(webapp2.RequestHandler):

	def get(self):

		self.response.write('add room')
		self.response.write('<form method="post" action="/rooms">')
		self.response.write('Name<input type=text name="name"></input>')
		self.response.write('Items<input type=text name="items"></input>')
		self.response.write('Own<input type=checkbox name="own"></input>')
		self.response.write('Rent<input type=checkbox name="rent"></input>')
		self.response.write('<input type=submit></input>')
		self.response.write('</form>')

		self.response.write('<table>')
		self.response.write('<tr><th>Name</th><th>Items</th><th>Own</th><th>Rent</th><th>Popularity</th></tr>')

		for room in Room.query().fetch():
			self.response.write('<tr>')
			self.response.write('<td>' + str(room.name) + '</td>')
			self.response.write('<td>' + str(json.dumps(room.item_categories)) + '</td>')
			self.response.write('<td>' + str(room.own) + '</td>')
			self.response.write('<td>' + str(room.rent) + '</td>')
			self.response.write('<td>' + str(room.popularity) + '</td>')
			self.response.write('</tr>')
		self.response.write('</table>')

		self.response.write('add item')
		self.response.write('<form method="post" action="/items">')
		self.response.write('Name <input type=text name="name"></input>')
		self.response.write('Category <input type=text name="category"></input>')
		self.response.write('Price <input type=text name="price"></input>')
		self.response.write('User <input type=text name="user"></input>')
		self.response.write('<input type=submit></input>')
		self.response.write('</form>')

		self.response.write('<table>')
		self.response.write('<tr><th>Name</th><th>Category</th><th>Price</th></tr>')

		for item in Item.query().fetch():
			self.response.write('<tr>')
			self.response.write('<td>' + str(item.name) + '</td>')
			self.response.write('<td>' + str(item.category) + '</td>')
			self.response.write('<td>' + str(item.price) + '</td>')
			self.response.write('</tr>')
		self.response.write('</table>')


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

		name = self.request.get("name")
		items = self.request.get("items")
		own = self.request.get("own")
		rent = self.request.get("rent")

		items = items.split(",")
		own = own == 'on'
		rent = rent == 'on'

		room = Room(name=name, item_categories=items, own=own, rent=rent, popularity=0)
		room.put()

	# def put(self):

	# 	name = self.request.get("name")

# Create item

class ItemHandler(webapp2.RequestHandler):

	def post(self):

		username = self.request.get("user")
		app_user = AppUser.query(AppUser.username==username).get()

		if app_user is None:
			app_user = AppUser(username=username)
			app_user.put()

		bag_key = Bag.get_user_bag_key(username)

		name = self.request.get("name")
		category = self.request.get("category")
		price = float(self.request.get("price"))

		item = Item(name=name, category=category, price=price, parent=bag_key)
		item.put()


	def put(self):

		username = self.request.get("user")
		app_user = AppUser.query(AppUser.username==username).get()

		if app_user is None:
			app_user = AppUser(username=username)
			app_user.put()

	def delete(self):
		pass

# Get user inventory

class BagHandler(webapp2.RequestHandler):

	def get(self):

		username = self.request.get("user")
		app_user = AppUser.query(AppUser.username==username).get()

		if app_user is None:
			app_user = AppUser(username=username)
			app_user.put()

		bag_key = Bag.get_user_bag_key(username)

		items = Item.query(ancestor=bag_key).fetch()

		items_serialized = []
		for item in items:
			items_serialized.append(json.dumps(item.to_dict()))

		self.response.write(items_serialized)

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

		rooms = Room.query().fetch()
		discovered = Room.query(ancestor=residence.key).fetch()
		undiscovered = []

		for room in rooms:
			if room not in discovered:
				data = {"name": room.name, "encoded": urllib.quote(room.name)}
				undiscovered.append(data)

		template = JINJA_ENVIRONMENT.get_template('tourRoomPage.html')
		template_data = {'rooms': undiscovered}

		self.response.write(template.render(template_data))


class RoomTourHandler(webapp2.RequestHandler):

	def get(self):

		user = users.get_current_user()

		if user is None:
			login_url = users.create_login_url('/welcome')
			self.response.write('<html><body>{}</body></html>'.format('<a href="' + login_url + '">Sign in</a>'))
			return

		room = self.request.get("room")

		if room is '':
			self.response.write("no room specified")
			return

		residence = Residence.get_residence_by_user(user)
		
		

		rooms = Room.query(Room.name==room).get()



		rooms = Room.query().fetch()
		discovered = Room.query(ancestor=residence.key).fetch()
		undiscovered = []

		for room in rooms:
			if room not in discovered:
				data = {"name": room.name, "encoded": urllib.quote(room.name)}
				undiscovered.append(data)

		template = JINJA_ENVIRONMENT.get_template('tourRoomPage.html')
		template_data = {'rooms': undiscovered}

		self.response.write(template.render(template_data))


class TestHandler(webapp2.RequestHandler):

	def get(self):
		self.response.write("bob")

app = webapp2.WSGIApplication([
	('/', MainHandler)
	, ('/items', ItemHandler)
	, ('/rooms', RoomHandler)
	, ('/admin', AdminHandler)
	, ('/price', PriceHandler)
	, ('/value', ValueHandler)
	, ('/bag', BagHandler)
	, ('/residence-tour', ResidenceTourHandler)
	, ('/room-tour', RoomTourHandler)
	, ('/room-items', RoomItemHandler)
	, ('/test', TestHandler)
], debug=True)



