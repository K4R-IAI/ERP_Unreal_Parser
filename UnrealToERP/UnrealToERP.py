#!/usr/bin/env python

import csv
import json
from geometry_msgs.msg import Pose

class Product:
  def __init__(self, data):
    self.items = []
    self.items_front = []
    self.shelves = []
    self.layers = []
    self.facing = 0

  def calc_items_front(self):
    for item in self.items:
      if self.items_front:
        if item.pose.position.x > self.items_front[-1].pose.position.x:
          self.items_front[-1] = item
        elif item.pose.position.x == self.items_front[-1].pose.position.x:
          self.items_front.append(item)
      else:
        self.items_front.append(item)

  def calc_facing(self):
    items_front_line = []
    max_facing = 0
    for i, item in enumerate(self.items):
      if items_front_line:
        if item.pose.position.z == items_front_line[-1].pose.position.z:
          items_front_line.append(item)
          if i == len(items_front_line) - 1:
            max_facing = len(items_front_line)
        else:
          if len(items_front_line) > max_facing:
            max_facing = len(items_front_line)
          items_front_line = [item]
      else:
        items_front_line.append(item)
    self.facing = max_facing

  def calc_layer(self, shelf):
    for item in self.items:
      for i, layer in enumerate(shelf.layers):
        if layer.z_min <= item.pose.position.z and item.pose.position.z <= layer.z_max:
          if not i in self.layers:
            self.layers.append(i)

  def __repr__(self):
    return str(self.items[0]) + ' - ' + str(len(self.items)) + ' items - ' + str(len(self.layers))  + ' layers (' + str(self.layers) + ')'

class Item:
  def __init__(self, data):
    self.name = str(data[0])
    self.pose = Pose()
    self.pose.position.x = float(data[1])
    self.pose.position.y = float(data[2])
    self.pose.position.z = float(data[3])
    self.pose.orientation.x = float(data[4])
    self.pose.orientation.y = float(data[5])
    self.pose.orientation.z = float(data[6])
    self.pose.orientation.w = float(data[7])
  def __repr__(self):
    return self.name

class Shelf:
  def __init__(self, data, shelf_id):
    self.id = shelf_id
    self.type = str(data[0])
    self.pose = Pose()
    self.pose.position.x = float(data[1])
    self.pose.position.y = float(data[2])
    self.pose.position.z = float(data[3])
    self.pose.orientation.x = float(data[4])
    self.pose.orientation.y = float(data[5])
    self.pose.orientation.z = float(data[6])
    self.pose.orientation.w = float(data[7])
    self.depth = 0.8
    self.width = 1.0
    self.layers = []
    self.products = []
  def __repr__(self):
    return str(self.id) + ' - ' + self.type + ': ' + str(self.layers)

class Layer:
  def __init__(self, z_min, z_max):
    self.z_min = z_min
    self.z_max = z_max
  def __repr__(self):
    return str(self.z_min) + ' - ' + str(self.z_max)

def fill(products, shelves):
  for product in products:
    for shelf in shelves:
      for item in product.items:
        if not shelf in product.shelves:
          if shelf.pose.position.x - shelf.depth/2 < item.pose.position.x and item.pose.position.x < shelf.pose.position.x + shelf.depth/2 and shelf.pose.position.y - shelf.width/2 < item.pose.position.y and item.pose.position.y < shelf.pose.position.y + shelf.width/2:
            product.shelves.append(shelf)
            shelf.products.append(product)

def csv_to_products(csv_items):
  with open(csv_items, mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='|')
    first_row = next(csv_reader)
    products = []
    products.append(Product(first_row))
    products[0].items.append(Item(first_row))
    for data in csv_reader:
      item = Item(data)
      if products[-1].items[-1].name != item.name:
        products.append(Product(data))
      products[-1].items.append(item)
  return products

def csv_to_shelves(csv_shelves):
  with open(csv_shelves, mode='r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter='|')
    shelves = []
    shelf_id = 0
    shelf_bottoms = []
    shelf_layers = []
    layer_heights = {}
    for data in csv_reader:
      if 'ShelfSystemH200T7L10W' in str(data[0]):
        shelves.append(Shelf(data, str(shelf_id)))
        layer_heights[shelves[-1]] = []
        shelf_id += 1
      elif 'Bottom' in str(data[0]):
        shelf_bottoms.append(data)
      elif 'ShelfLayer' in str(data[0]):
        shelf_layers.append(data)
    for data in shelf_bottoms:
      for shelf in shelves:
        if shelf.pose.position.x - shelf.depth/2 < float(data[1]) and float(data[1]) < shelf.pose.position.x + shelf.depth/2 and shelf.pose.position.y - shelf.width/2 < float(data[2]) and float(data[2]) < shelf.pose.position.y + shelf.width/2:
          layer_heights[shelf].append(float(data[3]))
    for data in shelf_layers:
      for shelf in shelves:
        if shelf.pose.position.x - shelf.depth/2 < float(data[1]) and float(data[1]) < shelf.pose.position.x + shelf.depth/2 and shelf.pose.position.y - shelf.width/2 < float(data[2]) and float(data[2]) < shelf.pose.position.y + shelf.width/2:
          layer_heights[shelf].append(float(data[3]))
    for shelf in layer_heights:
      layer_heights[shelf].sort()
      for i in range(len(layer_heights[shelf])-1):
        shelf.layers.append(Layer(layer_heights[shelf][i], layer_heights[shelf][i+1]))
      shelf.layers.append(Layer(layer_heights[shelf][i+1], float('inf')))
  return shelves

def write_output(products):
  data = {}
  for product in products:
    for item in product.items:
      if not item.name in data:
        data[item.name] = {}
        data[item.name]['layers'] = product.layers
        data[item.name]['facing'] = product.facing
  with open('output/ERP.json', 'w') as outfile:
    json.dump(data, outfile)

if __name__ == "__main__":
  products = csv_to_products('data/allitems.csv')
  #print(products)
  shelves = csv_to_shelves('data/allshelves.csv')
  #print(shelves)
  fill(products, shelves)

  products_valid = []
  for product in products:
    if product.shelves:
      products_valid.append(product)
  products = products_valid
  #print(products)
  #for product in products:
    #product.calc_facing()
    #product.calc_layer(shelves[0])
  #print(products)
  #write_output(products)